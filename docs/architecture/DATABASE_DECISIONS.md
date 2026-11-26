# Spendly Database Decisions and Open Questions

## Recommended decisions for MVP

The authoritative schema and ERD define 30 entities. This inventory is canonical; do not add entities to match any prior count of 33.

| Topic | Decision | Reason |
|---|---|---|
| Financial event | One `financial_transactions` header per real-world event | Prevent duplicate purchase records |
| Account balance | Derived from signed `account_entries` | One source of truth |
| Opening balance | Opening-balance transaction + entry | Avoid competing mutable balance fields |
| Transfer | One transaction + two equal/opposite entries + `transfer_details` | Transfer is neither income nor expense |
| Allocation | Separate positive attribution rows | Split reporting without duplicate cash movement |
| Partial allocation | Allowed; unallocated remainder visible | Real users may not know the split immediately |
| Refund | Link to original transaction and original allocation where possible | Correct net category/space reporting |
| Ownership | Account/space belongs to exactly one user OR one household | Clear authorization boundary |
| Household visibility | Purpose-built projection of shared allocations | Protect personal account and transaction details |
| Income forecast | Source + schedule + occurrence + receipt link | Separate expected money from received money |
| Budgets | Plan + period + category allocations | Keep plan distinct from actual spending |
| Bills | Template + occurrence + payment links | Support recurrence and partial payment without duplicate spending |
| Goals | Contributions are earmarks; actual account movement is a separate transfer | Saving is not an expense |
| Reserves | Separate reservation records | Explicitly model money unavailable for ordinary spending |
| Currency | LKR/USD from launch; no implicit conversion | Avoid invalid arithmetic |
| Cross-currency transfer | Defer | Rate, fees, rounding and historical reporting policy unresolved |
| Posted correction | Auditable atomic void + replacement (no duplicate reversal entry) | Preserve history |
| Budget rollover | Defer from first release | Avoid unclear carry-forward/Safe-to-Spend interactions |
| Monetary storage | MySQL `DECIMAL(19,4)`; Python `Decimal`; decimal strings in API | Exact storage with currency-specific validation |
| UUID storage | `BINARY(16)` for UUID keys; `UUID.bytes` conversion | Consistent compact key representation |
| Budget boundaries | Space-local calendar; start inclusive and end exclusive; events stored in UTC | Consistent period inclusion across personal and household spaces |
| Financial-history deletion | Restrict ordinary deletion; retain audit relationships | Prevent destructive loss of financial history |

## Policy details and remaining approval gates

### 1. Household-owned accounts — approved
**Approved:** support household-owned accounts in the schema. Membership grants no access to a member's personal accounts.

### 2. Household transaction projection — approved
**Approved:** personal spaces remain private; household spaces are visible to active members. Transactions are private until explicitly shared. Mixed Home/Personal transactions require creator-controlled explicit consent. Persist `household_share_status` and `mixed_allocation_consent_at`; authorize sharing changes against `created_by_user_id` and audit them. A shared transaction must have a Home allocation. Any allocation change clears consent and atomically returns sharing to `PRIVATE`; the creator must consent again. The API projection allowlist is transaction ID, Home allocation amount and currency, transaction calendar date, description, and category display name. Never expose transaction total, personal account identifiers/names/types/balances, personal allocations, beneficiary/private fields, notes, or unrelated personal history. Use a purpose-built projection; a separate table is not required.

### 3. Approved operational defaults
**Approved:** reusable records use `ACTIVE`/`ARCHIVED`; budget periods use `OPEN`/`CLOSED`; exact transitions must be defined before API implementation. New accounts default `include_in_safe_to_spend = FALSE`. Spaces take the owner/household-chosen IANA timezone at creation; each budget period snapshots it, and existing period dates/timezones remain unchanged after later space timezone updates. Invitations grant `MEMBER` only; ownership transfer is separate. Sound defaults off; reduced motion initializes from the platform preference and supports an explicit user override. Income occurrences permit multiple partial receipts, each linked to one transaction; each transaction links to at most one occurrence; reject cumulative overpayment until an adjustment policy is approved.

### 4. Allocation policy — existing baseline
**Recommendation:** allow partial allocations. Require `sum(allocations) <= transaction amount`, show the remainder explicitly, and never silently assume it belongs to a space.

### 5. Refund policy — approved
**Approved:** refunds are separate posted financial events linked to the original expense and explicit original allocation rows. Do not calculate proportional allocations silently. Preserve original space/category context and enforce refundable limits transactionally.

