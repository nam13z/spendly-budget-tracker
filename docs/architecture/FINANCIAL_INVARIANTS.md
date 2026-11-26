# Spendly Financial Invariants and Validation Plan

These invariants must be implemented in backend domain services and verified by automated tests before the UI relies on them. Frontend validation is for usability only; it is not an authority.

## 1. Ledger invariants

1. Transaction header `amount` is positive and stored as MySQL `DECIMAL(19,4)`; map it as SQLAlchemy `Numeric(19, 4, asdecimal=True)` and use Python `Decimal`.
2. Posted income/expense/refund/opening-balance/adjustment transactions have the required account entry or entries.
3. Ordinary income has positive account effect; ordinary expense has negative account effect; refund has positive account effect; opening balance/adjustment sign depends on the correction.
4. Same-currency transfer has exactly two entries: source negative X and destination positive X. Their sum is zero.
5. Every account entry currency equals its account currency.
6. Voided transactions contribute no balance. Draft transactions contribute no balance.
7. Balance is derived from posted account entries. Cached balances must be rebuildable.
8. Posted records cannot be silently mutated. Correction acts on a posted transaction and atomically marks it `VOIDED` and creates a new posted replacement whose `replaces_transaction_id` points to the original. The field is unique, so each transaction has at most one direct replacement and the correction chain is unambiguous. Original entries and allocations remain unchanged for audit and are excluded from balances and current reporting. A voided transaction cannot be edited or reposted; another correction creates a replacement of the currently posted replacement. No separate reversing transaction or entries are created by correction. A real refund/chargeback is a separate posted `REFUND` transaction linked to the original expense with `original_transaction_id`, and is not a correction.

## 2. Allocation invariants

For a transaction amount `T`:

- Each allocation amount is positive.
- Monetary amounts use `DECIMAL(19,4)` in MySQL, `Numeric(19, 4, asdecimal=True)` in SQLAlchemy, Python `Decimal` for calculations, and decimal strings in API payloads. Never use binary floating-point arithmetic authoritatively.
- Validate entered and posted amounts against the currency's `minor_unit_digits`. LKR and USD use two digits; reject excess fractional digits and do not silently round. Storage precision is four fractional digits; display formatting follows currency metadata. Currencies needing more than four digits require a reviewed storage change.
- Allocation currency is inherited from the transaction and therefore cannot differ in MVP.
- Sum of allocations must be less than or equal to `T`.
- Unallocated remainder is `T - SUM(allocations)` and is visible.
- Transfers have no normal income/expense allocations.
- MVP refund allocations must explicitly link through `reverses_allocation_id` to the original allocation and preserve its space/category context. Do not calculate proportional allocation silently. Each refund allocation cannot exceed the original allocation's remaining refundable amount.

A cross-row sum cannot be protected by a simple MySQL CHECK. Validate in a transaction with appropriate row locking so two concurrent requests cannot both exceed the original amount.

## 3. Budget invariants

- Budget plans and allocations are plans, not cash balances.
- Calculate periods in the relevant personal or household space timezone using local calendar boundaries; start is inclusive and end is exclusive. Store event timestamps in UTC.
- Set a space's IANA timezone at creation from the owner's or household's choice. Snapshot the timezone on each budget period; later space timezone changes do not alter existing period dates or snapshots.
- Reusable records use `ACTIVE`/`ARCHIVED`; budget periods use `OPEN`/`CLOSED`. Define exact transitions before API implementation.
- Actual spend comes from eligible posted expense allocations minus linked refund allocations.
- Transfers are excluded.
- A bill payment is counted through its posted expense allocation once; the commitment payment link only reconciles the bill status.
- Budget changes never rewrite actual transaction history.
- Rollover is deferred until its effect on period balances and Safe-to-Spend is explicitly specified.

## 4. Commitment/payment invariants

