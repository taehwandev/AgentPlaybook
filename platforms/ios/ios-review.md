---
keyflow_id: sys_9b770e3542d3
status: review
type: ai-generated
---

# iOS Review

Use for iOS SwiftUI/UIKit, navigation, concurrency, permission, and UI flow review.

## Review

- Check View/ViewModel ownership, navigation state, async task lifetime, and cancellation.
- Check SwiftUI route/screen/section boundaries against
  `ios-swiftui-ui.md` when SwiftUI screens changed.
- Confirm `UiState` represents loading, content, empty, error, permission
  denied, offline, disabled, and submitted states when applicable.
- Verify main actor boundaries for UI updates.
- Ensure API, persistence, keychain, file, notification, and permission APIs are wrapped.
- Check loading, empty, error, permission-denied, and offline states.
- Confirm sensitive data is not stored in plain UserDefaults or logs.
- Review Universal Links, URL schemes, entitlements, WebView bridges, ATS
  exceptions, and release signing when security surfaces change.

## Tools

- Static: Swift compiler, SwiftLint if configured.
- Unit: XCTest or Swift Testing for mapper, policy, service, ViewModel state.
- UI: XCUITest for navigation, forms, permissions, and critical flows.
- Snapshot: use only when visual regression matters and repo already supports it.
- Build: `xcodebuild test` or repo wrapper command.

## UI Test Focus

- Main flow works from launch to completion.
- Permission prompts and denied states are handled.
- Async loading and cancellation do not leave stale UI.
- SwiftUI previews or an equivalent visual check cover the changed visual
  states when UI structure changed.
- Dynamic Type, small screens, and VoiceOver labels are considered.
- Release configuration does not expose debug endpoints, secrets, or broad
  entitlements.
