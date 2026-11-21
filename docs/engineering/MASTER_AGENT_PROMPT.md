# Spendly — Master Coding Agent Project Context

You are helping build Spendly, a privacy-conscious financial decision-support application.

Before implementation, read `AGENTS.md` and the relevant docs. The product is decision-first, not merely a transaction ledger.

## Stack
- Frontend: Next.js App Router, TypeScript strict mode, Tailwind CSS, reusable accessible components.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic.
- Database: MySQL 8.4 LTS.
- Tests: Pytest backend; Vitest and Playwright frontend.
- Local development: GitHub Codespaces with a Linux Dev Container and MySQL 8.4 on a private Compose network. Windows Smart App Control remains enabled; see `docs/engineering/CODESPACES.md`.

## Build strategy
Use a modular monolith. Implement one milestone at a time. Do not generate the entire app in one pass.

## Non-negotiable domain rules
- One real transaction is stored once.
- Allocations attribute a transaction; they do not create additional spending.
- Transfers between owned accounts are not income or expense.
- Expected income is not received money.
- Budget remaining is not account balance.
- Safe-to-Spend is a transparent estimate, never a guarantee.
- Money uses Decimal / DECIMAL and decimal strings across API boundaries.
- No cross-currency summation without explicit FX conversion.
- Backend authorization is mandatory for every protected record.
- AI cannot calculate or invent financial facts.

## First assignment
Do not implement features yet. Inspect the repository and report:
1. current repository state;
2. missing prerequisites;
3. proposed directory structure;
4. local setup approach;
5. first three implementation milestones;
6. risks and unresolved decisions.

Wait for approval before changing files.
