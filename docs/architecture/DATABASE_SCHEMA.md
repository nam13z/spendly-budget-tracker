# Spendly Database Architecture — Logical Schema

**Version:** 1.1  
**Status:** Architecture proposal for review; not production DDL  
**Target:** MySQL 8.4 LTS, SQLAlchemy 2.x, Alembic migrations, FastAPI

## 1. Architectural rules

1. A real-world event is recorded once in `financial_transactions`.
2. Its effect on money held is recorded in `account_entries`.
3. Its reporting attribution is recorded in `transaction_allocations`.
4. Budgets, commitments, income forecasts, goals and reserves are planning records, not substitutes for ledger entries.
5. A user's Personal space and a household's Home space are different ownership/security scopes.
6. All money values use exact decimal arithmetic. MySQL `DECIMAL`, Python `Decimal`, and decimal strings in JSON are required. Never use binary floating point for money.
7. Every monetary record has an explicit currency. Never aggregate unlike currencies without a recorded conversion context.
8. Posted history is corrected through an auditable void-and-replacement operation, not silent mutation. For MVP, voided entries remain stored but are excluded from balances; do not also post a duplicate reversing entry for the same correction.

## 2. Naming and common conventions

- Use UUID primary keys consistently; prefer `BINARY(16)` in MySQL if the application layer handles conversion consistently.
- Store event timestamps in UTC. Store due dates and budget-period boundaries as `DATE` interpreted in the owning user's/household's configured timezone.
- Use `created_at`, `updated_at`, and where relevant `archived_at`, `voided_at`, `deleted_at`.
- Use foreign keys and `ON DELETE RESTRICT` for financial history. Avoid cascading deletion through posted financial records.
- Use explicit status enums or constrained strings with documented values. Do not use free-form strings for state transitions.
- Monetary columns should use a deliberate precision such as `DECIMAL(19,4)` only if the supported currency precision and future FX requirements justify it. Currency metadata defines display/minor-unit precision; do not assume all currencies use two decimal places.
- Store API monetary values as strings, e.g. `"1250.00"`.

## 3. Identity domain

### `users`
One registered Spendly user.

Key fields: `id`, `email_normalized` (unique), `password_hash`, `display_name`, `status`, `primary_currency_code`, `timezone`, `created_at`, `updated_at`, `deleted_at`.

A user is the security principal. Never use a client-supplied `user_id` as proof of authorization.

### `sessions`
Server-managed authenticated sessions.

Key fields: `id`, `user_id`, `token_hash` (unique), `expires_at`, `last_seen_at`, `revoked_at`, `device_label`, `created_at`.

Relationship: one user has many sessions. Store only a hash of the opaque session token.

### `user_preferences`
User experience and notification preferences.

Key fields: `user_id` (PK/FK), `theme_key`, `accent_palette`, `communication_style`, `motion_level`, `sound_enabled`, `reduced_motion`, `notification_preferences` (JSON), `updated_at`.

Preferences must not become a container for financial source-of-truth data.

## 4. Household and space domain

### `households`
A shared financial collaboration boundary.

Key fields: `id`, `name`, `created_by_user_id`, `status`, `created_at`, `updated_at`.

The creator is not automatically the only person with ownership forever; current ownership/role is represented by membership.

### `household_memberships`
Connects users to households.

Key fields: `id`, `household_id`, `user_id`, `role` (`OWNER`, `MEMBER`), `status` (`INVITED`, `ACTIVE`, `LEFT`, `REMOVED`), `joined_at`, `created_at`.

Constraint: unique `(household_id, user_id)`. A user can belong to multiple households unless product policy later restricts this.

### `household_invitations`
Revocable, expiring invitation credential.

Key fields: `id`, `household_id`, `created_by_user_id`, `token_hash`, `role_to_grant`, `expires_at`, `max_uses`, `uses_count`, `revoked_at`, `created_at`.

Never store the raw invitation token. The QR code should encode only the invitation URL/token, not household financial data.

### `spaces`
A reporting and planning context such as Personal, Home or a future custom space. A space is not a bank account and does not hold money.

