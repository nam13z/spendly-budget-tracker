# Coding Standards

## General
- Keep changes small and focused.
- Prefer readable explicit code over clever abstractions.
- Avoid premature microservices and overengineering.
- Use meaningful names and document non-obvious domain rules.
- No secrets or real financial data in source control.

## Python backend
- Python type hints for public functions.
- Pydantic request/response schemas.
- SQLAlchemy 2.x typed mappings.
- Decimal for money.
- Domain services contain business rules; routers stay thin.
- Explicit transaction boundaries.
- Ruff (lint/format) and Pytest.
- Avoid broad exception swallowing.
- Never return ORM entities directly from API.

## TypeScript frontend
- Strict TypeScript; avoid `any`.
- Separate server state from local UI state.
- Use shared typed API client.
- Centralize currency formatting and money parsing.
- No authoritative financial math using JS number.
- Components should have one clear responsibility.
- ESLint + formatter + typecheck.
- Avoid duplicated API/business rules in components.

## Database
- Alembic migration for every schema change.
- Review generated migrations manually.
- Add indexes based on query patterns.
- Use foreign keys and constraints.
- Never use destructive migration without explicit review and backup plan.

## Git
- Feature branches.
- Small commits with imperative messages.
- No direct pushes to protected main.
- PR must include summary, tests, screenshots for UI changes and migration notes.
