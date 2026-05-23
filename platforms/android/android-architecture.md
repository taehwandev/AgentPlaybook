---
keyflow_id: sys_f6093ac42517
status: review
type: ai-generated
---

# Android Architecture

Use for Compose/ViewModel/Flow, data, and Android platform boundary work.

For Compose state, Flow, repository, persistence, permissions, or lifecycle details, also use `android-state-data.md`.

For Compose screen/component structure, stateful/stateless split, previews, or
package layout, also use `android-compose-ui.md`.

For credentials, deep links, exported components, WebView, or release builds, also use `android-security.md`.

For WorkManager, foreground services, alarms, notifications, sync, uploads, or downloads, also use `android-background-work.md`.

## Boundaries

```text
Screen/Composable/Fragment -> ViewModel -> Use Case -> Repository -> Data Source/Platform Adapter
```

## Rules

- Composable renders state and sends events.
- Split ViewModel-backed holder composables from stateless screen/content
  composables.
- ViewModel owns UI state and lifecycle-aware work.
- Model loading, empty, error, permission denied explicitly.
- Keep one-off events separate from persistent state.
- Wrap API, Room, DataStore, file, permission, notification APIs.
- Keep background work behind Worker/use-case boundaries.
- Validate exported components, deep links, and release build security surfaces.
- Follow the repo's existing DI style.

## Refactor Signals

- Composable directly calls repository or API.
- ViewModel is tied to too many Android framework types.
- UI state is nullable values plus many flags.
- Navigation parsing and business rules are mixed.
- Background work is launched directly from UI without retry or cancellation policy.
- Exported components, WebView bridges, or deep links are added without a security review.
