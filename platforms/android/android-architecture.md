---
keyflow_id: sys_f6093ac42517
status: review
type: ai-generated
---

# Android Architecture

Use for Compose/ViewModel/Flow, data, and Android platform boundary work.

For Compose state, Flow, repository, persistence, permissions, or lifecycle details, also use `android-state-data.md`.

For ViewModel, `UiState`, Flow, repository, use case, persistence, and one-off event implementation details, also use `android-viewmodel-state.md`.

For Compose screen/component structure, stateful/stateless split, previews, or package layout, also use `android-compose-ui.md`.

For Gradle module boundaries, `api`/implementation splits, package layout, and feature/common/core ownership, also use `android-module-structure.md`.

For credentials, deep links, exported components, WebView, or release builds, also use `android-security.md`.

For WorkManager, foreground services, alarms, notifications, sync, uploads, or downloads, also use `android-background-work.md`.

## Boundaries

```text
Screen/Composable/Fragment -> ViewModel -> Use Case -> Repository -> Data Source/Platform Adapter
```

Module boundaries should support this dependency direction instead of fighting it. UI feature modules depend on repository/domain contracts, not repository internals; shared core/design-system modules do not depend on feature implementations.

## Concrete Structure Baseline

For a product-sized Compose app, start with this concrete structure and shrink it when the repo is smaller:

```text
app                         Activity, app startup, top-level navigation, DI wiring
core/designsystem            theme, semantic tokens, component wrappers, previews
core/model                   pure Kotlin product models and ids
core/domain                  use cases, repository contracts, product policies
core/data                    repository implementations, DTO/cache mapping, fakes
feature/<name>/api           route contracts, entrypoints, public events
feature/<name>/impl          Route, ViewModel, UiState, Screen, feature components
build-logic                  convention plugins and shared build settings
```

Keep the `app` module thin. Put reusable visual primitives in the design system, pure business data in model/domain, source coordination in data, and screen orchestration in feature implementations. Skip `api` modules, use cases, or repository splits until another module, test boundary, platform dependency, or replaceable implementation needs the contract.

## Feature Slice Baseline

Start every Android feature by naming the smallest architecture track that fits the behavior:

| Track | Use When | Required Shape |
| --- | --- | --- |
| Local UI | Local interaction only; no async data, persistence, permission, or navigation side effect. | Stateless composable plus local `remember` state where needed. |
| MVVM | Screen loads data, submits forms, handles permission state, emits navigation, or has testable UI logic. | `Route -> ViewModel -> Screen`; ViewModel owns `UiState`, actions, and effects. |
| Clean Architecture | Domain policy, offline/cache, auth/tenant/billing, sync, multiple clients, or risky side effects. | `Route -> ViewModel -> UseCase -> Repository -> DataSource/Adapter`. |
| Reducer/MVI | Many actions, optimistic updates, replayable transitions, concurrency races, or complex undo/retry. | `Route -> ViewModel/Store -> Reducer -> Effects/UseCases`. |

Do not add use cases, repositories, reducers, or modules only for ceremony. Add them when they protect a product rule, platform side effect, cache boundary, permission boundary, or test boundary.

## Rules

- Composable renders state and sends events.
- Split ViewModel-backed holder composables from stateless screen/content composables.
- ViewModel owns UI state and lifecycle-aware work.
- Model loading, empty, error, permission denied explicitly.
- Keep one-off events separate from persistent state.
- Wrap API, Room, DataStore, file, permission, notification APIs.
- Keep background work behind Worker/use-case boundaries.
- Validate exported components, deep links, and release build security surfaces.
- Follow the repo's existing DI style.

## Feature Implementation Checklist

For a non-trivial Compose feature, expect these pieces unless the repo has a more specific pattern:

```text
<Feature>Route.kt      stateful holder, ViewModel wiring, effects, navigation
<Feature>Screen.kt     stateless screen rendering and user intent callbacks
<Feature>UiState.kt    immutable state, actions, effects, UI display models
<Feature>ViewModel.kt  state owner, action handling, coroutine ownership
components/            feature-local stateless pieces
preview/               preview fixtures and sample UI states
```

Implementation order:

1. Define the screen contract: state, user actions, one-off effects, and route outputs.
2. Create or update the stateless `Screen` and previews for visible states.
3. Add the `Route` holder that collects state lifecycle-aware and handles effects.
4. Add ViewModel/use-case/repository boundaries only where data, policy, cache, permission, or platform APIs require ownership.
5. Verify state transitions and the visible UI path with repo-local tests, previews, screenshots, or manual smoke evidence.

Module decision:

- Keep the feature in one module when no caller needs a stable route or contract.
- Add `feature-api` when navigation, holder registration, route data, or another module needs the feature contract without implementation dependencies.
- Add repository `api`/implementation split when features need stable repository interfaces/entities but must not see DTOs, Retrofit/Room/DataStore, SDKs, or cache internals.
- Add shared/core modules only for stable, repeated contracts with clear ownership; do not create catch-all common modules.

## Boundary Placement

- Parse route arguments at the `Route` or navigation adapter boundary, then pass typed values into the ViewModel.
- Keep `Context`, `Activity`, `NavController`, permission launchers, `ActivityResultLauncher`, clipboard, files, notifications, sensors, and SDK calls out of stateless composables.
- Keep domain models free of Compose rendering types. Map domain to UI display models before the state reaches `Screen`.
- Keep repositories out of ViewModels only when a use case owns real product orchestration; pass-through use cases are optional, not mandatory.
- Keep data sources behind repositories or adapters. Room, DataStore, Retrofit, files, permissions, and SDK objects should not reach UI state directly.

## Refactor Signals

- Composable directly calls repository or API.
- ViewModel is tied to too many Android framework types.
- UI state is nullable values plus many flags.
- Navigation parsing and business rules are mixed.
- Background work is launched directly from UI without retry or cancellation policy.
- Exported components, WebView bridges, or deep links are added without a security review.
- A feature adds ViewModel state without previews or a visible-state test.
- A shared composable accepts product policy, routes, repositories, or a full screen `UiState` when smaller values would preserve reuse.
