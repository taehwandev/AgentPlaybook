---
keyflow_id: sys_application_react_desktop
status: review
type: ai-generated
---

# Application React Desktop

Use when building, refactoring, or reviewing a desktop app that uses a React
renderer inside a native shell, such as Tauri, Electron, WebView, or a Mac/Win
app with embedded web UI.

Also use:
- `application-architecture.md` for desktop shell and OS resource ownership.
- `application-command-ui.md` for commands, windows, panels, shortcuts, and
  renderer bridges.
- `application-system-integration.md` for files, shell, clipboard,
  notifications, background work, updates, and OS APIs.
- `application-security.md` for IPC, URL schemes, signing, updater trust,
  broad filesystem or shell access, and renderer exposure.
- `../web/web-code-structure.md` for React feature folder and import
  boundaries.
- `../web/web-react-ui.md` for container/screen, hook, `UiState`, and
  component contracts.
- `../web/web-state-data.md` when renderer state, cache, persistence, forms, or
  API clients are touched.

## Boundary Shape

Use this shape unless the target repo has a stricter local pattern:

```text
OS entry point -> Command/Use Case -> App Service -> System Adapter
                           |
                    Typed IPC/Bridge
                           |
Renderer Shell -> Feature Container -> Screen/View -> Feature Component
```

- OS entry points include menu items, shortcuts, tray/menu bar controls,
  toolbar buttons, deep links, file drops, and app lifecycle events.
- Commands own action semantics, enabled state, validation, permission checks,
  cancellation, progress, and user-visible errors.
- App services orchestrate persistence, background work, local workspace state,
  and system adapters.
- System adapters own filesystem, shell, clipboard, notifications, updater,
  window APIs, native permissions, watchers, and OS handles.
- The typed IPC/bridge is a trust boundary. It should expose narrow commands,
  validate renderer input, and return stable result/error shapes.
- Renderer shell owns route or view composition, layout regions, focus, and
  top-level providers.
- Feature containers wire renderer state, bridge calls, policies, and effects
  for one workflow.
- Screens and feature components render explicit state and emit intent. They
  should not call raw IPC, filesystem, shell, or native APIs.

## State Ownership

- Window visibility, size, focus, drag regions, panel placement, and tray/menu
  state are shell state, not product state.
- Renderer-local UI state stays near its interaction owner: menu open, selected
  row, draft text, hover, focus, and transient dialog state.
- Product/workspace state belongs to a feature store, use case, or app service
  with explicit persistence and restore rules.
- Server state and local filesystem state are different sources of truth. Do
  not copy one into the other without a sync rule, conflict rule, and refresh
  rule.
- File watchers, subscriptions, timers, monitors, background tasks, and IPC
  listeners need a single owner and cleanup on stop, timeout, failure,
  cancellation, window close, and app quit.
- Writes made by the app should not trigger recursive watcher or sync loops.
  Add an app-originated write guard, debounce, or normalization pause when a
  watcher observes files the app also writes.

## React Renderer Rules

- Keep raw bridge calls out of JSX. Put them behind feature hooks, clients,
  use cases, or command adapters.
- Convert IPC payloads, native errors, file metadata, and persisted records
  into display models before rendering.
- Represent loading, empty, error, permission denied, unavailable, progress,
  dirty, saving, and conflict states when the workflow can reach them.
- Use `useEffect` only to synchronize with external systems such as bridge
  subscriptions, timers, focus, media, watchers, and imperative editor APIs.
  Effects need dependencies and cleanup.
- Do not add a global provider for one panel, modal, tab, or temporary draft.
- Keep design-system primitives free of routes, bridge calls, platform policy,
  filesystem paths, analytics events, and product rules.

## File Layout

Adapt names to the repo, but keep ownership visible:

```text
src/
  app/
    AppShell.tsx
    routes/ or views/
  features/
    workspace/
      WorkspaceContainer.tsx
      WorkspaceScreen.tsx
      components/
      model/
        workspaceTypes.ts
        workspaceMappers.ts
        workspacePolicy.ts
      hooks/
        useWorkspace.ts
      commands/
        workspaceCommands.ts
      __tests__/
  platform/
    bridge/
      desktopBridge.ts
      desktopBridgeTypes.ts
      desktopErrors.ts
    adapters/
      fileSystemAdapter.ts
      shellAdapter.ts
      windowAdapter.ts
  services/
    workspaceService.ts
    sessionService.ts
```

Use a different folder shape when the repo already has one, but preserve these
owners:

- feature folders own one user workflow and renderer-facing models.
- bridge modules own typed IPC contracts and error/result mapping.
- platform adapters own native or privileged APIs.
- services own orchestration and background work.
- shared UI owns visual primitives only.

## Refactor Signals

- A React component imports Tauri, Electron, shell, filesystem, updater, or
  clipboard APIs directly.
- The same action logic is duplicated in a menu handler, shortcut callback,
  toolbar button, IPC handler, and React event handler.
- Window state is used as the source of product/session/workspace state.
- A feature container owns filesystem I/O, bridge payload mapping, permission
  policy, editor state, and rendering in one file.
- IPC accepts broad paths, commands, environment values, shell strings, or
  untyped payloads from the renderer.
- File watcher, refresh, save, and AI or background edits can trigger each
  other without an app-originated write guard.
- Multiple global stores or providers exist only because feature ownership is
  unclear.

## Refactor Recipe

1. Inventory OS entry points, React entry points, IPC calls, stores, providers,
   direct system API calls, watchers, and tests.
2. Pick one user workflow or one bridge boundary. Do not restructure the whole
   shell and all features in one pass.
3. Route duplicated menu, shortcut, toolbar, tray, and React actions through a
   named command or use case.
4. Move raw bridge payload conversion into a bridge client, mapper, or feature
   model before moving large JSX blocks.
5. Split feature containers from screens when data/effects and rendering are
   mixed.
6. Move privileged APIs into adapters and keep renderer access narrow.
7. Add focused contract tests for command enablement, bridge payloads, watcher
   loop guards, state restore, and visible failure states.
8. Run the narrowest available typecheck, frontend test, native command test,
   and smoke scenario for the affected workflow.

Do not mix product behavior changes with broad structure moves unless the
behavior change is an explicit acceptance point.

## Review Checklist

- Can the same user action run consistently from menu, shortcut, toolbar, tray,
  and React UI?
- Are renderer bridge APIs typed, narrow, validated, and mapped to stable
  user-safe errors?
- Does each long-running command expose cancellation, progress, timeout, and
  cleanup behavior?
- Are shell/window state, renderer UI state, product state, server state, and
  local filesystem state owned separately?
- Are app-originated writes guarded against watcher, sync, or normalization
  loops?
- Are local paths, file contents, clipboard contents, private prompts, tokens,
  and credentials kept out of logs and client-visible config?
- Can the changed workflow be tested without booting unrelated systems?