Key fields: `id`, `owner_user_id` nullable, `household_id` nullable, `name`, `type` (`PERSONAL`, `HOME`, `CUSTOM`), `visibility_policy`, `archived_at`, `created_at`, `updated_at`.

Critical invariant: exactly one of `owner_user_id` or `household_id` is non-null. Personal spaces are user-owned; Home spaces are household-owned. Enforce this with a database `CHECK` where supported and validate in the service layer too.

Relationships: a user owns multiple personal spaces; a household owns one or more spaces; a space receives transaction allocations and owns budget plans, commitments and goals.

## 5. Money and transaction domain

### `currencies`
Reference metadata for supported currencies.

Key fields: `code` (ISO 4217 code, PK), `name`, `symbol`, `minor_unit_digits`, `is_enabled`.

Seed at least LKR and USD. Currency metadata controls display precision; it does not itself supply an exchange rate.

### `accounts`
A place where money is held, such as cash, bank or savings.

Key fields: `id`, `owner_user_id` nullable, `household_id` nullable, `name`, `type` (`CASH`, `BANK`, `SAVINGS`, `OTHER`), `currency_code`, `include_in_safe_to_spend`, `status`, `created_at`, `updated_at`, `archived_at`.

Critical invariant: exactly one owner scope is set (user OR household). A household membership does not grant access to a member's personal account. Account currency is fixed for the account's lifetime; changing currency should require creating a new account and transferring/reconciling funds.

Do not store an authoritative `opening_balance` or mutable `current_balance` here. Opening balances and later corrections are ledger events.

### `categories`
A classification for income or expense allocations.

Key fields: `id`, `owner_user_id` nullable, `household_id` nullable, `name`, `kind` (`INCOME`, `EXPENSE`), `icon_key`, `color_key`, `is_system_default`, `archived_at`, `created_at`.

Scope rule: system defaults have both owner columns null; user/household categories have exactly one set. A category's kind must match the transaction/allocation context. Transfers are not categorized as income or expense in consolidated reporting.

### `financial_transactions`
The canonical record of a real-world financial event.

Key fields: `id`, `created_by_user_id`, `transaction_type` (`INCOME`, `EXPENSE`, `TRANSFER`, `REFUND`, `OPENING_BALANCE`, `ADJUSTMENT`), `status` (`DRAFT`, `POSTED`, `VOIDED`), `amount` (positive DECIMAL), `currency_code`, `occurred_at`, `description`, `notes`, `original_transaction_id` nullable (for refunds), `reversal_of_transaction_id` nullable (for explicit reversal/correction linkage), `voided_at`, `void_reason`, `created_at`, `updated_at`.

The amount is always positive; direction is represented by account entries. A normal income/expense transaction has one account effect in MVP. A same-currency transfer has two account effects. A refund is linked to the original expense and is not ordinary salary/income.

Do not put a single `account_id` on the transaction header as the canonical source of account effects: `account_entries` is authoritative and supports transfers cleanly. If the UI needs a display account, derive it from the relevant entry.

### `account_entries`
The signed effect of a posted transaction on a particular account.

Key fields: `id`, `transaction_id`, `account_id`, `amount_signed` (non-zero DECIMAL), `currency_code`, `entry_role` (`INCOME`, `EXPENSE`, `TRANSFER_SOURCE`, `TRANSFER_DESTINATION`, `REFUND`, `OPENING_BALANCE`, `ADJUSTMENT`), `created_at`.

Positive entries increase account balance; negative entries decrease it. The entry currency must equal the account currency. Enforce via composite FK or transaction service validation plus tests.

Balance formula:

`account_balance = SUM(account_entries.amount_signed for POSTED transactions)`

A voided transaction contributes zero. Do not add a separate opening-balance column to this formula.

### `transaction_allocations`
Attributes an event to a space/category/beneficiary without moving money.

Key fields: `id`, `transaction_id`, `space_id`, `category_id` nullable, `beneficiary_user_id` nullable, `amount` (positive DECIMAL), `reverses_allocation_id` nullable, `created_at`.

