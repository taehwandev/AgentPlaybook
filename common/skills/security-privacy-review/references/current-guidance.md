---
keyflow_id: sys_security_privacy_review
status: review
type: ai-generated
---

# Security Privacy Review

Use for auth, permissions, secrets, personal data, logs, storage, browser bundles, mobile storage, and external integrations.

For implementation work or open-source-safe setup, also use
`common/secure-development-baseline.md`.
For environment-specific API origins, callback URLs, redirect URIs, webhook
endpoints, CORS origins, deep link hosts, or asset hosts, also use
`common/runtime-url-configuration.md`.

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
- Do not treat every environment-specific app URL as a secret. Password-bearing
  URLs, database URLs, private-token URLs, and signing secrets are credential
  risks; public app origins, callback URLs, CORS origins, asset hosts, public
  telemetry DSNs, and provider-public client config are configuration/review
  concerns unless they carry credentials or expose private infrastructure.
- UI gating is not authorization.
- Store only the data needed for the product purpose.
- Treat logs, analytics, crash reports, exports, and audit rows as data surfaces.
- Use secure platform storage for secrets and credentials.
- Avoid localStorage/UserDefaults/plain files for sensitive data unless the risk is accepted in the repo.
- Treat deep links, IPC, webhooks, URL schemes, browser bundles, mobile intents, and desktop renderer bridges as trust boundaries.
- Require explicit review for exported components, tenant filters, privileged APIs, shell/file access, and release signing changes.
- Treat client-side credentials, signed payloads, deep-link parameters,
  platform identity responses, and embedded-web messages as untrusted until a
  trusted boundary validates issuer, audience, freshness, replay risk, and
  authorization. UI or platform-provider success is not server-side trust.
- For external launches, IPC, custom schemes, callbacks, renderer bridges, and
  other cross-process or cross-app handoffs, prefer explicit targets, narrow
  allowed actions/data, immutable or one-shot capabilities, and caller identity
  checks at sensitive operations.

## Check

- Who can read or mutate this resource?
- What server or platform boundary enforces that?
- What sensitive fields are stored, logged, cached, exported, or synced?
- Are runtime URLs supplied by the platform's config mechanism, and are
  credentials separated from public configuration?
- Does an error reveal whether a private resource exists?
- Are retention, deletion, and revoke flows considered?
- What untrusted input can trigger this code path?
- Which trusted boundary validates signed or provider-returned data, and how is
  stale or replayed data rejected?
- What happens when permission, membership, entitlement, or token state changes while the flow is active?

## Tests

Test denied access, cross-tenant access, stale session, revoked membership, malformed untrusted input, and secret leak surfaces when applicable.
