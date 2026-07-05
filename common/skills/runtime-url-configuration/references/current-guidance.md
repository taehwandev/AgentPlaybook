---
keyflow_id: sys_runtime_url_configuration
status: review
type: human-reviewed-needed
---

# Runtime URL Configuration

Use when implementing or reviewing app, server, mobile, desktop, webhook, auth,
or asset code that references URLs whose value changes by environment.

This is a portability and configuration concern, not a blocking secret scan by
itself. Password-bearing URLs, database connection strings, private tokens,
secret keys, and signing material are credential or security risks and must
follow `secure-development-baseline.md`. Environment-specific app URLs without
credentials should be reviewed as implementation architecture and release
configuration.

Repo-local instructions, platform deployment docs, and provider-specific setup
win when they give a more specific mechanism.

## Review Targets

Treat these as runtime URL configuration surfaces when they vary between local,
development, staging, preview, production, tenant, region, or distribution
channels:

- API origin, API base URL, RPC endpoint, GraphQL endpoint, or service origin
- frontend, backend, preview, staging, production, or development domains
- `redirect_uri`, callback URL, OAuth callback, auth redirect, deep link host,
  app link host, or Universal Link domain
- webhook endpoint, webhook callback, outbound integration endpoint, or relay URL
- asset host, media origin, object storage origin, CDN origin, or image proxy
  host when the value changes by environment
- CORS allowed origin, frame ancestor, allowed redirect host, or trusted return
  URL allowlist
- URLs passed directly to `fetch`, `axios`, `XMLHttpRequest`, `WebSocket`,
  `EventSource`, HTTP clients, SDK constructors, or generated API clients
- server or client config names that mean API URL, base URL, origin, host,
  callback, redirect, webhook, app link, asset host, or CDN origin, such as
  `API_URL`, `BASE_URL`, `ORIGIN`, `HOST`, `CALLBACK`, `REDIRECT`, or `WEBHOOK`

## Lower Priority Or Out Of Scope

Do not treat every URL-shaped string as runtime app configuration. These are
usually documentation, public metadata, or provider-public identifiers unless a
repo-local rule says otherwise:

- documentation links, source links, package homepages, GitHub repository URLs,
  changelog links, README anchors, or marketing page links
- Open Graph image URLs, public share-preview URLs, canonical URLs, sitemap URLs,
  and public discovery metadata governed by `public-discovery.md`
- Google Fonts URLs, public CDN library URLs, documentation URLs, public demo
  links, and static marketing anchors
- public telemetry ingest identifiers such as a Sentry DSN, unless the provider
  or repo treats the specific value as restricted
- provider-public client config such as Firebase public config, publishable keys,
  public project ids, app ids, or measurement ids when the provider expects
  client exposure

Public identifiers can still need environment separation, provider restrictions,
quota controls, or release review. They are not secrets merely because they look
like URLs or keys.

## Credential Distinction

- A password-bearing URL or database connection string is a credential and a
  security risk.
- A URL containing a private token, one-time secret, signed credential, session
  value, invite token, reset token, or service credential is a credential risk.
- A URL with only a username, public project id, public app id, public tenant
  slug, or public identifier is not a secret by default.
- A public telemetry DSN is normally a client-visible ingest identifier, not a
  secret, but it still belongs in the correct environment's config.
- Environment-specific app URLs without credentials are portability/configuration
  issues. Fix them by using the platform's normal config path, not by treating
  them as leaked secrets.

## Implementation Rules

- Do not hard-code production, staging, preview, local, tenant, region, callback,
  redirect, webhook, CORS, or asset-host URLs directly in source when the value
  changes by environment.
- Use the platform's normal configuration mechanism:
  environment variables, deployment platform config, framework runtime config,
  Android product flavors and manifest placeholders, iOS build settings and
  `.xcconfig` or Info.plist values, Flutter `--dart-define` or flavor config,
  server config modules, container/deployment config, or repo-approved config
  files.
- Keep server-only URL config on the server when it controls trusted callbacks,
  webhooks, CORS allowlists, private API origins, internal service hosts, or
  signed asset generation.
- Treat client-visible config as public. Client config may contain public origins
  or restricted publishable identifiers, but it must not contain server-only
  secrets, private internal hosts, admin endpoints, or enforcement facts.
- Centralize runtime URL assembly behind a small config module, provider, or
  adapter instead of scattering literals across screens, components, handlers,
  tests, and generated clients.
- Validate configured URLs at startup, app launch, build-time config generation,
  or adapter construction where the platform supports it. Fail closed for missing
  required production URLs; use explicit local defaults only when the repo
  documents that local mode.
- Keep sample config value-free or placeholder-based. Document variable names,
  purpose, visibility, and where each value is supplied, not private values.
- Keep provider restrictions aligned with config: allowed origins, callback URLs,
  bundle ids, package names, signing fingerprints, associated domains, webhook
  signing, and quota should match the intended environment.

## Platform Notes

- Web: use framework-supported public/server environment separation. Public
  variables such as `NEXT_PUBLIC_*` or equivalent are browser-visible. Keep API
  origins, CORS allowlists, redirect hosts, auth callbacks, and asset hosts in
  framework or deployment config instead of hard-coded `fetch` or SDK literals.
- Server: use typed config loading, deployment secrets/config, service discovery,
  or provider config. Keep database URLs, password-bearing URLs, webhook signing
  secrets, and internal service hosts out of client bundles and generated public
  artifacts.
- Mobile: use flavors, schemes, build settings, generated value resources,
  manifest placeholders, Info.plist values, or repo-approved runtime config.
  Deep link hosts, associated domains, callback URLs, and API origins must match
  the release channel being built.
- Desktop/application: use app config, build channel config, installer/release
  config, or signed update-channel config. Do not let untrusted renderer or
  plugin code choose trusted service origins without validation.

## Review Checklist

- Does the URL vary by environment, tenant, region, release channel, or provider
  app registration?
- Is the value a credential/security risk, a public identifier, or a
  portability/configuration concern?
- Is the value supplied through the repo's documented platform config mechanism?
- Is URL construction centralized enough that changing environment does not
  require editing business logic, UI, tests, generated clients, or multiple
  unrelated files?
- Are CORS origins, redirect/callback URLs, deep link hosts, webhook endpoints,
  asset hosts, and provider app registrations aligned for the target
  environment?
- Are public telemetry DSNs, Firebase config, publishable keys, and public app
  ids treated as public identifiers while still being placed in the correct
  environment config?
- Are real credentials, password-bearing URLs, database connection strings,
  private tokens, signing secrets, and webhook secrets kept in secret storage or
  ignored local config?

## Verification

Use the smallest check that proves the boundary:

- unit test or config validation for URL parsing, required variables, and local
  default behavior
- build or typecheck that proves server-only config does not enter client code
- platform smoke for login redirect, callback handling, deep link/app link,
  API request, WebSocket/EventSource connection, webhook delivery, or asset load
- release/preflight check that provider app registration, allowed origins,
  callback URLs, associated domains, bundle/package identity, and asset hosts
  match the target environment

Report unresolved URL placement as configuration or release risk unless it also
contains a credential or private endpoint exposure.
