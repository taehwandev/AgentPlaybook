---
keyflow_id: sys_ios_security
status: review
type: human-reviewed-needed
---

# iOS Security

Use when iOS work touches credentials, Keychain, local storage, permissions,
Universal Links, URL schemes, app groups, extensions, WebViews, networking,
signing, entitlements, or release builds.

Also use `common/secure-development-baseline.md` for shared secret handling,
authorization, logging, diagnostics, and open-source repository safety rules.
Use `common/runtime-url-configuration.md` for environment-specific API origins,
Universal Link domains, URL scheme callback hosts, redirect/callback URLs,
asset hosts, and release-channel config.

## Rules

- Store credentials, refresh tokens, private keys, and sensitive auth material in
  Keychain or a repo-approved secure storage wrapper.
- Treat UserDefaults, plist files, caches, screenshots, logs, analytics, and
  crash payloads as visible data surfaces.
- Keep server-only secrets out of app bundles, generated config, assets, and
  build settings.
- Put environment-specific API origins, callback URLs, Universal Link domains,
  URL scheme callback hosts, and asset hosts in build settings, `.xcconfig`,
  Info.plist values, schemes, or the repo-approved config path instead of source
  literals.
- Restrict client keys by bundle id, team id, associated domain, API scope,
  quota, or provider-specific controls when available.
- Treat URL schemes, Universal Links, App Clips, widgets, extensions, pasteboard,
  document providers, and share extensions as trust boundaries.
- Validate incoming links, file URLs, callback payloads, and redirect targets
  before using embedded IDs, tokens, or actions.
- Keep WKWebView bridges narrow, typed, and unavailable to untrusted content.
- Keep App Transport Security exceptions explicit and debug-scoped unless the
  repo documents an accepted production reason.
- Ensure permission purpose strings are specific, truthful, and aligned with the
  data actually used.
- Signing, entitlements, provisioning profiles, associated domains, and release
  build configuration need explicit smoke coverage when changed.

## Check

- Which app, extension, URL, file, web content, or external service can trigger
  this action?
- Is sensitive data outside UserDefaults, logs, screenshots, crash reports, and
  broad app group storage?
- Are permission denied, revoked permission, and restricted-device states visible
  and recoverable?
- Do entitlements, associated domains, callback URLs, and bundle ids match the
  intended environment?
- Do API origins, redirect/callback URLs, Universal Link domains, asset hosts,
  and provider app registrations match the release channel being built?
- Does release configuration avoid debug endpoints, broad ATS exceptions, and
  embedded private credentials?

## Do Not

- Do not put credentials, refresh tokens, OAuth client secrets, signing
  material, private API tokens, or service-role keys in app bundles, assets,
  Info.plist files, generated config, or build settings.
- Do not store sensitive user data in UserDefaults, plain plist files, caches,
  screenshots, crash payloads, pasteboard, or broad app group containers unless
  the repo records an accepted risk and protection model.
- Do not accept Universal Links, URL schemes, files, pasteboard values,
  extension payloads, or WebView messages without validating origin, target,
  action, and embedded identifiers.
- Do not keep WKWebView bridges broad, stringly typed, or available to
  third-party/untrusted content.
- Do not ship debug ATS exceptions, debug API origins, entitlement drift, broad
  associated domains, or vague permission purpose strings in release builds.

## Tests

Cover permission denied and revoked states, malformed Universal Links or URL
schemes, stale auth after app restart, Keychain read/write failure when
applicable, WebView bridge misuse when present, and release-build entitlement or
signing configuration when changed.
