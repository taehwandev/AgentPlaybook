---
keyflow_id: sys_web_security
status: review
type: human-reviewed-needed
---

# Web Security

Use when web work touches auth, session state, browser storage, cookies, tokens,
forms, uploads, embeds, third-party scripts, client-visible config, redirects,
or protected UI actions.

Also use `common/secure-development-baseline.md` and
`common/security-privacy-review.md` for shared secret handling, authorization,
logging, diagnostics, and open-source repository safety rules.

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

## Check

- What server boundary enforces this permission or entitlement?
- Can a denied user trigger the command through the API, route, keyboard, or
  browser dev tools?
- Which secrets or sensitive fields can appear in the bundle, storage, URL,
  logs, analytics, crash reports, or source maps?
- Are redirects, embeds, uploads, rich text, and third-party scripts constrained?
- Does logout, org switch, membership revoke, or plan downgrade clear or refresh
  browser-held state?

## Tests

Cover unauthorized, forbidden, cross-tenant, stale-session, revoked-permission,
malformed redirect, unsafe rich text, upload rejection, and client storage
cleanup paths when applicable. For UI work, verify denied users cannot trigger
the protected command, not only that the button is hidden.
