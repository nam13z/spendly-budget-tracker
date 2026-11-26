# Spendly Database Architecture — Logical Schema

**Version:** 1.2
**Status:** Owner-approved logical architecture; physical column details are specified in [DATABASE_COLUMN_CONTRACT.md](DATABASE_COLUMN_CONTRACT.md). This is not production DDL.
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

- Use `BINARY(16)` for every UUID primary and foreign key. In Python expose `uuid.UUID`; bind with `UUID.bytes` and read with `UUID(bytes=...)`. Do not use `bytes_le`, `CHAR(36)`, or mixed/dialect-native representations. Natural keys such as `currencies.code` retain their native types.
- Store event timestamps in UTC. Budget periods use the relevant personal or household space timezone and its local calendar; the start boundary is inclusive and the end boundary exclusive. Store due dates and period boundaries as `DATE`.
- Use `created_at`, `updated_at`, and where relevant `archived_at`, `voided_at`, `deleted_at`.
- Use foreign keys and `ON DELETE RESTRICT` for financial history. Use `ON UPDATE RESTRICT` for immutable identifiers unless a documented relationship requires otherwise. Ordinary application operations must not destructively delete financial history. Retention, erasure, backup, and legal policy are deferred for separate approval.
- Use explicit status enums or constrained strings with documented values. Do not use free-form strings for state transitions.
- Every monetary amount column uses MySQL `DECIMAL(19,4)` and SQLAlchemy `Numeric(19, 4, asdecimal=True)`. Python calculations use `Decimal`; API amounts use decimal strings. Validate input/posting against the currency's `minor_unit_digits` and reject excess fractional digits; never silently round. Storage scale and display precision are separate. LKR and USD use `minor_unit_digits = 2`; display formatting follows currency metadata. Currencies requiring more than four fractional digits are unsupported without a reviewed storage change. FX rates are not monetary amounts; their precision is a separate future technical decision.
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
`sound_enabled` defaults to false. Initialize `reduced_motion` from the platform preference and allow the user to override it explicitly.

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
Invitations grant `MEMBER` only. Household ownership transfer is a separate operation.

### `spaces`
A reporting and planning context such as Personal, Home or a future custom space. A space is not a bank account and does not hold money.

Key fields: `id`, `owner_user_id` nullable, `household_id` nullable, `name`, `type` (`PERSONAL`, `HOME`, `CUSTOM`), `timezone` (IANA TZID), `visibility_policy`, `archived_at`, `created_at`, `updated_at`.

Critical invariant: exactly one of `owner_user_id` or `household_id` is non-null. Personal spaces are user-owned; Home spaces are household-owned. Enforce this with a database `CHECK` where supported and validate in the service layer too.

Relationships: a user owns multiple personal spaces; a household owns one or more spaces; a space receives transaction allocations and owns budget plans, commitments and goals.

### Household visibility contract

Personal spaces remain private; household spaces are visible to active members, but transactions remain private unless explicitly shared. Persist `household_share_status` (`PRIVATE`, `SHARED`, default `PRIVATE`) and nullable `mixed_allocation_consent_at`; only the transaction creator may change sharing status. A shared transaction must have a Home allocation identifying the household projection scope. If it also has Personal allocations, explicit mixed-allocation consent must be recorded before sharing. Any allocation change clears consent and atomically resets sharing to `PRIVATE`; the creator must consent again to share. The API allowlist is transaction ID, Home allocation amount and currency, transaction calendar date, description, and category display name. Never return transaction total, account ID/name/type/balance, personal allocations, beneficiary/private fields, notes, unrelated personal history, or the full transaction ORM object. See the column contract for cross-row enforcement. No separate projection table is required.

Spaces receive the owner's or household's chosen IANA timezone at creation. Each budget period stores a timezone snapshot and uses inclusive start/exclusive end dates. Changing the space timezone does not reinterpret existing period dates or snapshots.

Reusable records use `ACTIVE`/`ARCHIVED`; where a reusable entity has no `status` field, `archived_at` null means active and a timestamp means archived. Budget periods use `OPEN`/`CLOSED`. Define exact transition rules before API implementation. New accounts default `include_in_safe_to_spend = FALSE`. Household invitations grant `MEMBER` only; ownership transfer is a separate operation. Sound defaults off; reduced-motion initializes from the platform preference and supports an explicit user override.

