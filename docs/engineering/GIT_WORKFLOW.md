# Git & Collaboration Workflow

## Branches
- `main`: stable, protected.
- `develop`: integration branch if the project uses a two-branch workflow.
- `feature/<short-name>`: feature work.
- `fix/<short-name>`: bug fixes.
- `docs/<short-name>`: documentation.

For a solo project, a simpler `main` + short-lived feature branches is also acceptable. Pick one model and document it.

## Commit messages
Use clear imperative messages, e.g.:
- `Add transaction allocation validation`
- `Fix transfer balance calculation`
- `Document Safe-to-Spend assumptions`

## Pull request checklist
- [ ] Scope matches issue/task.
- [ ] Tests added/updated and actually run.
- [ ] Lint/type checks pass.
- [ ] Financial invariants preserved.
- [ ] Authorization reviewed.
- [ ] Migration included and inspected.
- [ ] API docs updated.
- [ ] UI screenshots included where useful.
- [ ] No secrets or real user data.
- [ ] Known limitations stated.

## AI agent rule
AI-generated code is a proposal, not verified truth. Inspect the diff and run tests locally before merging.
