---
keyflow_id: sys_server_security
status: review
type: human-reviewed-needed
---

# Server Security

Use when server work touches auth, permissions, tenant isolation, API input,
database queries, webhooks, jobs, uploads, external calls, rate limits, secrets,
or public endpoints.

Also use `common/skills/secure-development-baseline/SKILL.md` and
`common/skills/security-privacy-review/SKILL.md` for shared secret handling, authorization,
logging, diagnostics, and open-source repository safety rules.
Use `common/skills/runtime-url-configuration/SKILL.md` for environment-specific service
origins, callback URLs, webhook endpoints, CORS origins, redirect hosts, and
asset/CDN hosts.

## Rules

- Enforce authentication, authorization, tenant boundaries, and entitlement
  checks on the server, not in callers or UI only.
- Validate and normalize request bodies, query params, path params, headers,
  files, webhook payloads, and background job payloads before product logic.
- Avoid mass assignment: map accepted fields explicitly instead of trusting
  client-shaped objects.
- Use parameterized queries, safe ORM APIs, and explicit sort/filter allowlists.
- Treat outbound HTTP, image fetches, webhooks, imports, and URL previews as
  SSRF boundaries; restrict protocols, hosts, redirects, and private networks.
- Rate-limit, debounce, or queue expensive, auth, invite, email, billing,
  password, token, and public unauthenticated endpoints.
- Make webhook verification, replay protection, idempotency, and timestamp skew
  explicit.
- Keep service keys, database URLs, signing secrets, and provider credentials in
  secret stores or ignored local config, never in responses, logs, fixtures, or
  generated clients.
- Keep environment-specific runtime URLs in typed server config, deployment
  config, or service discovery. Do not hard-code production/staging API origins,
  callback URLs, webhook endpoints, CORS allowlists, redirect hosts, or asset
  hosts in handlers, clients, jobs, or generated public artifacts.
- Return stable error shapes without revealing whether private resources,
  accounts, invites, tenants, or tokens exist unless the product policy allows
  that disclosure.

## Check

- Which server layer owns the permission and tenant check?
- Can a caller mutate fields that should be server-owned?
- Are SQL, NoSQL, GraphQL, search, sort, filter, and include parameters
  constrained?
- Can an external URL, webhook, job, upload, or import reach internal resources
  or replay side effects?
- Are runtime URLs and credential-bearing URLs separated, validated, and supplied
  by the target environment's config?
- What rate limit, idempotency key, audit log, and correlation id protects this
  endpoint?
- Do logs, errors, metrics, traces, exports, or fixtures contain secrets or
  personal data?

## Tests

Cover unauthenticated, forbidden, cross-tenant, stale-token, malformed input,
mass-assignment attempt, injection-shaped input, SSRF-shaped URL, rate-limit,
webhook signature failure, replay, idempotent retry, and secret/log leak paths
when applicable.
