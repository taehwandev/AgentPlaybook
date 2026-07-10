---
keyflow_id: sys_application_command_ui
status: review
type: human-reviewed-needed
---

# Application Command And UI

Use when creating, changing, moving, or reviewing desktop/native app windows,
panels, menu bar/tray items, shortcuts, commands, local state, background tasks,
IPC bridges, or UI tests.

For shell, file, clipboard, notification, power, update, and OS integration
details, also read `application-system-integration.md`. For privileged APIs,
IPC, signing, notarization, and update trust, also read
`application-security.md`.

## Application Layers

Use this shape unless the repo has a stricter local pattern:

```text
Window/Panel/View -> Presentation State -> Command/Use Case
-> App Service -> System Adapter
```

- Window/panel/view owns rendering, focus, layout, user intent, and presentation
  lifecycle.
- Presentation state owns visible loading, error, permission, progress, and
  selection state.
- Command/use case owns product action semantics and can be invoked from menu,
  shortcut, toolbar, tray/menu bar, or UI.
- App service owns orchestration, persistence, and background work.
- System adapter owns filesystem, shell, clipboard, notification, accessibility,
  power assertions, login items, updater, OS handles, and IPC.

## File And Command Split

Apply `../../common/skills/code-structure-ownership/SKILL.md` before growing desktop/native
runtime files. Default to one primary window/panel, presentation state owner,
command/use case, app service, system adapter, IPC contract, fixture, or
assertion owner per file.

Split files before adding behavior when command enablement, validation,
permission, progress, cancellation, bridge mapping, system API access, window
state, product state, and rendering can be named or tested independently.

Review must fail when a desktop/application runtime file keeps multiple
independently importable owners in one file: windows, panels, presentation
state, commands, services, system adapters, IPC contracts, bridge mappers,
fixtures, or assertion helpers.

Do not:

- Put a window, view state, command, service, filesystem/shell adapter, IPC
  payload mapper, and renderer UI in one file.
- Implement menu, shortcut, toolbar, tray, panel, and renderer actions in
  separate files that each repeat the same product logic instead of sharing a
  command boundary.
- Hide privileged shell, filesystem, clipboard, updater, permission, or
  credential access behind a broad `AppService`, `SystemService`, `Helpers`, or
  `Utils` file.
- Split into packages or targets when purpose-named files inside the current
  boundary would make ownership and verification clear.

## Command Rule

Every user action that can be triggered from more than one entry point should
route through one command path:

```text
menu item -> Command
shortcut -> Command
toolbar button -> Command
tray/menu bar item -> Command
panel button -> Command
```

The command should define:

- enabled/disabled state
- required permission, entitlement, file access, or OS capability
- input validation
- cancellation behavior
- progress reporting
- user-visible error
- cleanup on failure, timeout, cancellation, and app quit

Do not duplicate action logic in menu handlers, button handlers, IPC handlers,
and shortcut callbacks.

## Window And State Rule

- Window visibility, position, focus, and restoration state are not product
  state.
- Product state should survive close/reopen only when the product requires it.
- Panels, popovers, menu bar extras, and secondary windows need one owner.
- App launch, first run, restore, sign out, permission revoke, update, and quit
  should define state cleanup.
- UI should render loading, empty, error, permission denied, offline/unavailable,
  progress, disabled, and success states when reachable.

## IPC And Renderer Bridge

For Tauri, Electron, WebView, plugin, or renderer/main-process apps:

- Expose narrow typed commands, not broad filesystem, shell, environment, or
  credential APIs.
- Validate all renderer, URL, file, drag/drop, plugin, and external-app inputs.
- Keep privileged work in the trusted process or native layer.
- Treat IPC payloads as untrusted input even when the UI created them.
- Return stable, user-safe errors and log private detail only in safe logs.

## Background Work And OS Resources

- Long-running work needs cancellation, progress, timeout, retry, and
  user-visible failure state.
- Timers, event monitors, file watchers, power assertions, background tasks,
  sockets, and OS handles need explicit owners.
- Release resources on stop, failure, timeout, cancellation, logout, app quit,
  and window deallocation where applicable.
- Do not leave menu bar/tray indicators, monitors, or assertions active after
  the command has stopped.

## File Layout

A desktop feature can use:

```text
Features/Capture/
  CaptureWindow.swift / CapturePanel.tsx
  CaptureState.swift / captureState.ts
  CaptureCommand.swift / captureCommand.ts
  CaptureService.swift / captureService.ts
  System/
    ClipboardAdapter.swift / clipboardAdapter.ts
    FileBookmarkStore.swift / fileBookmarkStore.ts
  Tests/
```

Adapt names to Swift, Rust/Tauri, Electron, or the repo's local structure while
preserving command and adapter ownership.

## Tests

Choose the closest checks configured in the repo:

- Command tests for enabled state, validation, permission failure,
  cancellation, progress, and user-visible errors.
- Adapter tests for filesystem, clipboard, shell, notification, update, or
  permission behavior where the repo supports fakes.
- UI tests for window open/restore/close, menu/shortcut/tray consistency, forms,
  and permission prompts.
- Packaging smoke for signing, notarization, first launch, update, and
  quarantine behavior when release surfaces change.

Review the final diff for duplicated menu/button logic, privileged renderer
APIs, product state stored as window state, missing cleanup, hidden background
work, and private file/token/clipboard data in logs.
