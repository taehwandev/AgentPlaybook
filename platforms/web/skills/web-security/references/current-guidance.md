---
keyflow_id: sys_web_security
status: review
type: human-reviewed-needed
---

# Web Security

Use when web work touches auth, session state, browser storage, cookies, tokens,
forms, uploads, embeds, third-party scripts, client-visible config, redirects,
or protected UI actions.

Also use `common/skills/secure-development-baseline/SKILL.md` and
`common/skills/security-privacy-review/SKILL.md` for shared secret handling, authorization,
logging, diagnostics, and open-source repository safety rules.
Use `common/skills/runtime-url-configuration/SKILL.md` for environment-specific API origins,
client/server runtime config, callback URLs, redirect URIs, CORS origins,
WebSocket/EventSource endpoints, and asset hosts.

For server state, API clients, cache, and browser persistence, also use
`web-state-data.md`.

## Rules

- UI gating is not authorization; protected commands must be blocked by the API
  or server boundary.
- Keep access tokens, refresh tokens, private keys, service-role keys, and
  server-only secrets out of browser bundles, source maps, logs, and local
  storage.
- Treat `localStorage`, `sessionStorage`, IndexedDB, caches, URL params,
  clipboard, screenshots, analytics, and crash reports as visible data surfaces.
- Prefer secure, HTTP-only, same-site cookies for session material when the repo
  uses cookie sessions.
- Validate redirect targets, return URLs, OAuth state, invite links, deep links,
  and file names before using them.
- Keep CSP, CORS, frame embedding, mixed content, and trusted third-party script
  changes explicit and reviewed.
- Sanitize or escape untrusted HTML, markdown, rich text, and user-provided URLs
  before rendering.
- Keep upload/download paths scoped by auth, tenant, size, content type, and
  storage location.
- Do not expose demo roles, mock permissions, or billing toggles in production
  routes unless the repo documents an accepted test-only boundary.

## Server-To-Client Boundary

Server components, loaders, server actions, route handlers, and RPC endpoints
are all security boundaries when their output reaches browser code.

- Return explicit allowlisted DTOs. Do not return raw database rows, user
  profile documents, session records, auth claims, service SDK responses, or
  recursive serialized objects.
- Treat encrypted PII, deterministic hashes, internal IDs, private feature
  flags, moderation fields, access graphs, billing internals, and audit fields
  as sensitive even when they are not plain-text secrets.
- Server-side serialization only solves transport compatibility. It does not
  decide which fields are safe to expose.
- Re-check auth, ownership, tenant/workspace, role, membership, visibility,
  quota, and entitlement on every server action and API request.
- Ignore client-supplied authorization facts. Client payloads may identify the
  intended resource, but the server must derive trust from cookies, verified
  tokens, session records, or other server-owned state.
- Minimize response payloads for mutations and live calls. Prefer counts,
  statuses, opaque IDs, or public display models over refreshed raw entities.
- Return typed, redacted errors. Avoid leaking private resource existence,
  internal paths, storage keys, provider errors, stack traces, or cache tags.

## Cookies, Tokens, And CSRF

- Session cookies should be secure, HTTP-only, same-site, scoped by path/domain,
  and rotated or cleared on logout, account deletion, revocation, and privilege
  changes. Development exceptions must be explicit and not leak into production.
- If cookie-authenticated POST/PUT/PATCH/DELETE routes can be reached by a
  browser, apply the framework's CSRF protection or validate origin, method,
  and an anti-CSRF token.
- Signed URLs, share tokens, invite tokens, presence tokens, and preview tokens
  need purpose scoping, expiration, tamper verification, and no-store responses
  unless a public cache model is documented.
- Token-backed endpoints should validate both token integrity and request
  fields. A signed `postId` or tenant ID must match the requested resource.

## CORS, Cache, And Client Config

- CORS wildcards are acceptable only for intentionally public unauthenticated
  resources. Credentialed or user-owned routes need an allowlist.
- Environment-specific API origins, backend/frontend domains, callback URLs,
  redirect hosts, WebSocket/EventSource endpoints, and asset hosts belong in the
  framework or deployment config, not scattered `fetch`, SDK, or client
  component literals.
- Public CDN cache headers must only be used for data that is identical for all
  viewers. Private, follower-only, draft, admin, token-backed, live, or
  personalized data should be private/no-store or keyed by the full access
  dimension.
- `NEXT_PUBLIC_*` or equivalent client-visible config is public. Do not put admin
  identities, private endpoints, secrets, feature bypasses, or enforcement facts
  there.
- Revalidation endpoints must require a secret or trusted server caller, validate
  requested tags/paths, and avoid returning internal errors.

## HTML, Rich Text, And Embeds

- `dangerouslySetInnerHTML`, markdown renderers, Mermaid/SVG output, math output,
  iframe content, embeds, and syntax-highlighting HTML must have a named trust
  source and sanitization or escaping step.
- Structured data scripts should serialize through an escaping helper that
  neutralizes script-breaking characters.
- User-provided URLs need protocol, host, and storage-scope validation before
  link rendering, embed rendering, upload signing, or redirect.

## Check

- What server boundary enforces this permission or entitlement?
- Can a denied user trigger the command through the API, route, keyboard, or
  browser dev tools?
- Does every server-to-client payload use an allowlisted DTO instead of a raw
  serialized record?
- Can client-provided IDs, roles, owner IDs, tenant IDs, prices, quotas, paths,
  cache tags, or visibility values affect authorization?
- Which secrets or sensitive fields can appear in the bundle, storage, URL,
  logs, analytics, crash reports, or source maps?
- Are encrypted values, hashes, internal IDs, audit fields, and feature flags
  excluded from browser-visible payloads unless intentionally public?
- Are redirects, embeds, uploads, rich text, and third-party scripts constrained?
- Are runtime URLs separated into server-only and client-visible config, with
  public config treated as public and credentials kept server-side?
- Do cache headers match the data visibility and viewer dimensions?
- Does logout, org switch, membership revoke, or plan downgrade clear or refresh
  browser-held state?

## Tests

Cover unauthorized, forbidden, cross-tenant, stale-session, revoked-permission,
malformed redirect, unsafe rich text, upload rejection, token tampering,
cache-header, sensitive-field omission, and client storage cleanup paths when
applicable. For UI work, verify denied users cannot trigger the protected
command, not only that the button is hidden.
