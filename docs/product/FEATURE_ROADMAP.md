# Feature Roadmap

Roadmap is outcome-based, not a promise of fixed dates. Each phase must pass its exit criteria before expanding.

## Phase 0 — Product and technical foundation
- Confirm product scope and open decisions.
- Create repository and branch protection.
- Establish frontend/backend skeletons.
- Docker Compose for local MySQL and services.
- CI for lint, type checks and tests.
- Authentication threat model.
- Financial domain types and Decimal conventions.

**Exit:** clean clone can run locally using documented commands; CI passes.

## Phase 1 — Trusted financial core
- User registration/login/session.
- Personal profile and base currency.
- Accounts and opening balances.
- Categories.
- Income/expense transactions.
- Transaction listing/detail/edit.
- Database migrations.
- Audit-sensitive operations and idempotency.
- Critical financial unit/integration tests.

**Exit:** a user can record and correct transactions; balances and reports reconcile in tests.

## Phase 2 — Spaces and allocation model
- Personal and Home spaces.
- Transaction allocations.
- Split expense entry.
- Household creation and invitations.
- Owner/Member access.
- Privacy isolation tests.

**Exit:** one transaction can be allocated across spaces without double-counting; household isolation tests pass.

## Phase 3 — Budgeting and commitments
- Flexible budgets and periods.
- Bills and recurring schedules.
- Mark-paid workflow linked to transactions.
- Savings goals and contributions.
- Safe-to-Spend baseline and explanation.

**Exit:** calculations reconcile against documented scenarios; UI clearly distinguishes balance, budget and forecast.

## Phase 4 — Insights and product polish
- Category/trend charts.
- Contextual insights.
- Search/filter improvements.
- Onboarding refinement.
- Personalization preferences.
- Motion and accessibility pass.
- Export and account deletion.
- Backup/restore rehearsal.

**Exit:** usability testing shows users can complete core tasks and understand key figures.

## Phase 5 — Private beta
- Invite-only user testing.
- Error monitoring with privacy-safe metadata.
- Performance testing.
- Security review.
- Data export/delete verification.
- Bug triage and onboarding improvements.

**Exit:** no unresolved critical/high severity issues; support and recovery processes exist.

## Later phases
- PWA enhancements.
- Offline transaction capture and synchronization.
- Flutter Android/iOS clients.
- Native widgets, haptics and notifications.
- FX conversion provider and multi-currency reporting.
- AI explanation layer grounded in verified calculation facts.
- Optional bank import after provider/security review.

## Scope guardrails

Do not start AI, bank sync, complex forecasting, social features or mobile clients before the core financial model is stable. A beautiful UI over incorrect money logic is a failed product.
