---
keyflow_id: sys_android_security
status: review
type: ai-generated
---

# Android Security

Use when Android work touches credentials, local storage, IPC, deep links, WebView, permissions, exported components, or release builds.

Also use `common/secure-development-baseline.md` for shared secret handling,
authorization, logging, diagnostics, and open-source repository safety rules.
Use `common/runtime-url-configuration.md` for environment-specific API origins,
deep link hosts, app link hosts, redirect/callback URLs, asset hosts, and
release-channel config.

## Rules

- Store secrets with Android Keystore-backed storage or an accepted repo-local secure storage wrapper.
- Do not store access tokens, refresh tokens, private keys, or sensitive user data in plain SharedPreferences, logs, screenshots, or crash payloads.
- Keep local developer keys in ignored files such as `local.properties` or the
  repo-approved local config path; keep CI/release keys in the CI secret store.
- Treat `BuildConfig`, resources, manifest placeholders, assets, and generated
  config files as client-visible. They can hold restricted client keys, not
  server-only secrets.
- Put environment-specific API origins, callback URLs, app link hosts, and asset
  hosts in product flavors, manifest placeholders, generated resources, or the
  repo-approved config path instead of source literals.
- Restrict Android client keys by package name, signing certificate fingerprint,
  quota, API scope, or provider-specific controls when available.
- Treat `Activity`, `Service`, `Receiver`, and `Provider` export settings as security boundaries.
- Validate deep links and app links before using embedded IDs, tokens, or redirect targets.
- Use explicit intents for sensitive flows and check `PendingIntent` mutability.
  Prefer immutable `PendingIntent` by default; require an explicit target and a
  documented reason when mutability is needed.
- Treat nested intents, `onNewIntent`, app links, custom schemes, and
  externally supplied extras as untrusted input. Sanitize or whitelist the
  action, component, data URI, categories, MIME type, flags, and extras before
  launching or trusting them.
- Protect exported services, receivers, and providers with the narrowest
  manifest permissions, caller validation, signature checks, or explicit
  non-exported configuration that the behavior allows.
- Keep `ContentProvider` projections, selections, sort orders, and URI grants
  constrained; do not pass caller-controlled SQL fragments or broad file URI
  grants through unchecked.
- Keep WebView JavaScript bridges narrow, typed, and unavailable to untrusted content.
- For reusable WebView surfaces, define the allowlisted origin policy, JavaScript
  enablement, mixed-content policy, file/content access policy, external-browser
  fallback, and bridge availability before sharing the component across Activity
  and Compose wrappers.
- Do not let arbitrary server content enable a JavaScript bridge. Bind bridges
  only for trusted origins and keep bridge methods typed, minimal, and free of
  secrets, tokens, raw files, and direct navigation execution.
- Prefer platform photo picker and scoped storage over broad file permissions.
- Keep cleartext traffic disabled unless the repo documents an accepted debug-only exception.

## Check

- Which Android component can receive this intent or data?
- Can another app trigger the action, read the file, or intercept the token?
- Does permission denial have a user-visible and recoverable state?
- Are secrets excluded from logs, analytics, crash reports, notifications, and clipboard?
- Do release builds keep signing keys, API secrets, and debug endpoints out of the client?
- Do release builds use the intended API origin, callback URL, app link host,
  asset host, and provider app registration for that environment?

## Tests

Cover permission denied, revoked permission, malicious or malformed deep link, process recreation after auth state change, and release-build configuration when applicable.
