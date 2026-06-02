---
keyflow_id: sys_e5ada2ab6483
status: review
type: ai-generated
---

# iOS Architecture

Use for iOS SwiftUI/UIKit app structure, state, navigation, async work,
permissions, and app target behavior.

For Swift-wide app architecture, package, state owner, domain/data/platform
boundary, and design-system rules, also use
`../swift/swift-architecture.md`, `../swift/swift-code-structure.md`, and
`../swift/swift-design-system.md`.

For SwiftUI screen/component structure, ViewModel contracts, `UiState`, previews,
or clean-architecture implementation details, also use `ios-swiftui-ui.md`.

For UIKit screens, coordinators, view controllers, presenters, table/collection
views, diffable data sources, forms, or UIKit navigation, also use
`ios-uikit-ui.md`.

For targets, local Swift packages, feature folders, access control, and
contract/module splits, also use `ios-module-structure.md`.

For navigation, async work, persistence, permissions, or actor boundaries, also use `ios-state-concurrency.md`.

For credentials, Keychain, local storage, Universal Links, URL schemes,
entitlements, WebViews, or release builds, also use `ios-security.md`.

## Boundaries

```text
View/ViewController -> ViewModel/State -> Use Case -> Repository/Client -> Platform Adapter
```

Targets and Swift packages should support this direction. Feature
implementations depend on contracts, domain, data protocols, design system, and
platform adapters; shared design/domain modules do not import feature
implementations.

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
