# Spendly Financial Invariants and Validation Plan

These invariants must be implemented in backend domain services and verified by automated tests before the UI relies on them. Frontend validation is for usability only; it is not an authority.

## 1. Ledger invariants

1. Transaction header `amount` is positive.
2. Posted income/expense/refund/opening-balance/adjustment transactions have the required account entry or entries.
3. Ordinary income has positive account effect; ordinary expense has negative account effect; refund has positive account effect; opening balance/adjustment sign depends on the correction.
4. Same-currency transfer has exactly two entries: source negative X and destination positive X. Their sum is zero.
5. Every account entry currency equals its account currency.
6. Voided transactions contribute no balance. Draft transactions contribute no balance.
7. Balance is derived from posted account entries. Cached balances must be rebuildable.
8. Posted records cannot be silently mutated. For MVP edit/correction, void the original transaction (retain its entries for audit but exclude them from balances) and create a replacement in one atomic operation. Do not also post a second reversing entry for the same correction. A real refund is a separate posted refund transaction.

## 2. Allocation invariants

For a transaction amount `T`:

- Each allocation amount is positive.
- Allocation currency is inherited from the transaction and therefore cannot differ in MVP.
- Sum of allocations must be less than or equal to `T`.
- Unallocated remainder is `T - SUM(allocations)` and is visible.
- Transfers have no normal income/expense allocations.
- Refund allocations should reverse the original allocation(s); each refund allocation cannot exceed the original allocation's remaining refundable amount.

A cross-row sum cannot be protected by a simple MySQL CHECK. Validate in a transaction with appropriate row locking so two concurrent requests cannot both exceed the original amount.

## 3. Budget invariants

- Budget plans and allocations are plans, not cash balances.
- A period has a defined timezone and inclusive/exclusive boundary policy.
- Actual spend comes from eligible posted expense allocations minus linked refund allocations.
- Transfers are excluded.
- A bill payment is counted through its posted expense allocation once; the commitment payment link only reconciles the bill status.
- Budget changes never rewrite actual transaction history.
- Rollover is deferred until its effect on period balances and Safe-to-Spend is explicitly specified.

## 4. Commitment/payment invariants

- A commitment occurrence is a forecast obligation, not an account entry.
- A payment must link to a posted expense transaction, or an explicit action creates that transaction.
- Partial payments are allowed.
- Sum of applied payments cannot exceed the occurrence's expected amount unless a documented adjustment/overpayment workflow exists.
- Sum applied from a transaction cannot exceed the eligible expense amount.
- Outstanding amount = expected amount - applied payments - approved waivers/adjustments.
- Paid status is derived when outstanding amount reaches zero, unless an explicit state records cancellation/waiver.

## 5. Income invariants

- Expected income occurrences never affect account balances.
- Actual receipts must link to posted income transactions in the same currency.
- Partial receipts are supported.
- Received amount is derived from linked receipts; account balance is derived from the actual transaction's account entry.
- A receipt reconciliation link must not create a second account entry.
- Overpayment beyond expected amount requires an explicit policy, not silent truncation.

## 6. Goal and reserve invariants

- Goal contributions are not expenses.
- An earmark creates/links to a reservation but no account entry.
- A transfer contribution links to an actual transfer; account entries already represent the movement.
- A fund reservation is not a ledger entry.
- Active reservations cannot exceed eligible funds in the relevant account/scope.
- The same money cannot be reserved twice (e.g. once as a goal earmark and again as a manual reserve).
- If money is moved to a dedicated savings account excluded from Safe-to-Spend, do not also subtract the same amount as a source-account reserve.

## 7. Safe-to-Spend baseline

Calculate separately for each selected currency and scope:

`Safe-to-Spend = eligible posted account balances - unpaid commitments due within horizon - active fund reservations - safety buffer`

Rules:
- Only include accounts selected as eligible (`include_in_safe_to_spend = true`).
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
- LKR and USD totals remain separate unless a reporting conversion is explicitly requested.
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
| 11 | Goal earmark LKR 3,000 | Goal/reserve progress changes; account balance does not |
| 12 | Transfer LKR 3,000 to excluded savings account and link to goal | Source/destination balances change; no duplicate expense or reserve deduction |
| 13 | LKR 1,000 and USD 1,000 balances | Display separately; never show combined 2,000 |
| 14 | Void a posted expense | Balance and budget exclude it; audit trail remains |
| 15 | Retry create request with same idempotency key and same payload | No duplicate transaction |
| 16 | Reuse idempotency key with a different payload | Conflict response; no mutation |
| 17 | Household member guesses another member's personal account/transaction ID | Authorization denial; no private data leaked |
| 18 | Two concurrent partial refunds attempt to exceed original refundable amount | Only valid amount succeeds; no over-refund |
| 19 | Two concurrent allocations attempt to exceed transaction amount | At most valid total commits |
| 20 | Personal account pays shared purchase; Home allocation exists | Household sees only allowed Home projection, not private account or Personal allocation |

## 10. Transactional write patterns

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
2. Mark original voided / create explicit reversal according to the chosen ledger policy.
3. Create replacement transaction and entries.
4. Preserve links and audit history.
5. Commit all changes atomically.

The exact choice between a `VOIDED` state and a separately posted reversing event must be finalized consistently. Do not mix both semantics in different endpoints.
