---
keyflow_id: sys_60c9ad0c6826
status: review
type: ai-generated
---

# iOS State And Concurrency

Use when touching SwiftUI/UIKit state, navigation, async work, or platform permissions.

For SwiftUI `UiState`, ViewModel, screen composition, and preview rules, also use
`ios-swiftui-ui.md`.

For repository/client contracts, adapter packages, local Swift packages, and
target ownership, also use `ios-module-structure.md`.

## Defaults

- View owns only local presentation state.
- ViewModel or observable state owns loading, empty, error, and permission states.
- Prefer typed state models or enums over scattered booleans and nullable data
  when states are mutually exclusive.
- Navigation state is modeled, not hidden in side effects.
- Async work has visible ownership, cancellation, and error handling.
- UI updates respect actor boundaries.
- Long-running tasks define cancellation on disappear, logout, account switch,
  and permission changes.
- Persisted state defines migration, corruption, and app-upgrade behavior.
- Keychain, files, notifications, permissions, and persistence stay behind adapters.

## Async API Errors

For `async throws` repository or client calls, do not make `Result<Success,
Failure>` or a custom `success/failure` response enum the default shape only to
re-wrap thrown errors. Let successful async calls return the decoded value or an
internal response type, and throw typed transport, protocol, or domain errors
for failure.

Network adapters should hide `URLSession`, provider SDK, and transport-library
details by normalizing only the small response boundary the app owns, such as
status, selected headers, body, safe server error code, retry metadata, and
correlation id. ViewModels, stores, reducers, or coordinators catch those typed
errors and map them into `UiState`, alert/sheet/navigation state, or one-off
effects.

If a server error envelope carries presentation hints such as inline, banner,
alert, full-page, retry, or a deep-link action, treat them as stable contract
hints. The iOS state owner decides how to render supported hints in SwiftUI or
UIKit and defines a safe fallback for unsupported hints.

## Check

- Can stale async results update the UI?
- What happens when the view disappears?
- What cancels or restarts work after logout, account switch, app backgrounding,
  or process termination?
- Does permission denial have a user-visible state?
- Is sensitive data outside plain UserDefaults and logs?
- Are Task, async sequence, Combine, and observation lifetimes chosen
  intentionally?

## Tests

Cover cancellation, stale result suppression, permission denial, persistence
migration, process relaunch, and actor-boundary behavior when applicable.
