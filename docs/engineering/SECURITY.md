# Security & Privacy Baseline

This document is an engineering baseline, not a legal compliance certification. Obtain qualified review before public launch.

## 1. Threat model

Assets:
- identity credentials and sessions;
- account balances and transaction history;
- household membership and private/shared records;
- invitation tokens;
- exports and backups;
- API secrets and database credentials.

Threats:
- account takeover;
- insecure direct object reference (IDOR);
- cross-household data leakage;
- session theft/CSRF;
- injection and mass assignment;
- brute force and invitation abuse;
- exposed backups/logs;
- malicious or compromised dependencies;
- accidental deletion or corruption.

## 2. Authentication

- Secure password hashing (Argon2id preferred, parameterized and reviewed).
- Email verification and safe password reset.
- Rate-limit authentication endpoints.
- Secure HttpOnly, Secure, SameSite cookies.
- Rotate session identifiers after login/privilege changes.
- Store session token hashes, not raw tokens.
- Revoke sessions on logout/password reset as policy dictates.
- Optional PIN is an app lock, not a replacement for account authentication.

## 3. Authorization

- Deny by default.
- Check ownership/membership on every resource operation.
- Never rely on frontend hiding.
- Use explicit policies for household, personal and custom spaces.
- Test cross-user and cross-household access.
- Avoid exposing sequential IDs.

## 4. Application security

- Validate all input.
- Parameterized database access.
- CSRF defense for cookie sessions.
- CORS allowlist.
- Content Security Policy.
- Secure headers.
- Rate limiting.
- Dependency scanning and updates.
- File upload restrictions if attachments are added.
- Avoid unsafe HTML rendering.

## 5. Data protection

- TLS in transit.
- Encryption at rest through managed infrastructure where available.
- Encrypted, access-controlled backups.
- Separate production credentials.
- Least-privilege DB accounts.
- Sensitive-field redaction in logs.
- Data minimization.
- No transaction data sent to third-party AI/analytics without explicit privacy review and user disclosure.

## 6. Household invitations

- Generate cryptographically secure random tokens.
- Store only token hashes.
- Set expiry and usage limits.
- Support revocation.
- Do not include private data in QR payload.
- Require authenticated acceptance and preview household/role.

## 7. Export and deletion

- Verify requester identity.
- Export only data they are entitled to access.
- Use short-lived download links if hosted.
- Define retention, backup expiry and legal holds.
- Explain deletion consequences.
- Ensure deletion does not leave accessible orphaned private data.
- Document treatment of shared records where multiple members have legitimate interests.

## 8. Operational controls

- Monitor suspicious authentication and authorization failures without logging financial payloads.
- Maintain incident response contact/process.
- Test backup restoration.
- Keep dependencies patched.
- Restrict production access.
- Review access periodically.

## 9. Launch checklist

- Threat model reviewed.
- Security headers and TLS verified.
- Session and CSRF tests pass.
- IDOR tests pass.
- Secrets scan clean.
- Dependency audit reviewed.
- Backup restore proven.
- Privacy policy and terms reviewed by qualified counsel for target markets.