## 5. Money and transaction domain

### `currencies`
Reference metadata for supported currencies.

Key fields: `code` (ISO 4217 code, PK), `name`, `symbol`, `minor_unit_digits`, `is_enabled`.

Seed LKR and USD with `minor_unit_digits = 2`. Currency metadata controls accepted fractional precision and display formatting; it does not itself supply an exchange rate. Validate all user-entered monetary amounts (including planning values) and posted amounts against this precision; reject excess digits without rounding.

### `accounts`
A place where money is held, such as cash, bank or savings.

Key fields: `id`, `owner_user_id` nullable, `household_id` nullable, `name`, `type` (`CASH`, `BANK`, `SAVINGS`, `OTHER`), `currency_code`, `include_in_safe_to_spend`, `status`, `created_at`, `updated_at`, `archived_at`.
New accounts default `include_in_safe_to_spend` to `FALSE`.

Critical invariant: exactly one owner scope is set (user OR household). A household membership does not grant access to a member's personal account. Account currency is fixed for the account's lifetime; changing currency should require creating a new account and transferring/reconciling funds.

Do not store an authoritative `opening_balance` or mutable `current_balance` here. Opening balances and later corrections are ledger events.

### `categories`
A classification for income or expense allocations.

Key fields: `id`, `owner_user_id` nullable, `household_id` nullable, `name`, `kind` (`INCOME`, `EXPENSE`), `icon_key`, `color_key`, `is_system_default`, `archived_at`, `created_at`.

Scope rule: system defaults have both owner columns null; user/household categories have exactly one set. A category's kind must match the transaction/allocation context. Transfers are not categorized as income or expense in consolidated reporting.

### `financial_transactions`
The canonical record of a real-world financial event.

Key fields: `id`, `created_by_user_id`, `transaction_type` (`INCOME`, `EXPENSE`, `TRANSFER`, `REFUND`, `OPENING_BALANCE`, `ADJUSTMENT`), `status` (`DRAFT`, `POSTED`, `VOIDED`), `amount` (positive `DECIMAL(19,4)`), `currency_code`, `occurred_at`, `description`, `notes`, `original_transaction_id` nullable (refund-to-original link), `replaces_transaction_id` nullable (set on replacement; unique FK to the transaction it replaces), `household_share_status`, `mixed_allocation_consent_at`, `voided_at`, `void_reason`, `created_at`, `updated_at`.

The amount is always positive; direction is represented by account entries. A normal income/expense transaction has one account effect in MVP. A same-currency transfer has two account effects. For correction, atomically mark the posted original `VOIDED` and create a new posted replacement whose `replaces_transaction_id` points to the original. The original and its entries/allocations remain unchanged for audit and are excluded from balance/current reporting. A unique constraint on `replaces_transaction_id` permits one direct replacement and makes a chain unambiguous. Voided transactions cannot be edited or reposted. No separate reversing transaction or entries are created by correction. `original_transaction_id` is reserved for a real posted refund linked to its original expense; refunds are not corrections.

Do not put a single `account_id` on the transaction header as the canonical source of account effects: `account_entries` is authoritative and supports transfers cleanly. If the UI needs a display account, derive it from the relevant entry.

### `account_entries`
The signed effect of a posted transaction on a particular account.

Key fields: `id`, `transaction_id`, `account_id`, `amount_signed` (non-zero `DECIMAL(19,4)`), `currency_code`, `entry_role` (`INCOME`, `EXPENSE`, `TRANSFER_SOURCE`, `TRANSFER_DESTINATION`, `REFUND`, `OPENING_BALANCE`, `ADJUSTMENT`), `created_at`.

Positive entries increase account balance; negative entries decrease it. Composite foreign keys enforce that the entry currency equals both its account and transaction currency.

Balance formula:

`account_balance = SUM(account_entries.amount_signed where parent financial_transactions.status = POSTED)`

A voided or draft transaction contributes zero. Retain voided entries; do not delete or reverse them in a correction. Do not add a separate opening-balance column to this formula.

