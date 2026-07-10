---
keyflow_id: sys_kmp_security
status: review
type: human-reviewed-needed
---

# KMP Security

Use when Kotlin Multiplatform work touches credentials, local files, shell or
process execution, network clients, secure storage, platform permissions,
native interop, logging, release builds, signing, or open-source-safe setup.

Also use `common/skills/secure-development-baseline/SKILL.md` and
`common/skills/security-privacy-review/SKILL.md`. For desktop shell, IPC, signing,
notarization, updates, or privileged APIs, also use the application security
card.

## Rules

- Treat each actual implementation and platform adapter as a security boundary.
- Do not store secrets in shared resources, test fixtures, generated source, or
  public sample configuration.
- Keep credentials and tokens out of user-visible errors, telemetry, logs,
  screenshots, crash reports, and serialized run artifacts.
- Validate data crossing platform boundaries: files, URLs, shell output,
  clipboard, native callbacks, permissions, deep links, and interop pointers.
- Keep shell, filesystem, network, clipboard, notification, and secure-storage
  access behind narrow adapters with explicit allowed operations.
- Do not assume one target's permission or sandbox model applies to another.
- Document target-specific release requirements such as signing, entitlements,
  notarization, package identifiers, or store configuration in repo-local docs.

## Auth And Network Security

- Keep API origins, public app ids, and public client keys in the repo's normal
  environment/build configuration path. Do not hard-code production, staging,
  callback, WebSocket, or deep-link hosts in shared source.
- Keep private API keys, OAuth client secrets, signing keys, keystores,
  refresh tokens, service-role keys, and webhook secrets out of source,
  generated config, shared resources, fixtures, screenshots, and logs.
- Bearer-token refresh must skip auth/refresh endpoints to avoid loops, clear
  cached tokens on logout or refresh failure, and map expired session state into
  user-visible reauth flow.
- Restrict client-exposed provider keys where providers support package name,
  bundle id, SHA fingerprint, domain, quota, or environment restrictions.
- Redact `Authorization`, cookies, API keys, refresh tokens, request bodies, and
  private URLs in HTTP logging, debug inspectors, crash reports, and analytics.
- Debug network inspectors and verbose logging must be debug-only or no-op in
  release builds.

## Local Storage And Config Files

- Store refresh tokens and credentials in platform-appropriate secure storage
  when possible. If a repo uses plain settings/DataStore/UserDefaults/files,
  document the accepted risk and clear behavior.
- Define session clear behavior for logout, account switch, token refresh
  failure, permission revoke, app reinstall, and remote account deletion.
- Keep local developer config files, Android service JSON, Apple service plist,
  keystores, provisioning files, and signing passwords ignored unless the repo
  explicitly commits value-free templates.
- Do not place generated build config containing secrets in common source,
  public artifacts, or sample code.

## Review Questions

- Which targets can access the secret, file, permission, or privileged API?
- What is the user-visible failure when a target denies access or lacks the
  capability?
- Can a compromised renderer, plugin, file, clipboard value, callback, or native
  input invoke a broader operation than intended?
- Are debug/test credentials, local paths, signing material, or private prompts
  excluded from the open-source diff?
- Are release variants free of debug inspectors, verbose HTTP logging, broad
  exported components, local endpoints, and unredacted telemetry?

## Verification

- Run the relevant compile/test target and a focused adapter or smoke check when
  privileged behavior changed.
- Inspect the diff for secrets, local config, broad shell/filesystem APIs,
  unsafe logs, and silent unsupported-target fallbacks.
- Verify ignored config files and release artifacts before publishing, tagging,
  or distributing binaries.
