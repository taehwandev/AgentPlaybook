---
keyflow_id: sys_flutter_security
status: review
type: human-reviewed-needed
---

# Flutter Security

Use when Flutter work touches credentials, secure storage, platform channels,
plugins, WebViews, deep links, local files, clipboard, notifications, network
clients, logs, analytics, crash reports, release builds, signing, or
open-source-safe setup.

Also use `common/secure-development-baseline.md` and
`common/security-privacy-review.md`.
Use `common/runtime-url-configuration.md` for environment-specific API origins,
deep link hosts, redirect/callback URLs, WebView origins, asset hosts, and
release-channel config.

## Rules

- Treat MethodChannel, EventChannel, plugins, WebViews, deep links, files,
  clipboard, push payloads, browser messages, and native callbacks as untrusted
  input.
- Do not store secrets in Dart constants, bundled assets, test fixtures,
  generated code, screenshots, or public sample configuration.
- Keep tokens, private URLs, local paths, native errors, and credential metadata
  out of user-visible errors, telemetry, logs, crash reports, and analytics.
- Wrap secure storage, biometrics, keychain/keystore, permissions, and platform
  identity APIs behind narrow services.
- Do not expose broad filesystem, shell, native, or credential operations
  through channel methods.
- Validate deep links, redirect URLs, WebView navigation, file picks, and share
  inputs against repo-local allowlists and product rules.
- Put environment-specific API origins, redirect/callback URLs, deep link hosts,
  WebView origins, and asset hosts in flavors, `--dart-define`, generated
  config, or the repo-approved config path instead of Dart literals.
- Keep release signing, entitlements, app identifiers, store settings, and
  platform-specific secrets in repo-local docs and ignored configuration.

## Review Questions

- Which target can access the secret, file, permission, or privileged plugin?
- Can compromised UI input, a link, a file, a WebView, or a plugin callback
  trigger a broader native operation?
- Are logs and crash reports safe for open-source development and production
  support?
- Does the selected flavor or build channel use the intended API origin,
  callback URL, deep link host, WebView origin, and asset host?
- Does every denied permission, missing plugin, unsupported target, and secure
  storage failure have a user-safe state?

## Verification

- Run the relevant analyzer/test/build check and a focused platform smoke when
  privileged behavior changed.
- Inspect the diff for secrets, local config, broad channel methods, unsafe
  logs, WebView/deep-link exposure, and release setup drift.
