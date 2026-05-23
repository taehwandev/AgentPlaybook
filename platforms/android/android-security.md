---
keyflow_id: sys_android_security
status: draft
type: ai-generated
---

# Android Security

Use when Android work touches credentials, local storage, IPC, deep links, WebView, permissions, exported components, or release builds.

Also use `common/secure-development-baseline.md` for shared secret handling,
authorization, logging, diagnostics, and open-source repository safety rules.

## Rules

- Store secrets with Android Keystore-backed storage or an accepted repo-local secure storage wrapper.
- Do not store access tokens, refresh tokens, private keys, or sensitive user data in plain SharedPreferences, logs, screenshots, or crash payloads.
- Treat `Activity`, `Service`, `Receiver`, and `Provider` export settings as security boundaries.
- Validate deep links and app links before using embedded IDs, tokens, or redirect targets.
- Use explicit intents for sensitive flows and check `PendingIntent` mutability.
- Keep WebView JavaScript bridges narrow, typed, and unavailable to untrusted content.
- Prefer platform photo picker and scoped storage over broad file permissions.
- Keep cleartext traffic disabled unless the repo documents an accepted debug-only exception.

## Check

- Which Android component can receive this intent or data?
- Can another app trigger the action, read the file, or intercept the token?
- Does permission denial have a user-visible and recoverable state?
- Are secrets excluded from logs, analytics, crash reports, notifications, and clipboard?
- Do release builds keep signing keys, API secrets, and debug endpoints out of the client?

## Tests

Cover permission denied, revoked permission, malicious or malformed deep link, process recreation after auth state change, and release-build configuration when applicable.
