---
keyflow_id: sys_android_memory_lifecycle
status: review
type: human-reviewed-needed
---

# Android Memory And Lifecycle Guidance

## Owner And Release Matrix

| Resource or operation | Typical owner | Release boundary |
| --- | --- | --- |
| Compose listener, observer, or receiver | `DisposableEffect` | key change or composition disposal |
| Lifecycle callback | lifecycle effect or owner | matching stop, pause, destroy, or removal |
| Lifecycle-bound Flow collection | lifecycle-aware coroutine | inactive state or composition disposal |
| ViewModel coroutine | `viewModelScope` | ViewModel clear |
| Activity/Fragment view binding and listeners | view lifecycle | `onDestroyView` or listener removal |
| WebView | screen or holder | screen end or explicit destroy |
| Media player or large buffer | player/loader owner | screen exit, eviction, cancellation, or release policy |
| File stream or temporary file | operation or worker | `use`/`finally`, success, failure, or cancellation |
| Worker foreground resource or notification | Worker/WorkManager | success, failure, or cancel path |

## Rules

- Decide the owner and release boundary before allocating a heavy resource.
- `DisposableEffect` registrations must have matching `onDispose` cleanup.
- Use lifecycle-aware collection for UI state and repeatable active-state work;
  do not pass raw lifecycle-bound streams into leaf UI components.
- Do not store Activity, Fragment, View, or Composition references in a
  ViewModel, singleton, repository, or other long-lived object.
- Keep `GlobalScope` and unbounded `runBlocking` out of lifecycle-sensitive
  work. Use the scope owned by the operation or lifecycle.
- Retry, cancellation, logout, account change, and permission revocation must
  release temporary files, notifications, callbacks, and sensitive in-memory
  state when relevant.
- A pool or singleton is safe only when its retention, eviction, and release
  policy is explicit.

## Heavy Resource Checks

For WebView, media, bitmap, sensor, location, receiver, or file resources,
check creation frequency, callback removal, cancellation, off-screen behavior,
and failure cleanup. Avoid creating them inside recomposition or repeated list
item rendering unless the owner and reuse policy make that lifetime explicit.

## Verification

- Diff review pairs each allocation or registration with its release owner.
- Focused tests or harnesses cover retry, cancellation, failure, and owner end
  when those paths exist.
- Manual or UI checks cover enter/exit, rotation, background/foreground,
  off-screen scrolling, and account or permission changes as applicable.
- Report verified lifecycle paths separately from remaining manual checks.
