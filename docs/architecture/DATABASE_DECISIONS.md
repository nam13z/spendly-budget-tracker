# Spendly Database Decisions and Open Questions

## Recommended decisions for MVP

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
| Goals | Earmark or link to a transfer | Saving is not an expense |
| Reserves | Separate reservation records | Explicitly model money unavailable for ordinary spending |
| Currency | LKR/USD from launch; no implicit conversion | Avoid invalid arithmetic |
| Cross-currency transfer | Defer | Rate, fees, rounding and historical reporting policy unresolved |
| Posted correction | Auditable atomic void + replacement (no duplicate reversal entry) | Preserve history |
| Budget rollover | Defer from first release | Avoid unclear carry-forward/Safe-to-Spend interactions |

## Decisions to confirm before production migrations

### 1. Household-owned accounts
**Recommendation:** support them in the schema, even if the first UI focuses on personal accounts allocated to Home. A shared cash box or household bank account is a legitimate future use case.

### 2. Household transaction projection
**Recommendation:** initially expose only Home allocation amount, description, date and category, subject to creator's share setting. Hide payer's personal account name, full transaction total where it includes private allocations, Personal allocation, private notes and account balance.

### 3. Allocation policy
**Recommendation:** allow partial allocations. Require `sum(allocations) <= transaction amount`, show the remainder explicitly, and never silently assume it belongs to a space.

### 4. Refund policy
**Recommendation:** require linkage to the original expense when known. Refund allocations should offset the original space/category allocations. For a split purchase, allow user-confirmed proportional allocation as a convenience, but persist explicit allocation rows.

### 5. Posted transaction correction
**Recommendation:** expose an Edit action in UI, but implement it as one atomic, auditable void + replacement workflow. The voided original entries remain stored for audit but are excluded from balances. Do not also create a separate reversing entry for that same edit. A real refund/chargeback is a separate posted event.

### 6. Income schedules
**Recommendation:** model expected recurring and irregular income separately from actual receipts. A one-off occurrence must be possible without a recurring schedule. Partial receipt should be supported.

### 7. Partial bill payments
**Recommendation:** support many-to-many payment application through `commitment_payments`. A single expense transaction may cover multiple bill occurrences; one bill may be paid by multiple transactions.

### 8. Goal semantics and reserves
**Recommendation:** distinguish earmarking from moving cash. Earmark creates a `fund_reservation`; a transfer creates ledger entries and may be linked to the goal. Do not subtract the same money from Safe-to-Spend twice.

### 9. Safe-to-Spend scope
**Recommendation:** calculate per selected space/household and currency. Explicitly configure eligible accounts and horizon. Confirm how household-owned accounts and personal-account-funded Home allocations affect a household-level calculation before implementing that calculation.

### 10. Multi-currency
**Recommendation:** support independent LKR and USD balances immediately. Defer cross-currency transfers and combined converted dashboards until rate source, rate date, fees, rounding and historical-rate policy are agreed.

### 11. Account balance reconciliation
**Recommendation:** use adjustment transactions with a reason and audit event, not editing a past opening balance after activity exists.

### 12. Deletion and retention
**Recommendation:** archive/void financial records and implement export/deletion as a separate privacy workflow. Legal erasure, audit retention, backups and household membership removal need an explicit policy before launch.

## Risks and assumptions challenged

- **A `transactions.account_id` column is insufficient** once transfers and multi-account effects exist. `account_entries` is the canonical balance effect.
- **A mutable `accounts.current_balance` is dangerous** as a source of truth. It can drift from transactions; only use rebuildable caches later.
- **A `spaces` table is not an account table.** Spaces classify and scope reporting; accounts hold money.
- **A bill's `PAID` flag cannot be authoritative alone.** Payment must link to a real posted expense transaction.
- **Expected income must not be mixed with cash.** Forecast occurrences and actual receipts are different records.
- **Goal contributions are not automatically expenses.** Earmarks and transfers have different financial effects.
- **A simple unique key with nullable category may not prevent duplicate flexible budget pools in MySQL.** Use a generated key or service invariant.
- **Aggregate checks need concurrency control.** Allocation totals, refund limits, bill-payment totals and reserve caps cannot be guaranteed by row-level CHECK constraints alone.
- **Soft delete is not a complete deletion policy.** Define exports, backups, retention and erasure semantics.
- **Cross-currency transfers are not just two numbers.** They require a documented rate, direction, fees, rounding and historical reporting rule.

## Suggested review gate

Before migrations, review and approve:
1. The ERD and ownership boundaries.
2. Refund allocation behavior.
3. Correction/reversal semantics.
4. Household projections and household Safe-to-Spend scope.
5. Reservation and goal accounting.
6. Currency precision and cross-currency deferral.
7. Deletion/audit retention policy.

After approval, create MySQL DDL through Alembic migrations and test migrations against an empty database and an upgrade path. Do not let an AI coding agent invent these policies during implementation.