MVP allocation currency equals transaction currency; it can be derived from the parent transaction rather than redundantly stored. Allocation sums may be less than the transaction amount; the remainder must be explicitly displayed as unallocated. Sum may never exceed the eligible transaction amount.

For refunds, use `reverses_allocation_id` to associate a refund allocation with the original allocation when possible. Refund allocations are positive rows but reduce net expense in reports based on transaction type. A partial refund must not exceed the unrefunded amount of the original transaction/allocation.

Transfers normally have no expense/income allocations. If transfer-to-goal semantics are required, link the goal contribution to the transfer instead of classifying it as spending.

### `transfer_details`
Adds transfer-specific linkage to one transfer transaction.

Key fields: `transaction_id` (PK/FK), `source_account_entry_id` (unique FK), `destination_account_entry_id` (unique FK), `created_at`.

For MVP, source and destination entries must belong to the same transfer transaction, use the same currency, and have equal absolute amounts with opposite signs. Cross-currency transfers are deferred. Fees should be represented as a separate expense transaction linked to the transfer (future `related_transaction_id` or a dedicated relation), not hidden in an unbalanced transfer.

## 6. Income forecasting domain

Expected income is a forecast. It must not affect account balance until money is actually received and posted.

### `income_sources`
Named origin of income, e.g. salary, allowance, freelance client or family support.

Key fields: `id`, `owner_user_id`, `name`, `source_type`, `default_category_id` nullable, `status`, `created_at`, `updated_at`.

### `income_schedules`
A rule for expected income timing/amount. Supports recurring salary and irregular patterns.

Key fields: `id`, `income_source_id`, `space_id`, `expected_amount` (positive DECIMAL), `currency_code`, `frequency_type` (`WEEKLY`, `BIWEEKLY`, `MONTHLY`, `CUSTOM`, `IRREGULAR`), `recurrence_rule` nullable, `expected_next_date` nullable, `confidence` nullable, `status`, `created_at`, `updated_at`.

For truly irregular income, a schedule may be a planning profile without auto-generating dates; users can add individual occurrences.

### `income_occurrences`
One expected receipt on a date or within a date window.

Key fields: `id`, `income_schedule_id` nullable, `income_source_id`, `space_id`, `expected_amount`, `currency_code`, `expected_date`, `status` (`EXPECTED`, `PARTIALLY_RECEIVED`, `RECEIVED`, `SKIPPED`, `CANCELLED`), `created_at`, `updated_at`.

A one-off expected receipt can exist without a recurring schedule.

### `income_receipts`
Links actual received money to one expected occurrence.

Key fields: `id`, `income_occurrence_id`, `transaction_id`, `received_amount`, `received_at`, `created_at`.

The linked transaction must be a posted income transaction in the same currency. Multiple receipt rows allow partial receipts. The receipt sum cannot exceed expected amount without an explicit adjustment/overpayment policy. The actual income transaction and account entry are the balance source of truth; this link only reconciles forecast to actual.

## 7. Budgeting domain

### `budget_plans`
A named plan for one space and currency.

Key fields: `id`, `space_id`, `name`, `currency_code`, `period_type` (`WEEKLY`, `MONTHLY`, `CUSTOM`), `status`, `created_at`, `updated_at`.

### `budget_periods`
A concrete instance of a plan for a date range.

Key fields: `id`, `budget_plan_id`, `period_start`, `period_end`, `status`, `created_at`.

Use the user's/household's configured timezone to determine boundaries. Ensure period ranges for the same plan do not overlap unless an explicit product rule permits it.

### `budget_allocations`
Planned amount per category in a budget period.

Key fields: `id`, `budget_period_id`, `category_id` nullable (null represents a flexible/unallocated pool), `planned_amount`, `created_at`, `updated_at`.

Budget remaining is derived: planned allocation minus eligible net posted spending in that space/category/period. Do not store a mutable `remaining_amount`. Handle the single unallocated pool with a unique generated key or service invariant because MySQL UNIQUE indexes allow multiple NULL values.

## 8. Commitments and bills domain

### `commitment_templates`
A reusable one-time or recurring obligation definition.

