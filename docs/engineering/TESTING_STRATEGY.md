# Testing Strategy

## 1. Testing pyramid

### Unit tests
Test pure financial functions, validation, recurrence and formatting rules.

### Integration tests
Test services with a real test database, transactions, constraints and authorization.

### API tests
Test request/response contracts, validation errors, idempotency and access control.

### End-to-end tests
Test critical user journeys in a browser.

### Manual exploratory tests
Check usability, visual quality, confusing edge cases and accessibility.

## 2. Critical financial test suites

- Decimal precision and rounding.
- Account balance calculations.
- Transfers and transfer fees.
- Refunds and partial refunds.
- Split allocations and unallocated remainder.
- Budget period boundaries and timezone behavior.
- Commitments and paid transaction linkage.
- Expected vs received income.
- Safe-to-Spend with missing/stale data.
- Multi-currency non-summation and FX conversion.
- Voided/archived transaction behavior.
- Idempotency and concurrent requests.

## 3. Security tests

- User A cannot read/update User B resources.
- Household member cannot read another member's private records.
- Invitation expiry/revocation/use limits enforced.
- Role checks enforced server-side.
- Session revocation works.
- CSRF protections work for cookie-authenticated writes.
- Rate limits on login, password reset and invitation endpoints.
- Export and deletion scope is correct.

## 4. Frontend tests

- Form validation and preserved input after errors.
- Currency formatting for LKR/USD.
- Quick expense flow.
- Allocation editor total behavior.
- Budget progress and empty states.
- Responsive layout.
- Reduced-motion behavior.
- Accessible chart alternative.

## 5. E2E critical paths

1. Register → onboarding → add account → record expense.
2. Record split expense → verify total and per-space reports.
3. Create transfer → verify no income/expense inflation.
4. Create bill → pay it → verify it is counted once.
5. Create budget → add expense → verify remaining.
6. Create household → invite second user → verify privacy.
7. Export data → validate contents.
8. Request deletion → verify documented workflow.

## 6. Test data

Use deterministic synthetic fixtures. Never use actual family/user financial data in automated tests.

## 7. Release gates

- All critical tests pass.
- No known critical/high severity financial or authorization defects.
- Migration tested from clean DB and previous schema.
- Backup restore rehearsed.
- E2E smoke suite passes in staging.
- Accessibility and responsive QA completed.