### 6. Posted transaction correction — approved
**Approved:** correction acts on a posted original and atomically marks it `VOIDED` and creates a posted replacement. Original entries and allocations remain unchanged for audit and are excluded from balances/current reporting. No reversing transaction or entries are created. The replacement carries `replaces_transaction_id`, pointing to the original; the unique constraint allows one direct replacement and forms an unambiguous chain. A voided transaction cannot be edited or reposted. A real refund/chargeback is a separate posted `REFUND` transaction, linked using `original_transaction_id` and allocation reversal links where applicable.

### 7. Income schedules — existing baseline
Model expected recurring and irregular income separately from actual receipts. A one-off occurrence must be possible without a recurring schedule. Multiple partial receipts are approved as stated above.

### 8. Partial bill payments — existing baseline
**Recommendation:** support many-to-many payment application through `commitment_payments`. A single expense transaction may cover multiple bill occurrences; one bill may be paid by multiple transactions.

### 9. Goal semantics and reserves — approved MVP scope
**Approved:** goal contributions are earmarks by default and do not move account money. Actual movement between accounts is a transfer. Complex reservation release and transfer-linked goal-progress behavior are deferred to the planning phase. Do not add schema relationships for deferred workflows in this milestone.

### 10. Safe-to-Spend scope — deferred
The schema may store eligible-account flags, but Safe-to-Spend calculation behavior and household-owned-account/personal-funded-Home treatment are deferred to the planning phase and require a separate product decision.

### 11. Multi-currency — approved baseline
**Approved:** LKR and USD are independent currencies with `minor_unit_digits = 2`; never aggregate them without an explicitly approved conversion context. Cross-currency transfers and conversion reporting are deferred. `fx_rates.rate` is not a monetary amount and its precision is a separate technical decision for future FX work.

### 12. Account balance reconciliation — existing baseline
**Recommendation:** use adjustment transactions with a reason and audit event, not editing a past opening balance after activity exists.

### 13. Deletion and retention — approved ordinary-operation rule; production policy deferred
Ordinary application operations must not destructively delete financial history. Use `RESTRICT` for financial-history deletion and immutable identifier updates unless a relationship explicitly requires otherwise. Production retention, erasure, backup, and household-removal policies remain deferred for separate approval.

## Risks and assumptions challenged

- **Money and UUID representation are fixed:** monetary amount columns use `DECIMAL(19,4)`; UUID keys use `BINARY(16)` and Python `UUID.bytes`/`UUID(bytes=...)` conversion. Validate input against currency minor units and reject excess fractional digits without implicit rounding.

- **A `transactions.account_id` column is insufficient** once transfers and multi-account effects exist. `account_entries` is the canonical balance effect.
- **A mutable `accounts.current_balance` is dangerous** as a source of truth. It can drift from transactions; only use rebuildable caches later.
- **A `spaces` table is not an account table.** Spaces classify and scope reporting; accounts hold money.
- **A bill's `PAID` flag cannot be authoritative alone.** Payment must link to a real posted expense transaction.
- **Expected income must not be mixed with cash.** Forecast occurrences and actual receipts are different records.
- **Goal contributions are not automatically expenses.** Earmarks and transfers have different financial effects.
- **Flexible budget pools:** MySQL nullable uniqueness is insufficient; use the generated normalized category key and unique period/key constraint documented in `DATABASE_COLUMN_CONTRACT.md`.
- **Aggregate checks need concurrency control.** Allocation totals, refund limits, bill-payment totals and reserve caps cannot be guaranteed by row-level CHECK constraints alone.
- **Soft delete is not a complete deletion policy.** Define exports, backups, retention and erasure semantics.
- **Cross-currency transfers are not just two numbers.** They require a documented rate, direction, fees, rounding and historical reporting rule.

## Remaining review gates

Before migrations, define exact state transition rules for `ACTIVE`/`ARCHIVED` reusable records and `OPEN`/`CLOSED` budget periods. The remaining `income_sources.source_type` labels do not control permissions or financial treatment. Deferred Safe-to-Spend scope, complex goal/reservation behavior, retention/erasure, and FX conversion policy remain out of scope until separately approved.

Implementation choices such as UUID type mechanics, FK update restriction, constraint naming, and index ordering are engineering decisions and do not require separate product approval. FX rate precision remains deferred; no cross-currency feature is implied.

After approval, create MySQL DDL through Alembic migrations and test migrations against an empty database and an upgrade path. Do not let an AI coding agent invent these policies during implementation.