### `transaction_allocations`
Attributes an event to a space/category/beneficiary without moving money.

Key fields: `id`, `transaction_id`, `space_id`, `category_id` nullable, `beneficiary_user_id` nullable, `amount` (positive `DECIMAL(19,4)`), `reverses_allocation_id` nullable, `created_at`.

MVP allocation currency equals transaction currency; it can be derived from the parent transaction rather than redundantly stored. Allocation sums may be less than the transaction amount; the remainder must be explicitly displayed as unallocated. Sum may never exceed the eligible transaction amount.

Keep allocations of voided originals unchanged for audit and exclude them from current reporting through the parent transaction status. Replacements receive new allocation rows. For MVP refunds, require explicit allocation rows linked by `reverses_allocation_id` to original allocations; do not calculate proportional allocation silently. Refund allocation rows retain original space/category context and reduce net expense based on transaction type. A partial refund must not exceed the unrefunded amount of the original transaction/allocation, enforced transactionally.

Allocations use a space authorized for the transaction creator. A category must be system-scoped or share the allocation space's ownership scope, and category kind must match the transaction. Validate these polymorphic scope rules in the server transaction. Transfers have no allocations in MVP; transfer-to-goal behavior is deferred.

### `transfer_details`
Adds transfer-specific linkage to one transfer transaction.

Key fields: `transaction_id` (PK/FK), `source_account_entry_id` (unique FK), `destination_account_entry_id` (unique FK), `created_at`.

For MVP, both entry IDs are unique composite foreign keys paired with `transaction_id`, enforcing that they belong to this transfer. The service verifies transaction type, source/destination roles, same currency, equal absolute amounts and opposite signs. Cross-currency transfers are deferred. Fees should be represented as a separate expense transaction linked to the transfer (future relation), not hidden in an unbalanced transfer.

## 6. Income forecasting domain

Expected income is a forecast. It must not affect account balance until money is actually received and posted.

### `income_sources`
Named origin of income, e.g. salary, allowance, freelance client or family support.

Key fields: `id`, `owner_user_id`, `name`, `source_type`, `default_category_id` nullable, `status`, `created_at`, `updated_at`.

### `income_schedules`
A rule for expected income timing/amount. Supports recurring salary and irregular patterns.

Key fields: `id`, `income_source_id`, `space_id`, `expected_amount` (positive `DECIMAL(19,4)`), `currency_code`, `frequency_type` (`WEEKLY`, `BIWEEKLY`, `MONTHLY`, `CUSTOM`, `IRREGULAR`), `recurrence_rule` nullable, `expected_next_date` nullable, `confidence` nullable, `status`, `created_at`, `updated_at`.

For truly irregular income, a schedule may be a planning profile without auto-generating dates; users can add individual occurrences.

### `income_occurrences`
One expected receipt on a date or within a date window.

Key fields: `id`, `income_schedule_id` nullable, `income_source_id`, `space_id`, `expected_amount` (`DECIMAL(19,4)`), `currency_code`, `expected_date`, `status` (`EXPECTED`, `PARTIALLY_RECEIVED`, `RECEIVED`, `SKIPPED`, `CANCELLED`), `created_at`, `updated_at`.

A one-off expected receipt can exist without a recurring schedule.

### `income_receipts`
Links actual received money to one expected occurrence.

Key fields: `id`, `income_occurrence_id`, `transaction_id` (unique), `received_amount` (`DECIMAL(19,4)`), `received_at`, `created_at`.

The linked transaction must be a posted income transaction in the same currency. One occurrence may have multiple receipts for partial receipt; each receipt links to one transaction, and each actual transaction may link to at most one occurrence (unique `income_receipts.transaction_id`). Reject cumulative receipt overpayment until an adjustment policy is approved. The actual income transaction and account entry are the balance source of truth; this link only reconciles forecast to actual.

## 7. Budgeting domain

### `budget_plans`
A named plan for one space and currency.

Key fields: `id`, `space_id`, `name`, `currency_code`, `period_type` (`WEEKLY`, `MONTHLY`, `CUSTOM`), `status`, `created_at`, `updated_at`.

