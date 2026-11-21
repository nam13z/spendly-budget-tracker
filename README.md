# Spendly — Product & Engineering Documentation

**Documentation version:** 1.0  
**Status:** Foundation pack / implementation-ready after the decisions marked `OPEN` are confirmed  
**Initial product:** Responsive web application  
**Frontend:** Next.js + TypeScript  
**Backend:** Python + FastAPI  
**Database:** MySQL 8.4 LTS  
**ORM / migrations:** SQLAlchemy 2.x / Alembic

## What Spendly is

Spendly is a financial decision-support product for individuals and households. It combines manual financial tracking, account management, flexible budgeting, upcoming commitments, savings goals, shared spaces and understandable financial insights.

Its central promise is not “track every penny”. It is:

> Help people understand their current financial position, know what money is committed, decide what is safe to spend, and recover calmly when reality changes.

## Documentation map

| Folder | Purpose |
|---|---|
| `docs/product/` | Product vision, requirements, user journeys and release priorities |
| `docs/architecture/` | System design, data model, API contract and financial rules |
| `docs/design/` | Visual system, motion and accessibility requirements |
| `docs/engineering/` | Coding, testing, security, deployment and contribution practices |
| `docs/decisions/ADR/` | Records of important architecture decisions |
| `AGENTS.md` | Mandatory instructions for AI coding agents |

## Read in this order

1. `AGENTS.md`
2. `docs/product/PRODUCT_BLUEPRINT.md`
3. `docs/product/PRD.md`
4. `docs/architecture/FINANCIAL_LOGIC.md`
5. `docs/architecture/DATABASE_SCHEMA.md`
6. `docs/architecture/SYSTEM_ARCHITECTURE.md`
7. `docs/architecture/API_SPECIFICATION.md`
8. Engineering and design documents
9. `docs/product/FEATURE_ROADMAP.md`

## Important status convention

- **MUST**: required for the stated release or system correctness.
- **SHOULD**: strongly recommended; deviation requires a reason.
- **MAY**: optional or future capability.
- **OPEN**: requires a deliberate product/technical decision.
- **MVP**: required for the first useful public-quality release.
- **Later**: intentionally not part of the MVP.

Do not interpret every idea in this pack as an MVP feature. Build the smallest complete, trustworthy financial product first.

## Product invariants

1. A real-world transaction is recorded once.
2. Allocations describe who/which space a transaction benefits; they are not new transactions.
3. Transfers between a user's own accounts are not income or expense.
4. Expected income is not received money.
5. A budget is a plan/limit, not an account balance.
6. Safe-to-Spend is a derived estimate with a visible explanation, not a bank balance or guarantee.
7. Original transaction currency and amount are immutable historical facts unless the user explicitly edits the transaction.
8. Financial arithmetic uses decimal-safe representations, never binary floating point.
9. Every household and personal record is protected by server-side authorization.
10. AI may explain verified calculations; it must not invent or independently calculate financial facts.

## Current open decisions

- Open-source license: choose before public repository release.
- Production hosting provider and region: choose after privacy, cost and data-residency review.
- Final visual palette, typography and brand assets: finalize after user-provided visual references.
- FX rate source and conversion policy: finalize before multi-currency reporting is enabled.
- Exact Safe-to-Spend policy: begin with the documented transparent baseline and test with users.
- Offline synchronization: design IDs and idempotency now; implement after online transaction flows are stable.
- Legal/privacy obligations: review for launch markets before accepting real users.

## Development rule

Never ask an AI coding agent to build the whole application in one prompt. Give it one bounded milestone, require a plan, inspect the diff, run tests, and only then merge.

## Development setup

The supported backend and database workflow is [GitHub Codespaces](docs/engineering/CODESPACES.md). The Dev Container runs Python, Node.js and the application services in one Codespace, with private forwarded application ports. Windows local setup is retained as a legacy reference in [`docs/engineering/LOCAL_DEVELOPMENT_WINDOWS.md`](docs/engineering/LOCAL_DEVELOPMENT_WINDOWS.md). Deployment and production operations remain covered separately by [`docs/engineering/DEPLOYMENT.md`](docs/engineering/DEPLOYMENT.md).

The root [`PLANS.md`](PLANS.md) tracks the project implementation milestones and approval gates.