- A commitment occurrence is a forecast obligation, not an account entry.
- A payment must link to a posted expense transaction, or an explicit action creates that transaction.
- Partial payments are allowed.
- Sum of applied payments cannot exceed the occurrence's expected amount. Waiver/adjustment workflows are deferred unless required by initial bill-payment implementation; do not imply such a workflow without an approved schema.
- Sum applied from a transaction cannot exceed the eligible expense amount.
- Outstanding amount = expected amount - applied payments.
- Paid status is derived when outstanding amount reaches zero; cancellation is represented by its documented occurrence status. Waivers/adjustments are deferred.

## 5. Income invariants

- Expected income occurrences never affect account balances.
- Actual receipts must link to posted income transactions in the same currency.
- Partial receipts are supported.
- Each receipt links to exactly one posted income transaction; each transaction links to at most one occurrence; an occurrence may have multiple partial receipts.
- Reject cumulative receipts above an occurrence's expected amount until an adjustment policy is approved.
- Received amount is derived from linked receipts; account balance is derived from the actual transaction's account entry.
- A receipt reconciliation link must not create a second account entry.
- Overpayment beyond expected amount requires an explicit policy, not silent truncation.

## 6. Goal and reserve invariants

- Goal contributions are not expenses.
- An earmark creates/links to a reservation but no account entry.
- Actual movement between accounts is represented by a transfer. Transfer-linked goal progress is deferred.
- A fund reservation is not a ledger entry.
- Active reservations cannot exceed eligible funds in the relevant account/scope.
- The same money cannot be reserved twice. Manual reserve and complex release semantics are deferred; MVP goal contributions are earmarks.
- If money is moved to a dedicated savings account excluded from Safe-to-Spend, do not also subtract the same amount as a source-account reserve.

## 7. Safe-to-Spend baseline

Calculate separately for each selected currency and scope:

`Safe-to-Spend = eligible posted account balances - unpaid commitments due within horizon - active fund reservations - safety buffer`

Rules:
- New accounts default to `include_in_safe_to_spend = false`; only include accounts selected as eligible (`true`).
- Exclude voided/draft entries.
- Subtract only the outstanding portion of commitments due within the selected horizon.
- Do not subtract paid bills again.
- Do not subtract transfers as spending.
- Do not add expected income to confirmed Safe-to-Spend. An optional forecast scenario may display expected income separately.
- Do not subtract a reservation if the reserved money is already excluded by account eligibility or another reserve record.
- Never aggregate LKR and USD directly.
- Show the calculation timestamp, horizon, included accounts, commitments, reserves, buffer, data gaps and assumptions.
- If account coverage or required data is insufficient/stale, show an insufficient-data state rather than false precision.

This is a planning estimate, not a guarantee or financial advice.

## 8. Multi-currency invariants

- Each account has one currency.
- Each transaction and its account entries use the same currency in MVP.
- LKR and USD each have `minor_unit_digits = 2`; totals remain separate. Conversion reporting and cross-currency transfers are deferred.
- Cross-currency transfers are deferred until source/destination amounts, rate direction, rate source/time, fees, rounding and historical reporting rules are specified.
- Original transaction values are never overwritten by converted display values.

## 9. Required acceptance tests

