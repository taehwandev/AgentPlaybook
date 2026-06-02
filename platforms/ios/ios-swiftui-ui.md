---
keyflow_id: sys_ios_swiftui_ui
status: review
type: human-reviewed-needed
---

# iOS SwiftUI UI

Use when creating, changing, moving, or reviewing SwiftUI screens, view models,
state models, reusable views, previews, navigation, or UI tests.

For architecture choice, also read `../../common/architecture-design.md` and
`../swift/swift-architecture.md`. For Swift design-system tokens, styles,
primitives, and reusable component contracts, also read
`../swift/swift-design-system.md`. For
state lifetimes, async work, cancellation, persistence, and actor boundaries,
also read `ios-state-concurrency.md`. For reusable UI extraction, also read
`../../common/reusable-code-design.md` and `../../common/design-system.md`.
For targets, local Swift packages, feature contracts, and access-control
boundaries, also read `ios-module-structure.md` and
`../swift/swift-code-structure.md`.

## SwiftUI Layers

Use this shape unless the repo has a stricter local pattern:

```text
Route/Coordinator -> Screen View -> Section View -> Feature View
-> Design-System Primitive
```

- Route/coordinator owns navigation wiring, dependency entry points, sheets,
  alerts that cross screen boundaries, and platform handoff.
- Screen view renders one workflow. It observes state, sends user intent, and
  delegates complex areas to section views.
- Section views render one part of the screen and receive only the state they
  need.
- Feature views may know feature display models but not repositories, API
  clients, keychain, files, permission services, or analytics dispatch.
- Design-system primitives own visual and interaction contracts, not product
  policy, routing, or domain rules.

## Architecture Tracks

Choose the smallest track that makes ownership and testing clear:

| Track | Use When | Shape |
| --- | --- | --- |
| Simple SwiftUI | Local screen state, no domain workflow, no persistence, no external service. | `View -> local @State` |
| MVVM | Loading, form submission, async fetch, navigation state, permission state, or reusable screen logic. | `View -> @MainActor ViewModel -> Repository/Client` |
| Clean Architecture | Domain policy, offline/sync, auth/tenant/billing, multiple clients, multiple callers, or complex test boundary. | `View -> ViewModel -> UseCase -> Repository protocol -> Adapter/Client` |
| Unidirectional State | Many events, state transitions, optimistic updates, replayable actions, or reducer tests. | `View -> Store/Reducer -> Effects/UseCases -> Repositories` |

Do not add use cases, repositories, reducers, or protocols only for ceremony.
Add them when they isolate a real product rule, side effect, or test boundary.

## ViewModel Rule

View models should:

- Be `@MainActor` when they publish UI state.
- Own screen-level `UiState`, user actions, async task coordination, and
  user-visible errors.
- Depend on protocols or small client interfaces for API, persistence, keychain,
  files, permissions, notifications, and external SDKs.
- Convert DTO/domain models into display models before the view renders them.
- Expose methods named by user intent, such as `onAppear()`, `refresh()`,
  `submit()`, `retry()`, `selectItem(_:)`, or `dismissError()`.

Views should not:

- Call repositories, URLSession, Keychain, file APIs, permission APIs, or
  analytics directly.
- Own business rules in `body`, `.task`, `.onAppear`, or button handlers.
- Store server state in `@State` when a ViewModel should own the lifecycle.
- Switch on raw API errors or transport DTOs.

## UiState Shape

Use explicit state instead of scattered booleans and optional data.

For mutually exclusive screen states, prefer an enum:

```swift
enum ProfileUiState: Equatable {
    case loading
    case content(ProfileViewData)
    case empty
    case permissionDenied
    case offline(ProfileViewData?)
    case error(ProfileErrorViewData)
}
```

For content with independent sub-states, prefer a struct with typed fields:

```swift
struct CheckoutUiState: Equatable {
    var form: CheckoutFormState
    var submit: SubmitState
    var entitlement: EntitlementState
    var banner: BannerState?
}
```

