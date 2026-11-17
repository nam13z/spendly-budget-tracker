# Financial Logic & Invariants

This document is authoritative for financial behavior. If UI, API or agent assumptions conflict with this document, stop and resolve the conflict.

## 1. Money representation

- Backend: Python `Decimal`.
- Database: `DECIMAL(19,4)` baseline, subject to currency/scale validation.
- API: monetary amounts transmitted as decimal strings, e.g. `"1250.50"`.
- Frontend: decimal-safe library or string arithmetic; never authoritative JS floating-point arithmetic.
- Rounding: explicit currency-aware rounding mode at defined boundaries.
- Store currency code with every amount.

## 2. Separate the concepts

- Account balance: money held in an account.
- Transaction: actual financial event.
- Allocation: attribution of a transaction to spaces/beneficiaries.
- Budget: planned spending.
- Commitment: expected future obligation.
- Goal: desired future reserve/target.
- Safe-to-Spend: derived planning estimate.

Never treat these as interchangeable.

## 3. Account balance

For a given account and currency, a basic posted balance is:

`opening balance + posted income + inbound transfers + refunds/adjustments - posted expenses - outbound transfers`

Exact sign and refund semantics must be encoded in one tested ledger service. A refund should reverse or offset the original expense according to explicit policy, not be misclassified as ordinary salary income.

Voided transactions do not affect balances. Editing a posted transaction must atomically update the authoritative record and any derived views.

## 4. Transaction allocation

For a fully allocated transaction:

`sum(allocation amounts) = transaction amount`

For partially allocated transactions:

`sum(allocation amounts) <= transaction amount`

The unallocated remainder must be explicit and visible. Do not silently discard it.

Example:
- One grocery expense: LKR 5,000.
- Home allocation: LKR 2,500.
- Personal allocation: LKR 2,500.
- Actual account outflow: LKR 5,000.
- Combined expense reporting: LKR 5,000.
- Home space expense: LKR 2,500.
- Personal space expense: LKR 2,500.

Allocations are attribution, not separate cash movements.

## 5. Transfers

A transfer moves money between accounts. It is not income or expense at the user-level consolidated view.

For same-currency transfer:
- source decreases by X;
- destination increases by X;
- consolidated net worth/cash total is unchanged, ignoring fees.

For cross-currency transfer:
- store source amount/currency and destination amount/currency;
- store applied rate, fee and date;
- do not fabricate a rate;
- record any FX gain/loss only if the product explicitly supports accounting for it.

## 6. Refunds

A refund should link to the original transaction when possible. Support partial refunds. Prevent refunded amount from exceeding refundable amount unless an explicit correction workflow exists. Display net category spending consistently.

## 7. Budgets

Budget remaining is not account balance.

`budget remaining = planned allocation - eligible posted spending in the budget period`

Rules:
- define period boundaries in user's timezone;
- include only transactions in the relevant scope and category;
- use allocations for space-specific spending;
- avoid counting transfers as spending;
- handle refunds by reducing eligible net spending;
- show adjustments to planned allocation separately from actual spend.

## 8. Commitments and expected income

A commitment is a forecast obligation until paid. When paid, link it to a posted transaction. Avoid counting both the bill amount and payment transaction as two cash outflows.

Expected income is a scenario, not cash on hand. Display it separately. A forecast may include it with a confidence/assumption label, but current balance must not.

## 9. Safe-to-Spend

Safe-to-Spend is a planning estimate, not a guarantee.

Recommended initial transparent baseline, calculated per selected scope and currency:

`Safe-to-Spend = eligible available balances - unpaid commitments due within horizon - user-designated reserves - safety buffer`

Optional scenario view may add expected income, but must show it separately and never merge it into confirmed available funds.

Key policies:
- define the horizon (e.g. until next income date or user-selected date);
- exclude accounts marked as unavailable/long-term savings unless user includes them;
- avoid double-subtracting bills already paid;
- avoid subtracting goal contributions twice if already reserved in an account;
- avoid counting transfers as expenses;
- show missing account coverage and stale data;
- if data is insufficient, show “Not enough information yet” rather than a confident number;
- show included commitments, reserves and accounts;
- user can adjust buffer and eligible accounts;
- timestamp the calculation and state assumptions.

Do not present this as financial advice or guarantee.

## 10. Multi-currency

- Every account and transaction has its own currency.
- Do not add LKR and USD directly.
- A reporting currency is selected for cross-currency summaries.
- Conversion needs a rate source, rate timestamp, direction and rounding policy.
- Preserve original transaction amount permanently.
- If no rate is available, show separate currency totals rather than guessing.
- Historical reports should use a documented historical-rate policy.

## 11. Time and recurrence

- Store event timestamps in UTC where time-of-day matters.
- Store due dates as dates in the user's timezone.
- Recurrence generates expected occurrences; it must not create duplicate posted transactions.
- Use idempotent job keys for generated occurrences.
- Handle month-end recurrence (e.g. 31st) explicitly.

## 12. Reconciliation test scenarios

1. Opening LKR 10,000; expense LKR 2,000 → balance LKR 8,000.
2. Opening LKR 10,000; transfer LKR 3,000 to another account → source 7,000, destination +3,000, total unchanged.
3. LKR 5,000 expense split 2,500/2,500 → total spend 5,000.
4. LKR 1,000 partial refund against LKR 4,000 expense → net expense 3,000.
5. Expected salary LKR 50,000 → actual balance unchanged.
6. Bill LKR 4,000 paid with linked expense → commitment no longer unpaid; expense counted once.
7. A budget of LKR 20,000 with eligible spend LKR 7,500 → remaining LKR 12,500.
8. Same numeric amounts in LKR and USD → never summed without conversion.
9. Voided expense → no balance or budget impact.
10. Partial allocation remainder → shown as unallocated, not lost.
