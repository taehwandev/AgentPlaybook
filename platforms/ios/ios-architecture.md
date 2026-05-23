---
keyflow_id: sys_e5ada2ab6483
status: review
type: ai-generated
---

# iOS Architecture

Use for SwiftUI/UIKit app structure, state, navigation, and async work.

For SwiftUI screen/component structure, ViewModel contracts, `UiState`, previews,
or clean-architecture implementation details, also use `ios-swiftui-ui.md`.

For navigation, async work, persistence, permissions, or actor boundaries, also use `ios-state-concurrency.md`.

For credentials, Keychain, local storage, Universal Links, URL schemes,
entitlements, WebViews, or release builds, also use `ios-security.md`.

## Boundaries

```text
View/ViewController -> ViewModel/State -> Use Case -> Repository/Client -> Platform Adapter
```

## Rules

- View renders state and sends intent.
- Keep ViewModel-backed containers thin and delegate rendering to explicit
  screen/section views when SwiftUI is used.
- Model loading, empty, error, permission states explicitly.
- Choose simple SwiftUI, MVVM, clean architecture, or reducer/state-machine
  tracks based on real state, side-effect, domain, and test pressure.
- Keep async task ownership and cancellation visible.
- Keep UI updates on the correct actor boundary.
- Wrap API, persistence, keychain, file, notification, permission APIs.
- Keep DTOs out of Views when they carry transport details.

## Refactor Signals

- SwiftUI body owns side effects and business rules.
- ViewModel exposes raw API DTOs.
- Permission checks repeat in Views.
- ViewController owns UI, API, and state transformation together.
