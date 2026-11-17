# Spendly — Project Implementation Plan

This roadmap sequences implementation using the approved architecture and supplied product requirements. It is a milestone plan, not authorization to begin later phases. Complete and review each assigned milestone before proceeding.

## Development workflow

1. Plan the milestone.
2. Prepare a scoped implementation task.
3. Inspect relevant code and documentation.
4. Implement only the approved scope.
5. Run tests and verification.
6. Review the code and diff.
7. Update documentation.
8. Obtain project owner approval before proceeding.

Codex must stop after each assigned milestone and wait for project owner approval before starting another.

## Phase 0 — Project governance

**Status: Planning baseline established.**

- **Objective:** Establish the authoritative project guidance, documentation map and milestone workflow.
- **Main implementation areas:** Preserve the supplied documentation and ADRs; define agent instructions; establish this roadmap and the initial repository layout.
- **Expected deliverables:** Documentation package retained; `AGENTS.md` governance rules; `PLANS.md`; baseline repository directories and safe local configuration templates.
- **Verification and completion criteria:** Required documents and ADRs are present and reviewed; governance and roadmap agree with the approved stack; requested directories exist; no application implementation or Git history changes were made.

## Phase 1 — Technical foundation

**Status: Current phase — not yet completed.**

- **Objective:** Create a minimal, runnable development foundation for the approved frontend, backend and local environment.
- **Main implementation areas:** Next.js + TypeScript frontend skeleton; FastAPI backend skeleton; shared configuration conventions; Docker development foundation; CI workflows; baseline lint, type-check and test tooling.
- **Expected deliverables:** Documented local setup; minimal health endpoints/pages as appropriate; reproducible development configuration; CI checks for frontend and backend.
- **Verification and completion criteria:** A clean checkout can follow the documented setup; services start using the documented local workflow; lint, type checks and baseline tests pass; no secrets are required from source control.

## Phase 2 — Database implementation

**Status: Not started.**

- **Objective:** Turn the reviewed logical data model into safe, versioned MySQL schema changes.
- **Main implementation areas:** Resolve schema review gates; SQLAlchemy 2.x mappings; Alembic configuration and initial migrations; constraints, indexes and synthetic development fixtures.
- **Expected deliverables:** Approved schema decisions; reversible initial migration where practical; database setup and migration instructions; tests for constraints and migration behavior.
- **Verification and completion criteria:** Migrations apply to a clean MySQL 8.4 database and upgrade path; key ownership, currency and financial constraints are tested; fixtures contain only synthetic data.

## Phase 3 — Backend architecture

**Status: Not started.**

- **Objective:** Establish a modular FastAPI application with clear API, domain, persistence and security boundaries.
- **Main implementation areas:** Application configuration; API versioning and error handling; Pydantic schemas; SQLAlchemy session lifecycle; authentication and authorization foundations; domain module boundaries.
- **Expected deliverables:** Typed modular backend; documented dependency/configuration handling; consistent API errors; authorization test foundations.
- **Verification and completion criteria:** API starts with validated configuration; route and service boundaries follow architecture guidance; protected-resource access checks and error contracts have tests.

## Phase 4 — Financial transaction engine

**Status: Not started.**

- **Objective:** Implement reliable ledger events and account balance effects while preserving financial invariants.
- **Main implementation areas:** Decimal money types; income, expense, opening balance and adjustment events; account entries; transfers; refunds and auditable corrections; allocation validation; idempotency and concurrency controls.
- **Expected deliverables:** Financial domain services and API contracts; migrations as needed; transaction workflows; audit-safe correction behavior.
- **Verification and completion criteria:** Unit, integration and API tests cover precision, balances, transfers, refunds, allocation limits, retries, concurrency and authorization; transactions and allocations are never double-counted.

## Phase 5 — Financial planning engine

**Status: Not started.**

- **Objective:** Model plans and expected future obligations separately from actual money held and posted transactions.
- **Main implementation areas:** Budgets and periods; commitments and payment links; income forecasts; goals and reservations; Safe-to-Spend inputs and transparent calculations.
- **Expected deliverables:** Planning domain services and APIs; calculation explanations and data completeness behavior; associated tests and documentation.
- **Verification and completion criteria:** Tests show forecasts do not alter received balances, bills link to actual events, goals are not misclassified as expenses, and calculations match approved documented scenarios.

## Phase 6 — API contracts and integration

**Status: Not started.**

- **Objective:** Align versioned REST contracts with domain behavior and provide a stable frontend integration surface.
- **Main implementation areas:** OpenAPI schemas; pagination and filtering; session/CSRF behavior; error envelopes; idempotency; contract and integration testing.
- **Expected deliverables:** Reviewed API contract; generated API documentation; typed integration guidance; tested endpoint behavior.
- **Verification and completion criteria:** Contract tests cover success, validation, conflicts, idempotency and cross-user/household authorization; monetary API values remain decimal strings.

## Phase 7 — Frontend foundation and design system

**Status: Not started.**