### `budget_periods`
A concrete instance of a plan for a date range.

Key fields: `id`, `budget_plan_id`, `period_start`, `period_end`, `timezone_snapshot`, `status`, `created_at`.

Store the space timezone used to generate the period as `timezone_snapshot` so later space-timezone changes do not reinterpret historical period boundaries. Start is inclusive and end is exclusive. Ensure period ranges for the same plan do not overlap unless an explicit product rule permits it.
Budget periods use `OPEN`/`CLOSED`; exact transitions must be defined before API implementation. Reusable records use `ACTIVE`/`ARCHIVED`.

### `budget_allocations`
Planned amount per category in a budget period.

Key fields: `id`, `budget_period_id`, `category_id` nullable (null represents a flexible/unallocated pool), `planned_amount` (`DECIMAL(19,4)`), `created_at`, `updated_at`.

Budget remaining is derived: planned allocation minus eligible net posted spending in that space/category/period. Do not store a mutable `remaining_amount`. MySQL permits multiple NULLs in UNIQUE indexes, so `budget_allocations.category_unique_key` is a stored generated `BINARY(16)` value equal to `COALESCE(category_id, all-zero UUID)`, with all-zero category IDs prohibited by CHECK. Unique `(budget_period_id, category_unique_key)` permits one flexible pool and one allocation per category.

## 8. Commitments and bills domain

### `commitment_templates`
A reusable one-time or recurring obligation definition.

Key fields: `id`, `space_id`, `name`, `expected_amount` (`DECIMAL(19,4)`), `currency_code`, `category_id` nullable, `recurrence_rule` nullable, `status`, `created_at`, `updated_at`.

A one-time bill can have a template with no recurrence rule. The template is not itself a payment.

### `commitment_occurrences`
A specific due obligation generated from a template or entered manually.

Key fields: `id`, `commitment_template_id` nullable, `space_id`, `name_snapshot`, `expected_amount` (`DECIMAL(19,4)`), `currency_code`, `due_date`, `status` (`UPCOMING`, `PARTIALLY_PAID`, `PAID`, `SKIPPED`, `CANCELLED`), `created_at`, `updated_at`.

Snapshot name/amount/currency where required so later template edits do not rewrite historical due obligations.

### `commitment_payments`
Applies part of a real transaction to a bill occurrence.

Key fields: `id`, `commitment_occurrence_id`, `transaction_id`, `applied_amount` (`DECIMAL(19,4)`), `created_at`.

Supports partial payments and one payment transaction covering multiple bills. The linked transaction must be a posted expense in the same currency. Sum applied to an occurrence cannot exceed its amount; sum applied from a transaction cannot exceed the eligible expense amount. A bill is paid only when outstanding reaches zero. Waiver/adjustment workflows are deferred and no schema relationship for them is introduced in this phase.

## 9. Goals and reserves domain

### `goals`
A target such as emergency savings or a planned purchase.

Key fields: `id`, `space_id`, `name`, `target_amount` (`DECIMAL(19,4)`), `currency_code`, `target_date` nullable, `status`, `created_at`, `updated_at`.

Goal progress is based on linked contributions/reservations according to the chosen goal policy, not a duplicate account balance.

### `goal_contributions`
Records a contribution toward a goal.

Key fields: `id`, `goal_id`, `contribution_type` (`EARMARK`), `amount` (`DECIMAL(19,4)`), `currency_code`, `fund_reservation_id`, `contributed_at`, `note`.

MVP goal contributions are earmarks linked to a `fund_reservation` through `fund_reservation_id`; no cash movement occurs. Actual movement between accounts is represented by an ordinary transfer. Transfer-linked goal progress and complex reservation release behavior are deferred; do not add a transfer link or related schema behavior in this phase. A goal contribution is never an expense merely because the user is saving.

### `fund_reservations`
Represents money the user deliberately treats as unavailable for ordinary spending.

Key fields: `id`, `account_id`, `space_id` nullable, `amount` (`DECIMAL(19,4)`), `currency_code`, `reservation_type` (`MANUAL`, `GOAL`), `status` (`ACTIVE`, `RELEASED`), `reason`, `created_at`, `released_at`.

