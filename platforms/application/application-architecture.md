---
keyflow_id: sys_7a1b89bb9a49
status: review
type: ai-generated
---

# Application Architecture

Use for desktop/native app shells: Mac, Tauri, Electron, menu bar, windows, local files, and system integration.

For concrete command routing, window/panel state, renderer/IPC bridge, and
background resource ownership, also use `application-command-ui.md`.

For files, shell, clipboard, notifications, background work, updates, power assertions, menu bar/tray controls, or privileged APIs, also use `application-system-integration.md`.

For signing, notarization, IPC, URL schemes, renderer bridges, shell/file access, or credential exposure risk, also use `application-security.md`.

For Swift macOS apps, also use `../swift/swift-architecture.md`,
`../swift/swift-code-structure.md`, and `../swift/swift-design-system.md` for
Swift package, state, module, and design-system boundaries.

## Boundaries

```text
Window/Scene/View -> Presentation State -> Command/Use Case -> App Service -> System Adapter
```

## Rules

- Separate window lifecycle from screen state.
- Route menu, shortcut, toolbar actions through commands.
- Wrap file, shell, notification, clipboard, permission APIs.
- Keep IPC contracts typed and explicit.
- Long-running work needs cancellation, progress, and error reporting.
- Distinguish user-facing errors from logs.
- Keep menu bar/tray, panel, shortcut, and toolbar entry points on the same command path.
- Keep OS resource ownership explicit: status items, windows, monitors, timers, assertions, and background workers.

## Do Not

- Do not expose broad shell, filesystem, clipboard, environment, updater,
  credential, or permission APIs directly to renderer, webview, plugin, or
  untrusted URL code.
- Do not let windows or panels own product rules, persistence, SDK calls,
  command validation, and rendering in one unit.
- Do not implement the same user action separately for menu, shortcut, toolbar,
  tray, and panel entry points.
- Do not start background work, watchers, monitors, timers, or power assertions
  without a cancellation and cleanup owner.
- Do not log local paths, file contents, clipboard values, private prompts,
  credentials, tokens, or privileged command output.

## Refactor Signals

- Window code owns file I/O, network, and product rules.
- Menu actions repeat permission/state checks.
- Renderer exposes privileged APIs too broadly.
- Background task ownership is unclear.
- App quit, timeout, or failure does not clean up active OS resources.

## Verification

- command/use-case test for each changed menu, shortcut, toolbar, tray, panel,
  or renderer entry point
- IPC/bridge test or typed contract inspection when renderer/native boundaries
  changed
- lifecycle smoke for window open/close, app quit, cancellation, timeout, and
  failed background work when OS resources are touched
- signing, update, entitlement, permission, first-launch, or packaging smoke
  check when release-sensitive app configuration changed
