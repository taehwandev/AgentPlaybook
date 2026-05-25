---
keyflow_id: sys_android_compose_ui
status: review
type: human-reviewed-needed
---

# Android Compose UI

Use when creating, changing, moving, or reviewing Jetpack Compose screens,
state holders, design-system components, feature UI components, previews, or UI
tests.

For reusable UI extraction, also read `common/reusable-code-design.md` and
`common/design-system.md`.

## Compose Layers

Use this shape unless the repo has a stricter local pattern:

```text
Route/Holder Composable -> Screen Composable -> Section Composable
-> Feature Component -> Design-System Primitive
```

- Route/holder composable wires ViewModel, lifecycle collection, effects,
  navigation callbacks, permission launchers, and dependency entry points.
- Screen composable is stateless. It receives immutable UI state plus explicit
  callbacks and renders the whole screen.
- Section composables group screen areas and accept only the state they need.
- Feature components may know product display models but not repositories,
  ViewModels, activities, or routers.
- Design-system primitives know visual and interaction contracts, not product
  routes, analytics labels, or fake data.

## Stateful And Stateless

Stateful composables:

- End with `Route`, `Host`, or another repo-local holder suffix when possible.
- Collect `StateFlow` with lifecycle-aware APIs.
- Own `LaunchedEffect` for one-off effects such as navigation, snackbar, focus,
  permission launch, or external activity launch.
- Translate platform results into ViewModel actions or route events.
- Delegate rendering to a stateless screen/content composable.

Stateless composables:

- Take `state: FooUiState`, explicit callbacks, slots, and `modifier`.
- Do not obtain ViewModels, repositories, activities, nav controllers, or
  service locators.
- Do not launch coroutines for business work.
- Keep UI-local state only when it affects rendering or interaction locally,
  such as scroll, focus, gesture, animation, expanded, selected tab, or text
  field draft state.
- Expose user intent as callbacks such as `onBackClick`, `onRetryClick`,
  `onQueryChange`, or `onAction` when the action set is already typed.

## UI State

Model screen states explicitly:

```text
loading -> content -> empty -> error -> permission denied -> offline
```

- Prefer immutable `UiState` data classes or sealed interfaces over scattered
  nullable values and boolean flags.
- Keep one-off effects separate from persistent state.
- Keep domain models free of Compose types such as `Color`, `Dp`, `TextStyle`,
  painter, icon lambdas, or resource ids.
- Map domain models to UI models in the feature UI/state boundary.
- User-facing strings should follow repo-local localization rules.

## Architecture Tracks

Choose the smallest track that makes ownership clear:

| Track | Use When | Shape |
| --- | --- | --- |
| Simple Compose | Local interaction only, no async data or product workflow. | `Composable -> local remember state` |
| MVVM | Loading, forms, async fetch, permission state, navigation output, or reusable screen logic. | `Route -> ViewModel -> Screen` |
| Clean Architecture | Domain policy, offline/sync, auth/tenant/billing, multiple clients, or complex test boundary. | `Route -> ViewModel -> UseCase -> Repository -> DataSource` |
| Reducer/MVI | Many events, replayable transitions, optimistic updates, or concurrency races. | `Route -> ViewModel/Store -> Reducer -> Effects/UseCases` |

Do not add use cases, repositories, reducers, or modules only for ceremony. Add
them when they isolate a real product rule, side effect, or test boundary.

## Edge-To-Edge And IME Insets

Compose screens should handle edge-to-edge and keyboard overlap explicitly:

- Call `enableEdgeToEdge()` from the owning `Activity.onCreate()` before
  `setContent` when the app should draw behind system bars. Treat this as the
  default path for modern fullscreen/edge-to-edge Compose screens, especially
  for apps targeting Android 15/API 35 or higher.
- Do not confuse edge-to-edge with immersive mode. `enableEdgeToEdge()` lets
  content draw behind transparent or translucent system bars; hiding system bars
  is a separate immersive-mode decision.
- Configure the Activity with `android:windowSoftInputMode="adjustResize"` when
  the screen needs IME insets so Compose can resize or pad content as the
  software keyboard appears and disappears.