A reservation is an earmark, not a ledger entry. Active reservations must not exceed eligible available funds in the account/scope. Manual reservation release and complex transfer-linked goal behavior are deferred; `RELEASED` records may be retained, but the lifecycle for those deferred cases is not specified here. A transfer into an excluded savings account must not also be subtracted as a source-account reservation after the transfer.

The goal/reservation relationship uses only the unique `goal_contributions.fund_reservation_id` foreign key. Do not add a reverse `fund_reservations.goal_contribution_id`; removing that redundant edge avoids a DDL dependency cycle. Manual reservations have no goal contribution.

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

Key fields: `id`, `base_currency_code`, `quote_currency_code`, `rate` (precision/scale TBD for future FX; not a monetary amount), `rate_source`, `rate_timestamp`, `created_at`.

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
- `goals` 1—many `goal_contributions`; MVP contributions are earmarks linked to reservations by unique `goal_contributions.fund_reservation_id`. The reverse FK on reservations is omitted to avoid a cycle. Transfer-linked goal progress is deferred.
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
- Unique `(accounts.id, accounts.currency_code)` and `(financial_transactions.id, financial_transactions.currency_code)` candidate keys for currency-matching entry FKs.
- Index `financial_transactions(created_by_user_id, occurred_at, id)` and `(status, transaction_type, occurred_at)`.
- Unique `financial_transactions.replaces_transaction_id`; `account_entries(id, transaction_id)` candidate key; indexes `account_entries(account_id, created_at, id)` and `(transaction_id)`.
- Index `transaction_allocations(space_id, transaction_id)`, `(transaction_id)`, and `(reverses_allocation_id)`.
- Unique source and destination entry IDs on `transfer_details`; composite FKs tie each to `transaction_id`.
- Unique `(budget_plan_id, period_start, period_end)`; index periods by date.
- Unique `(budget_period_id, category_unique_key)` on budget allocations to enforce one uncategorized/flexible pool.
- Index `commitment_occurrences(space_id, due_date, status)`.
- Index `income_occurrences(space_id, expected_date, status)`.
- Unique `income_receipts.transaction_id`; index `(income_occurrence_id, received_at)`.
- Unique `(commitment_occurrence_id, transaction_id)` and index `(transaction_id)` on commitment payments.
- Unique `goal_contributions.fund_reservation_id` (single FK direction; no reservation-to-contribution FK).
- Unique `(user_id, operation_scope, idempotency_key)`.
- Index idempotency records by expiry; audit events by `(resource_type, resource_id, occurred_at)` and `(actor_user_id, occurred_at)`.
- FX unique `(base_currency_code, quote_currency_code, rate_source, rate_timestamp)` and reverse pair/time index; rate precision and conversion remain deferred.
- Foreign keys use `ON DELETE RESTRICT ON UPDATE RESTRICT`; no cascade through financial/audit history.

Database `CHECK` constraints should enforce row-level rules (positive amounts, valid owner XOR, non-zero signed entries). Aggregate rules (allocation sums, refund caps, payment sums, reservation caps, balanced transfer entries) must be enforced in domain services inside atomic database transactions, with concurrency-safe locking and automated tests. A simple CHECK cannot validate sums across rows.

## 14. Column-level contract

The physical types, lengths, nullability, defaults, keys, checks, indexes, and FK actions for all 30 entities are specified in [DATABASE_COLUMN_CONTRACT.md](DATABASE_COLUMN_CONTRACT.md). That contract is normative with this logical schema and records remaining product-state decisions without adding entities or behavior.

## 15. Derived values — do not store as source of truth

Derive or cache-rebuild these values:

- Account balance from posted account entries.
- Transaction reporting totals from allocations.
- Budget remaining from plan minus eligible net posted allocations.
- Bill outstanding from expected amount minus linked payments.
- Income received amount from linked receipts.
- Goal progress from MVP earmark contributions/reservations; transfer-linked goal progress is deferred.
- Safe-to-Spend from eligible balances, unpaid commitments, active reserves and safety buffer.

A cache/materialized summary may be added for performance, but must be rebuildable and must never become a competing source of truth.

## 16. Recommended implementation order

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
