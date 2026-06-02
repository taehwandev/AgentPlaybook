---
keyflow_id: sys_swift_review
status: review
type: human-reviewed-needed
---

# Swift Review

Use for reviewing Swift app, package, architecture, module, SwiftUI/UIKit/AppKit
UI, state, concurrency, design-system, platform adapter, or Apple target
changes.

## Review

- Check architecture boundaries against `swift-architecture.md` when state,
  domain, data, platform, or dependency assembly changed.
- Check package, target, access-control, resource, import, and file ownership
  against `swift-code-structure.md` when files moved or a package/target split
  changed.
- Check design-system tokens, styles, primitives, variants, previews, and visual
  states against `swift-design-system.md` when shared UI, styling, or reusable
  controls changed.
- Confirm views/controllers render explicit state and send intent instead of
  owning API, persistence, credential, permission, or platform calls.
- Confirm `UiState` or equivalent state models represent loading, content,
  empty, error, permission denied, offline/unavailable, disabled, submitting,
  success, and stale states when reachable.
- Verify `@MainActor`, actor isolation, `Sendable`, cancellation, stale result
  suppression, and resource cleanup for async, delegate, notification, timer,
  Combine, or OS-handle work.
- Ensure domain and contract modules avoid SwiftUI, UIKit, AppKit, DTO,
  persistence row, SDK, and app-route implementation dependencies.
- Ensure sensitive data is not stored in plain UserDefaults, logs, previews,
  fixtures, screenshots, or public bundles.
- Review platform security surfaces such as Keychain, URL schemes, Universal
  Links, entitlements, WebViews, file access, Accessibility, signing,
  notarization, app extensions, and release builds when touched.

## Tools

- Static: Swift compiler, SwiftLint, SwiftFormat, or repo-local wrapper when
  configured.
- Unit: XCTest or Swift Testing for mappers, policies, use cases, reducers,
  state owners, adapters, and style/token mapping.
- UI: XCUITest or repo-local smoke checks for navigation, forms, permissions,
  windows, panels, menus, focus, and critical flows.
- Preview/visual: SwiftUI previews, snapshots, fixture review, or screenshot
  checks when visual states changed and the repo supports them.
- Build: `swift build`, `swift test`, `xcodebuild`, or the repo's documented
  build/test scripts for affected targets.

## Structure Checks

- App target owns composition root and lifecycle, not feature internals.
- Feature modules own cohesive workflows, not shared primitives or raw SDK
  clients.
- Contract modules contain small stable caller-facing APIs and no implementation
  dependencies.
- Shared packages have one clear owner and do not become mixed helper dumps.
- Resources, localization, previews, fixtures, and generated files stay with the
  target or package that owns them.
- Public APIs are intentional caller contracts with compatibility and tests.

## Design-System Checks

- Tokens are semantic and cover role, state, hierarchy, appearance, density, and
  accessibility behavior where applicable.
- Primitives define loading, disabled, focused, invalid, selected, expanded,
  destructive, empty, and unavailable states when reachable.
- Reusable SwiftUI APIs use explicit bindings, callbacks, slots, typed variants,
  and caller-owned product policy instead of page-specific boolean flags.
- UIKit/AppKit bridges preserve Dynamic Type, focus, contrast, safe areas,
  window size changes, and platform appearance behavior.
- Product copy, navigation, analytics, permissions, repository calls, and domain
  policy remain in features or callers.

## Verification Focus

- Main user or system flow works through the changed entry point.
- Loading, empty, error, permission-denied, disabled, offline/unavailable, and
  success states are covered where applicable.
- Async work cancels or ignores stale results on disappear, logout, account
  switch, permission change, app backgrounding, process termination, or command
  replacement when those events matter.
- Denied or unavailable users cannot trigger protected work only because a
  button is hidden; command, adapter, or API boundary also handles denial.
- Dynamic Type, long text, dark mode, focus, keyboard, VoiceOver, small screens,
  compact panels, or window resizing do not break changed UI.
- Release configuration does not expose debug endpoints, broad entitlements,
  secrets, local file paths, or private diagnostics.
