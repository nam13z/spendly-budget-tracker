# AGENTS.md — Mandatory instructions for coding agents

You are contributing to Spendly, a financial decision-support application. Treat money correctness, privacy and user trust as higher priorities than speed or visual novelty.

## 1. Before changing code

1. Read this file and the relevant documentation under `docs/`.
2. Inspect the existing repository and current implementation. Do not assume the project is empty.
3. Identify the exact feature, acceptance criteria, affected modules, data changes and tests.
4. Write a short implementation plan before editing.
5. If requirements conflict or are ambiguous in a way that affects financial correctness, security, schema or API compatibility, stop and ask. Do not silently invent a policy.

## 2. Non-negotiable financial rules

- Never use `float` / JavaScript `number` for persisted or authoritative monetary arithmetic.
- Backend money values must use Python `Decimal`; database values must use suitable `DECIMAL(p,s)` columns.
- Frontend money must be represented as decimal strings or a safe decimal library type. Convert to formatted strings only at display boundaries.
- Never sum transaction amount and its allocations as separate spending.
- Transfers between owned accounts do not count as income or expense.
- A refund must be represented explicitly and linked to the original transaction when possible.
- Expected income must not be treated as received balance.
- Do not silently convert historical transaction values when exchange rates change.
- Use database transactions for operations that update multiple financial records.
- Enforce allocation sum rules and account ownership on the server.
- Use idempotency keys for transaction-creation operations where retries could duplicate money records.

## 3. Security and privacy

- Assume all client input is untrusted.
- Enforce authentication and authorization on the backend for every protected resource.
- Never trust a client-supplied `user_id`, household membership, role or ownership claim.
- Scope queries to the authenticated principal and authorized household/space.
- Never expose secrets, tokens, passwords, financial records or personally identifying data in logs.
- Do not add telemetry that captures transaction descriptions, amounts or account details unless explicitly approved and privacy-reviewed.
- Use parameterized queries / ORM expressions.
- Do not disable security checks to make tests pass.
- Never commit `.env`, credentials, real user data, production dumps or private keys.

## 4. Engineering standards

- Keep frontend, backend and domain/financial logic separated.
- Prefer small modules with clear responsibilities.
- Avoid giant components, giant routers and circular imports.
- Add type annotations to Python public functions and TypeScript strict typing.
- Validate at API boundaries with Pydantic and frontend schemas where appropriate.
- Use Alembic migrations for every schema change. Never rely on `create_all()` as production migration strategy.
- Add tests for business rules before or alongside implementation.
- Update API and architecture docs when behavior changes.
- Preserve backward compatibility unless the task explicitly authorizes a breaking change.
- Avoid unnecessary dependencies; explain why each new dependency is needed.

## 5. Required workflow for every task

1. Restate the requested outcome.
2. List assumptions and relevant docs.
3. Inspect relevant code.
4. Propose implementation steps and risks.
5. Implement only the requested scope.
6. Add/update tests.
7. Run relevant formatting, linting, type checks and tests.
8. Report exact commands and results. Never claim a test passed if it was not run.
9. Summarize changed files, migration/API impact and remaining risks.
10. Do not commit or push unless explicitly asked.

## 6. Definition of done

A task is complete only when:
- Acceptance criteria are met.
- Tests cover normal, boundary and failure cases.
- Authorization is tested where applicable.
- No monetary precision regression exists.
- Migrations are reversible where practical and reviewed.
- Documentation is updated.
- The app runs using documented commands.
- The agent reports actual test output and known limitations.

## 7. UI principles

- Decision-first, calm, refined and clear.
- Avoid shame language, alarmist red, manipulative streaks or pressure.
- Use animation to communicate state changes, not decorate every pixel.
- Respect reduced motion and keyboard access.
- Provide loading, empty, error and success states.
- Never use color alone to communicate financial meaning.
- Do not invent financial insights when data is insufficient.

## 8. What not to build without approval

- Bank integrations or financial institution credential collection.
- AI chatbot or autonomous financial advice.
- Investment recommendations or credit scoring.
- Payment initiation or money movement.
- Social feeds, public leaderboards or competitive spending.
- Automatic deletion/rewriting of financial history.
- New data collection or third-party analytics involving financial records.

## 9. Project governance and approved architecture

- Follow the approved stack and modular monolith architecture in `docs/architecture/` and `docs/engineering/MASTER_AGENT_PROMPT.md`: Next.js + TypeScript, Tailwind CSS, shadcn/ui, Motion, FastAPI, MySQL 8.4, SQLAlchemy 2.x, Alembic and Pydantic. Do not substitute technologies or redesign the architecture without project owner approval.
- Treat the supplied hierarchy as authoritative: product requirements in `docs/product/`, system and financial contracts in `docs/architecture/`, engineering practices in `docs/engineering/`, design requirements in `docs/design/`, and decisions in `docs/decisions/ADR/`. Preserve these documents unless the assigned task explicitly requires a scoped update.
- Work one approved milestone at a time. Inspect existing code and relevant documentation, state a short plan before edits, and stop after the assigned milestone for project owner review and approval before proceeding.
- Follow `docs/engineering/GIT_WORKFLOW.md`. Do not initialize or rewrite Git history, change remote/repository settings, push, or connect external services unless explicitly authorized.
- Do not run destructive database operations, deploy, or make other external changes without explicit project owner approval. Schema changes require reviewed, reversible Alembic migrations where practical.
- Run only the verification relevant to the assigned scope; report exact commands and actual results. Never imply the application is configured or operational unless verified.
