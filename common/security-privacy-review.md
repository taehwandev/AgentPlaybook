---
keyflow_id: sys_security_privacy_review
status: review
type: ai-generated
---

# Security Privacy Review

Use for auth, permissions, secrets, personal data, logs, storage, browser bundles, mobile storage, and external integrations.

For implementation work or open-source-safe setup, also use
`common/secure-development-baseline.md`.

For platform-specific surfaces, also consult the matching security or review document:

```text
Android: platforms/android/android-security.md
iOS: platforms/ios/ios-security.md
Application/Desktop: platforms/application/application-security.md
Server: platforms/server/server-security.md
Web: platforms/web/web-security.md
```

## Priority

1. Secret exposure
2. Broken authorization or tenant isolation
3. Personal data over-collection or leakage
4. Unsafe storage or transport
5. Excessive logging or observability payloads

## Rules

- Follow `common/secure-development-baseline.md` for secret handling,
  authorization boundaries, local config, client app keys, logs, diagnostics, and
  open-source repository safety.
- Do not put service-role keys, API secrets, tokens, or private credentials in client bundles.
- UI gating is not authorization.
- Store only the data needed for the product purpose.
- Treat logs, analytics, crash reports, exports, and audit rows as data surfaces.
- Use secure platform storage for secrets and credentials.
- Avoid localStorage/UserDefaults/plain files for sensitive data unless the risk is accepted in the repo.
- Treat deep links, IPC, webhooks, URL schemes, browser bundles, mobile intents, and desktop renderer bridges as trust boundaries.
- Require explicit review for exported components, tenant filters, privileged APIs, shell/file access, and release signing changes.

## Check

- Who can read or mutate this resource?
- What server or platform boundary enforces that?
- What sensitive fields are stored, logged, cached, exported, or synced?
- Does an error reveal whether a private resource exists?
- Are retention, deletion, and revoke flows considered?
- What untrusted input can trigger this code path?
- What happens when permission, membership, entitlement, or token state changes while the flow is active?

## Tests

Test denied access, cross-tenant access, stale session, revoked membership, malformed untrusted input, and secret leak surfaces when applicable.