- Use `Modifier.imePadding()` on the screen container, scroll container, or
  bottom action area that must move above the software keyboard. Do not rely on
  fixed `Dp` keyboard spacers or legacy `adjustResize` behavior alone.
- Prefer Compose inset modifiers such as `safeDrawingPadding`,
  `windowInsetsPadding`, `windowInsetsBottomHeight`, and `imePadding` over
  hand-rolled system bar or keyboard measurements. Avoid double-applying insets
  across parent and child layouts.
- For `LazyColumn` or other scrolling forms, verify the focused text field and
  bottom actions remain visible while the IME opens. Use inset-sized bottom
  spacers when needed instead of only `contentPadding`.
- Keep tappable controls and gesture targets out of unsafe system gesture areas
  unless the product intentionally owns that interaction and verifies it on
  gesture navigation and 3-button navigation.

## Preview Rule

Every new or meaningfully changed screen, section, or reusable component needs a
Compose preview unless the repo has a stronger screenshot test that covers it.

Previews should:

- Target stateless composables, not ViewModel-backed holders.
- Use deterministic sample state from a `preview`, `sample`, or `fixture` owner.
- Cover the changed states: at least content plus loading, empty, error,
  permission denied, offline, long text, or disabled when affected.
- Wrap content in the app theme or design-system theme.
- Avoid network, database, DI containers, real credentials, random data, current
  time, or device-only services.
- Stay small enough that agents and reviewers can quickly understand the visual
  contract.

If a preview cannot be created, state why and name the replacement verification
such as a screenshot test, Compose UI test, or manual smoke path.

## Package Structure

Use package names that reveal ownership and dependency direction. A typical
feature implementation can use:

```text
feature/<name>/impl/src/main/.../<name>/
  <Name>Route.kt        stateful holder and lifecycle wiring
  <Name>Screen.kt       stateless screen content
  <Name>ViewModel.kt    UI state owner
  <Name>UiState.kt      state, actions, effects, UI models
  components/           feature-local reusable pieces
  preview/              sample UI states and preview fixtures
```

Use `components/` for feature-local pieces and promote only stable visual
contracts to a shared design-system module. Shared design-system modules can use:

```text
core/designsystem/.../theme/
core/designsystem/.../component/
core/designsystem/.../component/<domain-free-group>/
```

Keep generated resources, route contracts, domain models, repositories, and fake
services outside shared UI component packages unless the repo documents a more
specific boundary.

## Component API Rules

- `modifier: Modifier = Modifier` belongs near the top of public composable
  parameters and should be applied to the root layout exactly once.
- Prefer plain values, immutable UI models, callbacks, and slots.
- Use slots for caller-owned icons, actions, media, and trailing content when
  visual structure is reusable but content varies.
- Keep default parameters simple and side-effect free.
- Do not pass full `UiState` into leaf components when a smaller model or value
  set is enough.
- Do not make leaf components depend on ViewModel, repository, router, Activity,
  Context side effects, or DI.
- Accessibility labels, roles, selected states, enabled states, and content
  descriptions are part of the component contract.

## Reuse Decision

Before moving Compose UI into a shared package, ask:

- Is this a design-system primitive, a feature product component, or just a local
  screen section?
- Can the component be named without the original screen or feature name?
- Are product copy, route events, analytics, permissions, and business rules
  still owned by the caller?
- Can previews demonstrate the reusable states without feature setup?
- Will extraction reduce duplicated fixes without creating a flag-heavy API?

If the answer is no, keep it local or in feature common rather than promoting it
to the design system.

## Verification

Choose the closest checks configured in the repo:

- compile check for changed modules
- ViewModel/state unit test for state transitions
- Compose UI test for interaction, semantics, and navigation events
- screenshot or preview validation for visual component changes
- accessibility check for labels, roles, focus order, touch targets, and text
  scaling when affected

Review the final diff for direct repository calls from UI, missing previews,
stateful logic inside leaf components, and shared components that absorbed
product-specific behavior.