- **Objective:** Build an accessible, responsive client foundation consistent with the supplied design and API contracts.
- **Main implementation areas:** Next.js App Router and strict TypeScript; Tailwind CSS and shadcn/ui; Motion with reduced-motion support; typed API client; shared layouts, forms and financial display primitives.
- **Expected deliverables:** Navigable application shell; reusable accessible components; loading, empty, error and success patterns; frontend test and quality tooling.
- **Verification and completion criteria:** Lint, type checks and Vitest pass; keyboard, responsive and reduced-motion checks cover shared patterns; authoritative monetary calculations remain server-owned or decimal-safe.

## Phase 8 — Onboarding and user identity

**Status: Not started.**

- **Objective:** Let users securely establish an identity and reach initial personal setup without requiring unnecessary financial data.
- **Main implementation areas:** Registration, login, logout, session management and recovery; profile/preferences; onboarding steps; personal space and optional household choice.
- **Expected deliverables:** End-to-end identity flows; validated onboarding state; session and privacy controls.
- **Verification and completion criteria:** Authentication, session revocation, CSRF, rate limits and authorization tests pass; onboarding supports skip/return paths and does not expose another user's records.

## Phase 9 — Core application features

**Status: Not started.**

- **Objective:** Deliver the primary account, transaction, budget, commitment, goal and household workflows agreed for MVP.
- **Main implementation areas:** Account management; transaction entry/listing/search; allocations; budgets; bills; goals; household membership and privacy projections.
- **Expected deliverables:** Integrated user flows and accessible screens backed by domain APIs; synthetic demo fixtures; updated user and API documentation.
- **Verification and completion criteria:** Critical end-to-end journeys pass; posted activity reconciles; transfers and allocations are counted correctly; household privacy and transaction idempotency are tested.

## Phase 10 — Insights and analytics

**Status: Not started.**

- **Objective:** Explain verified financial history and plans without implying unsupported certainty.
- **Main implementation areas:** Spending and cash-flow summaries; budget progress; trends; Safe-to-Spend explanation; accessible chart alternatives and completeness indicators.
- **Expected deliverables:** Server-derived insight endpoints and user-facing summaries; calculation provenance and accessible data alternatives.
- **Verification and completion criteria:** Calculations reconcile to source records across currencies and periods; insufficient/stale data is surfaced; charts provide exact accessible values; no invented insight is presented as fact.

## Phase 11 — PWA/mobile readiness

**Status: Not started.**

- **Objective:** Prepare responsive web workflows for mobile use and assess installability/offline needs without compromising data integrity.
- **Main implementation areas:** Mobile interaction and performance; PWA capabilities where approved; client-generated IDs and idempotency; explicit offline conflict and sync design before implementation.
- **Expected deliverables:** Mobile usability review; approved PWA scope; documented synchronization policy if offline work is authorized.
- **Verification and completion criteria:** Core tasks work at mobile sizes and with touch/keyboard; reduced motion and accessibility remain supported; offline writes, if implemented, are retry-safe and tested for conflicts.

## Phase 12 — Security, privacy and reliability

**Status: Not started.**

- **Objective:** Strengthen protections and operational recovery before real-user use.
- **Main implementation areas:** Threat model review; dependency and secret checks; authorization and privacy testing; data export/deletion policy; logging redaction; backup/restore and reliability checks.
- **Expected deliverables:** Reviewed security controls; incident and recovery procedures; privacy-reviewed data lifecycle; verified backup/restore process.
- **Verification and completion criteria:** Security and tenant-isolation suites pass; no sensitive financial payloads enter logs/telemetry; restore is rehearsed; legal and privacy obligations are reviewed for intended launch markets.

## Phase 13 — Production and release

**Status: Not started.**

- **Objective:** Prepare and release a reviewed production deployment with controlled operational procedures.
- **Main implementation areas:** Hosting/region decision; production configuration and secrets; TLS, managed MySQL, backups, monitoring, deployment/rollback, release gates and support readiness.
- **Expected deliverables:** Approved deployment architecture; release checklist; runbooks; staged and production release artifacts as separately authorized.
- **Verification and completion criteria:** Staging checks and release gates pass; migrations and rollback/recovery are reviewed; production deployment receives explicit project owner approval.

## Phase 14 — Future expansion

**Status: Not started.**

- **Objective:** Evaluate additional capabilities only after core financial correctness, privacy and reliability are established.
- **Main implementation areas:** Potential FX reporting, offline sync, native clients, bank imports, AI explanations and other roadmap ideas, each subject to product, security and architecture review.
- **Expected deliverables:** Individually approved proposals and ADRs; bounded follow-on milestones for accepted work.
- **Verification and completion criteria:** Each expansion has explicit approval, resolved policy decisions, privacy/security review and tests; deferred capabilities remain out of scope until separately authorized.

## Documentation references

- Product scope and user journeys: `docs/product/`.
- System design, API, data model and financial rules: `docs/architecture/`.
- Coding, testing, security, deployment and collaboration: `docs/engineering/`.
- Visual, accessibility and motion requirements: `docs/design/`.
- Accepted and proposed decisions: `docs/decisions/ADR/`.
