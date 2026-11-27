# API Specification — REST v1

This is a contract outline. Exact schemas should be generated from Pydantic models and published through OpenAPI.

## 1. Conventions

- Base path: `/api/v1`.
- JSON request/response.
- Amounts are decimal strings, never JSON floating-point numbers.
- IDs are opaque UUIDs.
- Timestamps are ISO 8601 UTC; date-only values use `YYYY-MM-DD`.
- Authentication: secure HttpOnly session cookie for browser.
- State-changing cookie-authenticated requests require CSRF protection.
- Pagination: `limit` + opaque `cursor` preferred.
- All protected queries enforce server-side ownership/membership.

## 2. Response/error shape

Success responses return resource objects or `{ "data": ..., "meta": ... }`.

Errors use a stable structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request could not be processed.",
    "details": [],
    "request_id": "opaque-id"
  }
}
```

Never return stack traces or internal SQL errors to clients.
All API errors include an opaque `request_id` and matching `X-Request-ID` response header.
Validation `details` may identify field locations and error codes, but must not include rejected
input values or internal exception messages. Unhandled errors return a generic message; internal
exception text and stack traces are not returned or logged.

## 3. Endpoint inventory

### Authentication
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/password/forgot`
- `POST /auth/password/reset`
- `GET /auth/session`
- `GET /auth/sessions`
- `DELETE /auth/sessions/{session_id}`

### User and preferences
- `GET /me`
- `PATCH /me`
- `GET /me/preferences`
- `PATCH /me/preferences`
- `GET /me/export`
- `POST /me/deletion-request`

### Households
- `POST /households`
- `GET /households`
- `GET /households/{household_id}`
- `PATCH /households/{household_id}`
- `GET /households/{household_id}/members`
- `DELETE /households/{household_id}/members/{user_id}`
- `POST /households/{household_id}/invitations`
- `POST /household-invitations/accept`
- `DELETE /households/{household_id}/invitations/{invitation_id}`

### Spaces
- `GET /spaces`
- `POST /spaces`
- `GET /spaces/{space_id}`
- `PATCH /spaces/{space_id}`
- `POST /spaces/{space_id}/archive`

### Accounts
- `GET /accounts`
- `POST /accounts`
- `GET /accounts/{account_id}`
- `PATCH /accounts/{account_id}`
- `POST /accounts/{account_id}/archive`
- `GET /accounts/{account_id}/balance`

### Categories
- `GET /categories`
- `POST /categories`
- `PATCH /categories/{category_id}`
- `POST /categories/{category_id}/archive`

### Transactions
- `GET /transactions`
- `POST /transactions`
- `GET /transactions/{transaction_id}`
- `PATCH /transactions/{transaction_id}` — correcting a posted transaction atomically voids the original and creates/returns a posted replacement; voided records cannot be edited or reposted.
- `POST /transactions/{transaction_id}/void`
- `POST /transfers`
- `POST /transactions/{transaction_id}/refunds`
- `GET /transactions/{transaction_id}/allocations`
- `PUT /transactions/{transaction_id}/allocations`

### Budgets
- `GET /budgets`
- `POST /budgets`
- `GET /budgets/{budget_id}`
- `PATCH /budgets/{budget_id}`
- `GET /budgets/{budget_id}/progress`

### Commitments
- `GET /commitments`
- `POST /commitments`
- `PATCH /commitments/{commitment_id}`
- `POST /commitments/{commitment_id}/payments`
- `POST /commitments/{commitment_id}/skip`

### Goals
- `GET /goals`
- `POST /goals`
- `PATCH /goals/{goal_id}`
- `POST /goals/{goal_id}/contributions`

### Insights
- `GET /overview`
- `GET /insights/spending`
- `GET /insights/cashflow`
- `GET /insights/budgets`
- `GET /safe-to-spend`

## 4. Example transaction create

```json
{
  "type": "EXPENSE",
  "amount": "5000.00",
  "currency": "LKR",
  "account_id": "uuid",
  "occurred_at": "2026-11-15T08:30:00Z",
  "description": "Groceries",
  "category_id": "uuid",
  "allocations": [
    { "space_id": "home-space-uuid", "amount": "2500.00" },
    { "space_id": "personal-space-uuid", "amount": "2500.00" }
  ]
}
```

Header: `Idempotency-Key: <random-unique-key>`

The server validates account access, currency compatibility, allocation sum, category access and space permissions before commit.

Transactions default to private. Sharing is creator-controlled; a shared transaction requires a Home allocation, and mixed Home/Personal allocations require explicit creator consent. Household transaction responses use a purpose-built projection containing only transaction ID, Home allocation amount and currency, transaction date in the Home space timezone, description, and category display name. They omit transaction total, account identifiers/names/types/balances, personal allocations, beneficiary/private fields, notes, and unrelated personal history.

Personal spaces remain private; household spaces are visible to active members. Any allocation change clears mixed-allocation consent and atomically returns the transaction to `PRIVATE`; the creator must consent again before sharing. New accounts default to `include_in_safe_to_spend = FALSE`. Space creation uses the owner's or household's chosen IANA timezone; each period snapshots it, and existing periods retain their original dates and timezone. Reusable records use `ACTIVE`/`ARCHIVED`; budget periods use `OPEN`/`CLOSED`, with exact transition rules defined before API implementation. Household invitations grant `MEMBER` only; ownership transfer is separate. Sound defaults off; reduced motion initializes from the platform preference and permits explicit user override. An income occurrence accepts multiple partial receipts; each receipt links to one transaction, each transaction links to at most one occurrence, and cumulative overpayment is rejected until an adjustment policy is approved.

The `/void` endpoint must not create a standalone posted void. Posted corrections atomically void the original and create a posted replacement; any endpoint performing that operation must require both effects in one database transaction.

## 5. Example response

```json
{
  "data": {
    "id": "transaction-uuid",
    "type": "EXPENSE",
    "amount": "5000.00",
    "currency": "LKR",
    "description": "Groceries",
    "allocations": [
      { "space_id": "home-space-uuid", "amount": "2500.00" },
      { "space_id": "personal-space-uuid", "amount": "2500.00" }
    ],
    "created_at": "2026-11-15T08:30:00Z"
  }
}
```

## 6. Validation and conflict codes

Suggested codes:
- `AUTH_REQUIRED`
- `FORBIDDEN`
- `NOT_FOUND`
- `VALIDATION_ERROR`
- `INSUFFICIENT_ALLOCATION`
- `ALLOCATION_EXCEEDS_TRANSACTION`
- `CURRENCY_MISMATCH`
- `IDEMPOTENCY_CONFLICT`
- `INVALID_INVITATION`
- `INVITATION_EXPIRED`
- `RESOURCE_ARCHIVED`
- `CONCURRENT_MODIFICATION`

## 7. API rules

- Never trust user/household IDs supplied by client without authorization checks.
- Use consistent pagination and filtering.
- Avoid returning unnecessary personal data.
- Apply the household projection allowlist to every household transaction response; never serialize the full transaction ORM object to household members.
- Use optimistic concurrency or version checks for sensitive edits where appropriate.
- Document all endpoints in OpenAPI.
- Add contract tests for financial endpoints.
