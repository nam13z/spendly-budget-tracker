# System Architecture

## 1. Architectural direction

Use a modular monolith initially: one backend application with clear domain modules, one relational database, and a separately deployed frontend. Avoid microservices until scale or team boundaries justify them.

## 2. Logical architecture

```text
Browser / PWA
   |
   | HTTPS + JSON REST API
   v
Next.js + TypeScript frontend
   |
   v
FastAPI application
   |-- Authentication / authorization
   |-- Users / households / spaces
   |-- Accounts / transactions
   |-- Allocations / categories
   |-- Budgets / commitments / goals
   |-- Financial calculation services
   |-- Insights / exports
   |
   v
SQLAlchemy
   |
   v
MySQL 8.4
```

Optional supporting components later:
- background worker for reminders and recurring schedules;
- queue for reliable jobs;
- object storage for receipt attachments;
- email provider for verification and reset;
- monitoring/error reporting with sensitive-data scrubbing.

## 3. Frontend

- Next.js App Router + TypeScript strict mode.
- Tailwind CSS and shadcn/ui as implementation tools, not product identity.
- Motion for purposeful animation.
- TanStack Query or equivalent for server state (choose one).
- React Hook Form + Zod or a consistent alternative for forms.
- Charts should use a maintained library with accessible labels and tabular alternatives.

Frontend responsibilities:
- render UI and local interaction state;
- validate for user experience;
- call API;
- format money using locale/currency rules;
- never decide authoritative balances, permissions or Safe-to-Spend.

## 4. Backend

FastAPI modular structure, e.g.:

```text
backend/
  app/
    api/
      v1/
    schemas/       # Pydantic request/response contracts
    services/      # use-case orchestration and domain rules
    repositories/  # scoped persistence queries
    core/          # config, error contracts, logging, security
    domains/
      identity/
      households/
      spaces/
      accounts/
      transactions/
      budgets/
      commitments/
      goals/
      insights/
    financial/     # Decimal money, ledger rules, calculations
    db/
    workers/
  tests/
```

Use Pydantic for request/response schemas, SQLAlchemy 2.x for persistence, Alembic for migrations and Pytest for tests.

### Backend dependency direction

- API routers parse HTTP requests, apply request/response schemas, call services and translate results to HTTP responses. They do not issue ORM queries or own business rules.
- Services coordinate one use case, enforce domain invariants and own explicit transaction boundaries. They do not depend on FastAPI types.
- Repositories contain scoped SQLAlchemy reads and writes. They do not decide business policy or return HTTP responses.
- `db` owns the engine, request-scoped session dependency, SQLAlchemy base/models and database-specific types. `core` owns validated configuration, cross-cutting errors and privacy-conscious logging.
- Keep dependencies flowing `api -> services -> repositories -> db`; shared `core` support may be used at application composition boundaries. Add modules when a real use case needs them rather than creating speculative abstractions.

The initial backend foundation may establish these package boundaries without adding financial or identity workflows. Operational health endpoints remain outside the versioned product API and may call a read-only database connectivity probe directly.

Application request logs may contain a generated request ID, HTTP method, matched route template, status code and duration. Do not log raw paths, query strings, request/response bodies, credentials, SQL parameters, user identifiers or financial details. Error responses must omit rejected input values, exception text and stack traces.

## 5. Domain boundaries

- Identity owns users and sessions.
- Household owns memberships and invitations.
- Space owns organization/visibility context.
- Account owns held-money records and account currency.
- Transaction owns the real-world event.
- Allocation owns attribution of transaction value.
- Budget owns planned allocations and periods.
- Commitment owns future obligation schedule and payment status.
- Goal owns target and contribution tracking.
- Financial service computes balances and Safe-to-Spend from authoritative records.

## 6. Data flow

1. Request enters API.
2. Authentication resolves principal.
3. Authorization checks resource and scope.
4. Request schema validates shape.
5. Domain service validates business invariants.
6. DB transaction writes consistent records.
7. Response schema returns canonical representation.
8. Frontend refreshes affected queries.

## 7. Authentication recommendation

For browser-first application, prefer secure server-managed sessions using opaque random session identifiers in `HttpOnly`, `Secure`, `SameSite` cookies, with CSRF protection for state-changing requests. Store only a hash of session tokens server-side. Avoid placing long-lived access tokens in localStorage.

If a future native client needs token-based auth, add a carefully designed OAuth2/OIDC-compatible flow rather than weakening browser security. Final implementation must be reviewed against the chosen deployment topology.

## 8. API versioning

Prefix API with `/api/v1`. Use consistent error envelopes and pagination. Breaking changes require a new version or migration plan.

## 9. Background work

Do not introduce a queue until asynchronous work exists. When needed, use durable jobs for email, reminders, recurring bill generation and exports. Job handlers must be idempotent.

## 10. Offline readiness

Even before offline support:
- generate UUIDs for client-created records;
- support idempotency keys;
- store timestamps in UTC and retain user timezone;
- define conflict behavior;
- never assume client clock is authoritative;
- make transaction create operations retry-safe.

Do not promise full offline synchronization in MVP.

## 11. Environments

- Local development: GitHub Codespaces with a Linux Dev Container; Next.js and FastAPI run in the workspace container, while MySQL 8.4 runs on a private Compose network with no published port. See `docs/engineering/CODESPACES.md`.
- Test: isolated database, deterministic tests.
- Staging: production-like configuration, synthetic data.
- Production: managed database, TLS, backups, least privilege, monitoring.

No production financial data in local development fixtures.