Key fields: `id`, `space_id`, `name`, `expected_amount`, `currency_code`, `category_id` nullable, `recurrence_rule` nullable, `status`, `created_at`, `updated_at`.

A one-time bill can have a template with no recurrence rule. The template is not itself a payment.

### `commitment_occurrences`
A specific due obligation generated from a template or entered manually.

Key fields: `id`, `commitment_template_id` nullable, `space_id`, `name_snapshot`, `expected_amount`, `currency_code`, `due_date`, `status` (`UPCOMING`, `PARTIALLY_PAID`, `PAID`, `SKIPPED`, `CANCELLED`), `created_at`, `updated_at`.

Snapshot name/amount/currency where required so later template edits do not rewrite historical due obligations.

### `commitment_payments`
Applies part of a real transaction to a bill occurrence.

Key fields: `id`, `commitment_occurrence_id`, `transaction_id`, `applied_amount`, `created_at`.

Supports partial payments and one payment transaction covering multiple bills. The linked transaction must be a posted expense in the same currency. Sum applied to an occurrence cannot exceed its amount; sum applied from a transaction cannot exceed the eligible expense amount. A bill is paid only when the outstanding amount reaches zero or an explicit write-off/waiver state is recorded.

## 9. Goals and reserves domain

### `goals`
A target such as emergency savings or a planned purchase.

Key fields: `id`, `space_id`, `name`, `target_amount`, `currency_code`, `target_date` nullable, `status`, `created_at`, `updated_at`.

Goal progress is based on linked contributions/reservations according to the chosen goal policy, not a duplicate account balance.

### `goal_contributions`
Records a contribution toward a goal.

Key fields: `id`, `goal_id`, `contribution_type` (`EARMARK`, `TRANSFER_LINK`), `amount`, `currency_code`, `fund_reservation_id` nullable, `transfer_transaction_id` nullable, `contributed_at`, `note`.

For `EARMARK`, the contribution links to a fund reservation through `fund_reservation_id`; no cash movement occurs. For `TRANSFER_LINK`, the contribution links to a real transfer transaction; account entries already record the movement. Enforce exactly one relevant link for the selected contribution type. A goal contribution is never an expense merely because the user is saving.

### `fund_reservations`
Represents money the user deliberately treats as unavailable for ordinary spending.

Key fields: `id`, `account_id`, `space_id` nullable, `amount`, `currency_code`, `reservation_type` (`MANUAL`, `GOAL`), `goal_contribution_id` nullable, `status` (`ACTIVE`, `RELEASED`), `reason`, `created_at`, `released_at`.

A reservation is an earmark, not a ledger entry. Active reservations must not exceed the eligible available funds in the account/scope. Avoid reserving the same money through both a goal earmark and a manual reserve. A transfer into an excluded savings account should not also be subtracted as a reservation from the source account after the transfer.

## 10. Reliability, audit and FX

### `idempotency_records`
Prevents retried create requests from creating duplicate financial events.

Key fields: `id`, `user_id`, `operation_scope`, `idempotency_key`, `request_hash`, `response_reference`, `created_at`, `expires_at`.

Unique `(user_id, operation_scope, idempotency_key)`. Reuse with a different request hash must return a conflict, not silently replay a different operation.

### `audit_events`
Security and financial-history event log.

Key fields: `id`, `actor_user_id` nullable for system jobs, `action`, `resource_type`, `resource_id`, `occurred_at`, `metadata` (strict allowlist).

Do not store passwords, tokens, full private notes, or unnecessary financial detail in audit metadata. Define retention and user deletion behavior.

### `fx_rates`
Future conversion reference, not a reason to enable cross-currency transfers prematurely.

Key fields: `id`, `base_currency_code`, `quote_currency_code`, `rate`, `rate_source`, `rate_timestamp`, `created_at`.

Preserve original transaction amounts. Historical reporting policy must specify which rate/date/source to use. If no valid rate exists, show separate currency totals.

## 11. Relationship summary

