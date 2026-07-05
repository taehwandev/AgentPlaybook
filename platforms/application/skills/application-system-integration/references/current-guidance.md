---
keyflow_id: sys_b9d08be59ef0
status: review
type: ai-generated
---

# Application System Integration

Use when touching windows, commands, files, shell, clipboard, notifications, background work, power assertions, menu bar/tray items, or app updates.

For privileged APIs, IPC, shell/file access, signing, notarization, or update trust, also use `application-security.md`.

## Defaults

- Window state and product state are separate.
- Menu, shortcut, tray, toolbar actions route through commands.
- System APIs stay behind adapters.
- Privileged APIs exposed to renderer/webview are narrow and typed.
- Background work has cancellation, progress, retry, and user-visible error handling.
- Signing, permissions, first launch, and update flow need smoke coverage.
- Timers, event monitors, power assertions, background tasks, and OS handles are released on stop, failure, timeout, and app quit.
- Menu bar, shortcut, toolbar, and panel entry points share the same command path.

## Check

- Can this action run from menu, shortcut, and UI consistently?
- What state survives app restart?
- Are file paths, tokens, and private data kept out of logs?
- What permission, signing, or OS resource does this action require?
- What cleanup happens if the app quits while the action is active?

## Do Not

- Do not create separate menu, shortcut, tray, toolbar, and UI code paths for
  the same command. Route them through one command boundary.
- Do not expose broad shell, file, clipboard, notification, updater, or OS APIs
  directly to a renderer, WebView, plugin, or untrusted script surface.
- Do not leave timers, event monitors, file handles, power assertions,
  background tasks, sockets, or observers alive after stop, failure, timeout, or
  app quit.
- Do not log private file paths, clipboard contents, tokens, command payloads,
  document contents, or update credentials as part of diagnostics.
- Do not treat signing, notarization, permissions, login items, update trust,
  or first-launch prompts as covered by a UI-only smoke check.