| # | Setup / action | Expected result |
|---|---|---|
| 1 | Opening balance LKR 10,000; expense LKR 2,000 | Balance LKR 8,000 |
| 2 | LKR 10,000 transferred between two LKR accounts | Source -10,000; destination +10,000; combined total unchanged |
| 3 | LKR 5,000 expense allocated Home 2,500 + Personal 2,500 | One purchase, one -5,000 account effect, combined spend 5,000 |
| 4 | LKR 5,000 expense with only LKR 3,000 allocated | LKR 2,000 visibly unallocated; total spend remains 5,000 |
| 5 | LKR 4,000 expense receives LKR 1,000 partial refund | Net expense LKR 3,000; account gets +1,000 |
| 6 | Expected salary LKR 50,000 scheduled | Account balance unchanged until actual receipt is posted |
| 7 | Expected salary LKR 50,000 received in two receipts of 20,000 and 30,000 | Forecast occurrence becomes received; exactly two actual account effects total +50,000 |
| 8 | LKR 4,000 bill paid by linked LKR 4,000 expense | Bill outstanding zero; spending counted once |
| 9 | LKR 4,000 bill paid in two parts 1,500 and 2,500 | Outstanding 0; two payment links; two actual transactions/effects |
| 10 | LKR 20,000 budget, eligible net spend LKR 7,500 | Remaining LKR 12,500 |
| 11 | Goal earmark LKR 3,000 | Earmark/reservation changes; account balance does not |
| 12 | Same-currency transfer LKR 3,000 to savings account | Source/destination balances change equally/oppositely; no expense is created |
| 13 | LKR 1,000 and USD 1,000 balances | Display separately; never show combined 2,000 |
| 14 | Atomically correct a posted expense | Original is voided; entries/allocations remain for audit but are excluded from balance/reporting; one replacement effect counts; no reversing entry exists |
| 15 | Retry create request with same idempotency key and same payload | No duplicate transaction |
| 16 | Reuse idempotency key with a different payload | Conflict response; no mutation |
| 17 | Household member guesses another member's personal account/transaction ID | Authorization denial; no private data leaked |
| 18 | Two concurrent partial refunds attempt to exceed original refundable amount | Only valid amount succeeds; no over-refund |
| 19 | Two concurrent allocations attempt to exceed transaction amount | At most valid total commits |
| 20 | Personal account pays a mixed Home/Personal purchase | Household view appears only after explicit creator consent and shows only approved Home projection fields |
| 21 | Two sequential corrections | Each replacement points to its predecessor; unique link prevents multiple direct replacements; voided records cannot be reposted |
| 22 | Retry a correction request with same idempotency key/payload | No duplicate replacement or ledger effect |
| 23 | Enter LKR/USD with more than two fractional digits | Validation rejects; no rounding or write occurs |
| 24 | Exercise the DECIMAL(19,4) four-decimal storage boundary | Database-type round-trip is exact; application currency validation separately rejects more than two digits for LKR/USD |

## 10. Privacy and deletion invariants

- Personal spaces remain private; household spaces are visible to active members. Transactions are private until explicitly shared by their creator. Mixed Home/Personal allocations require explicit consent.
- Household projection allowlist: transaction ID, Home allocation amount and currency, transaction calendar date in the Home space timezone, description, and category display name. Omit transaction total, account identifiers/names/types/balances, personal allocations, beneficiary/private fields, notes, unrelated personal history, and the full transaction ORM object.
- Only the creator may change sharing status; status and consent changes are audited. A shared transaction requires a Home allocation. Mixed Home/Personal allocations require creator consent before sharing. Any allocation change clears consent and atomically returns sharing to `PRIVATE` until fresh creator consent.
- Household invitations grant `MEMBER` only; ownership transfer is a separate operation.
- Sound defaults off. Reduced-motion preference initializes from the platform setting and supports explicit user override.
- Ordinary application operations do not destructively delete financial history. Foreign keys restrict deletion; retention, erasure, backup, and legal policy remain deferred for separate approval.

## 11. Transactional write patterns

### Create an expense
1. Authenticate and authorize account and space/category.
2. Validate positive amount and matching currency.
3. Lock any rows needed for aggregate checks.
4. Insert transaction header.
5. Insert negative account entry.
6. Insert allocation rows.
7. Validate allocation total <= transaction amount.
8. Insert idempotency result and audit event.
9. Commit once; rollback all writes on failure.

### Create a same-currency transfer
1. Authorize both accounts; verify same currency and valid ownership scope.
2. Insert one transfer header.
3. Insert source negative and destination positive account entries for equal amounts.
4. Insert transfer details referencing both entries.
5. Validate sum of transfer entries = zero.
6. Commit atomically.

### Correct a posted transaction
1. Lock original transaction and entries.
2. Mark original `VOIDED`; retain its entries and allocations unchanged.
3. Create replacement as `POSTED`, set its unique `replaces_transaction_id` to the original, and insert new entries and allocations.
4. Preserve correction-chain links and audit history; do not create a separate reversing event or entries.
5. Commit all changes atomically. A later correction voids the current posted replacement and creates its next linked replacement.