Rules:

- Loading, empty, error, permission denied, offline, disabled, and submitted
  states must be representable.
- Keep one-off events separate from persistent state. Use navigation state,
  callback output, or a typed effect channel instead of hiding navigation inside
  random booleans.
- Do not represent state with unrelated pairs such as `isLoading`, `items?`,
  `error?`, and `isEmpty` when impossible combinations can occur.
- Do not put SwiftUI types such as `Color`, `Font`, `Image`, or `View` inside
  domain models. Keep those at the UI/display boundary.

## View Composition

Screen views should be easy to preview and test:

```swift
struct ProfileScreen: View {
    let state: ProfileUiState
    let onRetry: () -> Void
    let onEdit: () -> Void

    var body: some View {
        switch state {
        case .loading:
            ProgressView()
        case .content(let data):
            ProfileContent(data: data, onEdit: onEdit)
        case .empty:
            EmptyStateView(...)
        case .permissionDenied:
            PermissionDeniedView(...)
        case .offline(let cached):
            OfflineProfileView(cached: cached, onRetry: onRetry)
        case .error(let error):
            ErrorStateView(error: error, onRetry: onRetry)
        }
    }
}
```

- Keep ViewModel-backed containers thin and delegate rendering to pure views.
- Pass callbacks, bindings, and small display models, not full service objects.
- Keep `@State` local to presentation details such as focus, expansion, scroll,
  tab selection, text-field drafts before commit, and animation flags.
- Use `@Binding` only when the parent owns the value and two-way editing is the
  intended contract.
- Use environment values for framework-level concerns, not hidden business
  dependencies.

## Navigation And Effects

- Model navigation as explicit state or typed output from the screen owner.
- Keep deep link, URL scheme, tab, sheet, popover, and alert decisions at route
  or coordinator boundaries.
- Keep `.task` and `.onAppear` idempotent. They should call a ViewModel intent
  rather than embedding fetch logic.
- Ensure async work cancels on disappear, logout, account switch, permission
  changes, or task replacement when those events matter.
- Suppress stale async results when a newer request has replaced the old one.

## File Layout

A feature can use:

```text
Features/Profile/
  ProfileRoute.swift          navigation and dependency wiring
  ProfileScreen.swift         pure screen rendering
  ProfileViewModel.swift      state owner and intents
  ProfileUiState.swift        state, display models, actions, effects
  Components/                 feature-local views
  PreviewData/                deterministic preview fixtures
  ProfileViewModelTests.swift
```

Shared UI can use:

```text
DesignSystem/
  Theme/
  Components/
  Components/Inputs/
  Components/Feedback/
```

Promote a view to shared UI only when its caller contract is stable and product
copy, routing, analytics, permissions, and domain policy stay outside it.

## Preview Rule

Every new or meaningfully changed screen, section, or reusable view needs a
SwiftUI preview unless the repo has a stronger snapshot or UI test that covers
the same visual states.

Previews should:

- Target pure screen/section/component views, not dependency-heavy route views.
- Use deterministic sample state from `PreviewData`, fixtures, or static
  factory methods.
- Cover changed states such as content, loading, empty, error, permission
  denied, offline, disabled, long text, Dynamic Type, and dark mode when
  affected.
- Avoid network, persistence, keychain, random data, current time, real
  credentials, and device-only services.

If a preview cannot be added, name the replacement verification path.

## Tests

Choose the closest checks configured in the repo:

- ViewModel tests for state transitions, user intents, loading, error, retry,
  permission denial, and cancellation.
- Mapper tests for DTO/domain to display-state conversion.
- Use case tests when product rules move out of the ViewModel.
- XCUITest for navigation, forms, permissions, and critical flows.
- Snapshot tests only when the repo already supports them and visual regression
  is meaningful.
- Build or test command for the affected target.

Review the final diff for business rules in views, direct platform API calls
from UI, impossible UI state combinations, missing previews, and shared views
that absorbed product-specific behavior.