- `users` 1—many `sessions`; `users` 1—1 `user_preferences`.
- `users` many—many `households` through `household_memberships`.
- `households` 1—many `household_invitations` and `spaces`.
- `users` 1—many personal `spaces`; each `space` has exactly one user or household owner.
- `users`/`households` 1—many `accounts` according to account owner scope.
- `financial_transactions` 1—many `account_entries` and 1—many `transaction_allocations`.
- `accounts` 1—many `account_entries`; `spaces` 1—many `transaction_allocations`.
- `financial_transactions` 1—0/1 `transfer_details`; transfer details identify two account entries.
- `income_sources` 1—many `income_schedules` and `income_occurrences`; occurrences 1—many `income_receipts`; receipts link to actual income transactions.
- `space` 1—many `budget_plans`, `commitment_occurrences`/templates and `goals`.
- `budget_plans` 1—many `budget_periods`; periods 1—many `budget_allocations`.
- `commitment_occurrences` many—many `financial_transactions` through `commitment_payments`.
- `goals` 1—many `goal_contributions`; contributions may link to reservations or transfer transactions.
- `accounts` 1—many `fund_reservations`.
- `users` 1—many `idempotency_records` and `audit_events`.

## 12. Authorization and ownership rules

- Every read/write must be authorized on the server against the resource's owner scope and active household membership.
- A personal account or Personal space is private even when its owner belongs to a household.
- Household-owned accounts/spaces are accessible only to active members and permitted roles.
- When a personal account pays a shared purchase, the household projection exposes only the Home allocation and explicitly approved fields. Do not return the full transaction ORM object to household members.
- MVP: a transaction may allocate to the creator's personal space(s) and at most one household context. Cross-household allocation is deferred.
- Use dedicated response DTOs/projections for personal and household views.

## 13. Indexes and constraints

At minimum:

- Unique `users.email_normalized`.
- Unique `sessions.token_hash`; index `(user_id, expires_at, revoked_at)`.
- Unique `(household_id, user_id)` on memberships; index `(user_id, status)`.
- Unique `household_invitations.token_hash`; index `(household_id, expires_at, revoked_at)`.
- Index `accounts(owner_user_id, status)` and `accounts(household_id, status)`.
- Index `financial_transactions(created_by_user_id, occurred_at, id)` and `(status, transaction_type, occurred_at)`.
- Index `account_entries(account_id, created_at, id)` and `(transaction_id)`.
- Index `transaction_allocations(space_id, transaction_id)` and `(transaction_id)`.
- Unique `(budget_plan_id, period_start, period_end)`; index periods by date.
- Index `commitment_occurrences(space_id, due_date, status)`.
- Index `income_occurrences(space_id, expected_date, status)`.
- Unique `(user_id, operation_scope, idempotency_key)`.
- Foreign keys for all relationships; `ON DELETE RESTRICT` for financial records.

Database `CHECK` constraints should enforce row-level rules (positive amounts, valid owner XOR, non-zero signed entries). Aggregate rules (allocation sums, refund caps, payment sums, reservation caps, balanced transfer entries) must be enforced in domain services inside atomic database transactions, with concurrency-safe locking and automated tests. A simple CHECK cannot validate sums across rows.

## 14. Derived values — do not store as source of truth

Derive or cache-rebuild these values:

- Account balance from posted account entries.
- Transaction reporting totals from allocations.
- Budget remaining from plan minus eligible net posted allocations.
- Bill outstanding from expected amount minus linked payments.
- Income received amount from linked receipts.
- Goal progress from contributions/reservations/transfers under explicit goal semantics.
- Safe-to-Spend from eligible balances, unpaid commitments, active reserves and safety buffer.

A cache/materialized summary may be added for performance, but must be rebuildable and must never become a competing source of truth.

## 15. Recommended implementation order

1. Currency metadata, users, sessions, preferences.
2. Households, memberships, invitations, spaces.
3. Accounts and categories.
4. Transaction headers, account entries and ledger service.
5. Allocations, refunds and transfer details.
6. Income sources, schedules, occurrences and receipt reconciliation.
7. Budget plans, periods and allocations.
8. Commitment templates, occurrences and payment links.
9. Goals, contributions and fund reservations.
10. Idempotency, audit, reporting projections and performance indexes.

Do not begin with all UI screens. Implement and test the financial core first.
