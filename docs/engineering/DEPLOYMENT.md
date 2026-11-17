# Deployment & Operations

## 1. Local development

Use Docker Compose for MySQL and optionally backend services. Provide:
- `.env.example` with placeholder values only;
- migrations command;
- synthetic seed command;
- health checks;
- one documented startup command.

## 2. Environments

### Development
Local data only; synthetic accounts.

### Test
Ephemeral or isolated DB; no production secrets.

### Staging
Production-like topology; synthetic or anonymized data only.

### Production
Managed hosting, managed MySQL, TLS, backups, monitoring, restricted access and documented rollback.

## 3. Configuration

Use environment variables or a secret manager. Validate required configuration at startup. Never commit `.env`.

## 4. Database operations

- Run migrations as a controlled deployment step.
- Back up before risky migrations.
- Test migration on staging.
- Prefer backward-compatible expand/migrate/contract changes.
- Monitor DB connections, storage and slow queries.
- Test restore periodically.

## 5. CI/CD

On every pull request:
- frontend lint/typecheck/tests;
- backend lint/typecheck/tests;
- migration validation;
- dependency/security checks;
- build verification.

Deploy staging automatically after approved merge if configured. Production deploy requires explicit approval until operational maturity is established.

## 6. Observability

Collect:
- request latency and error rates;
- service health;
- database health;
- background job failures;
- deployment version.

Do not collect raw transaction descriptions, amounts or account details in telemetry.

## 7. Incident response

1. Identify and contain.
2. Protect users and preserve evidence.
3. Assess affected data and systems.
4. Restore service safely.
5. Notify affected parties/regulators as required by applicable law.
6. Document root cause and prevention.

## 8. Provider selection

OPEN: choose hosting and region after comparing price, reliability, managed MySQL support, backup options, data residency, security controls and ease of operations. Do not choose based solely on a free tier.
