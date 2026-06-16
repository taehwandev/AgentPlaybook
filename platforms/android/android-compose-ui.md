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

For feature module boundaries, `api`/implementation splits, package ownership,
and shared holder/design-system promotion, also read
`android-module-structure.md`.

For Compose performance, stability, modifier, effect, slot, focus, animation,
and testing work that cites external skill repositories, also read
`android-external-skill-source-coverage.md` before editing or reviewing.

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
- Each layer should pass the smallest stable model or value set needed by the
  next layer. Avoid sending a whole screen `UiState` into sections and leaf
  components when a narrower value keeps recomposition and ownership clearer.

## Stateful And Stateless

Stateful composables:

- End with `Route`, `Host`, or another repo-local holder suffix when possible.
- Collect `StateFlow` with lifecycle-aware APIs.
- Own lifecycle-aware effects for one-off commands such as navigation,
  snackbar, focus, permission launch, or external activity launch.
- Prefer `LifecycleEventEffect` for a single lifecycle callback,
  `LifecycleStartEffect` for `ON_START`/`ON_STOP` work with cleanup, and
  `LifecycleResumeEffect` for `ON_RESUME`/`ON_PAUSE` work with cleanup. Use
  `LaunchedEffect` when the coroutine is tied only to composition lifetime and
  does not need a lifecycle start/stop boundary.
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
- Keep state reads as close as practical to the composable that needs them. A
  screen can branch on high-level status, but repeated rows and leaf components
  should receive row models or plain values.

## Route And Screen Template

For a ViewModel-backed Compose screen, generate or review both the holder and the
stateless screen. Replace `hiltViewModel()` with the repo's DI pattern.

```kotlin
@Composable
fun ProfileRoute(
    onBack: () -> Unit,
    onOpenEditor: (ProfileId) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ProfileViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }

    LifecycleStartEffect(viewModel) {
        val collectJob = this.lifecycleScope.launch {
            viewModel.effects.collect { effect ->
                when (effect) {
                    ProfileEffect.NavigateBack -> onBack()
                    is ProfileEffect.OpenEditor -> onOpenEditor(effect.id)
                    is ProfileEffect.ShowSnackbar -> {
                        snackbarHostState.showSnackbar(effect.message.text)
                    }
                }
            }
        }

        onStopOrDispose {
            collectJob.cancel()
        }
    }

    ProfileScreen(
        state = state,
        onAction = viewModel::onAction,
        snackbarHostState = snackbarHostState,
        modifier = modifier,
    )
}
```

```kotlin
@Composable
fun ProfileScreen(
    state: ProfileUiState,
    onAction: (ProfileAction) -> Unit,
    modifier: Modifier = Modifier,
    snackbarHostState: SnackbarHostState = remember { SnackbarHostState() },
) {
    Scaffold(
        modifier = modifier,
        snackbarHost = { SnackbarHost(snackbarHostState) },
    ) { contentPadding ->
        when (val status = state.status) {
            ProfileStatus.Loading -> ProfileLoading(
                modifier = Modifier.padding(contentPadding),
            )
            ProfileStatus.Empty -> EmptyState(
                onRetryClick = { onAction(ProfileAction.RetryClick) },
                modifier = Modifier.padding(contentPadding),
            )
            is ProfileStatus.Error -> ErrorState(
                message = status.message,
                onRetryClick = { onAction(ProfileAction.RetryClick) },
                modifier = Modifier.padding(contentPadding),
            )
            ProfileStatus.PermissionDenied -> PermissionDeniedState(
                modifier = Modifier.padding(contentPadding),
            )
            is ProfileStatus.Content -> ProfileContent(
                profile = status.profile,
                canEdit = state.canEdit,
                onBackClick = { onAction(ProfileAction.BackClick) },
                onEditClick = { onAction(ProfileAction.EditClick) },
                modifier = Modifier.padding(contentPadding),
            )
        }
    }
}
```

Rules for applying this template:

- `Route` may know ViewModel, lifecycle collection, navigation outputs,
  permission launchers, activity results, and snackbar/focus effects.
- `Screen` must be previewable without DI, ViewModel, navigation, database,
  network, or platform services.
- Leaf components should receive the smallest model or values they need, not the
  whole screen `UiState`.
- If a callback count becomes noisy, introduce a typed `UiAction`; do not pass a
  ViewModel into the screen to reduce parameters.
- Keep `modifier` on the public composable and apply it to the root layout once.

## Compose Code Writing Rules

Write Compose code so state ownership, recomposition boundaries, and preview
contracts are visible in the function signature:

- Prefer one public or internal `Route` plus one public or internal stateless
  `Screen`; keep helper sections and leaf components private until another
  caller proves a reusable contract.
- Keep public composable parameters ordered as stable inputs, callbacks or
  slots, `modifier`, then optional visual defaults. Follow the repo's local
  ordering when it is stricter.
- Avoid reading `ViewModel`, DI, `LocalContext`, `LocalActivity`, `NavController`,
  or service locators below the route/holder boundary. If a platform value is
  required by a leaf, pass a plain value or callback instead.
- Use `remember` for UI-local objects, expensive calculations, gesture or
  animation state, and stable wrappers. Do not wrap every expression in
  `remember`; cheap derived values can be recomputed.
- Use `derivedStateOf` only when a derived value is expensive or changes less
  often than its inputs and can reduce real recomposition work.
- Use `rememberUpdatedState` for callbacks or values captured by long-lived
  `LaunchedEffect`, `LifecycleEventEffect`, `LifecycleStartEffect`,
  `LifecycleResumeEffect`, `DisposableEffect`, or animation callbacks.
- Use `DisposableEffect` for external listeners, receivers, observers, or
  platform callbacks that need explicit registration and cleanup. Prefer
  lifecycle-compose effects when the cleanup is tied to `ON_STOP` or
  `ON_PAUSE`.
- Register listeners, receivers, observers, and platform callbacks from an
  effect with a matching dispose path. Do not create heavy platform resources
  from a composable body without a clear owner and release point.
- Defer high-frequency state reads as far down the tree as practical. Prefer a
  lambda or lambda-based modifier when a parent only needs to pass a changing
  value to a child and should not recompose for every frame.
- Key effects by the lifecycle owner or the specific input that should restart
  the effect. Avoid broad keys such as a whole `UiState` unless the whole state
  should restart the work.
- Do not write to Compose state from a composable body in response to the state
  value read earlier in that same composition. Put that transition in a callback,
  effect, state holder, or reducer so recomposition does not loop.
- For `LazyColumn`, `LazyRow`, pager, and grid content, provide stable `key` and
  `contentType` when items can reorder, update independently, animate, or hold
  local state.
- Keep row item models stable and immutable. Avoid constructing a new mutable
  list, random id, formatter, painter, or callback wrapper for every item during
  every recomposition.
- Keep layout dimensions stable for repeated cells, navigation items, controls,
  and animated surfaces. Dynamic content should not resize the whole control
  unless the product intentionally owns that layout shift.

## Compose Performance Gate

Use a measure-first loop for Compose performance work:

```text
Measure -> Diagnose -> Fix one cause -> Verify
```

Do not call a change a performance fix only because it adds packages,
annotations, `remember`, module splits, or a different architecture pattern.
Record the bottleneck category first: recomposition, stability, lazy layout,
main-thread work, startup, allocation, subcomposition, side effects, tracing,
or release configuration.

Performance claims should use release-like evidence whenever practical:

- Measure Compose runtime behavior in a release or benchmark variant with R8
  enabled and a physical device when the claim is about frame time, jank,
  startup, or scroll smoothness. Debug builds, emulators, and Layout Inspector
  counts are diagnostic only unless the report says so.
- Quote the variant, device, compilation mode, iteration count, and before/after
  numbers when reporting a measured improvement.
- Use compiler reports, Layout Inspector, recomposition tracing,
  Macrobenchmark, Baseline Profiles, Perfetto, or focused manual evidence
  according to the repo's tooling. Do not invent metrics.
- Keep each fix scoped to one diagnosed cause and remeasure before moving to the
  next optimization.

### Stability And Strong Skipping

- Check the Kotlin and Compose compiler versions before changing stability
  policy. Newer Kotlin/Compose toolchains may enable strong skipping by
  default; do not add configuration without verifying the current behavior.
- Stability annotations are contracts. Use `@Immutable` or `@Stable` only for
  owned types whose public properties, equality behavior, and mutation rules are
  defensible.
- Prefer immutable collections or stable UI wrappers before adding a stability
  configuration entry. Stability config is a codebase-wide promise, not a local
  patch.
- Pure Kotlin/data modules that need Compose stability markers should use the
  official runtime annotation artifact or an approved repo-local marker pattern
  without depending on the full Compose runtime.
- `Flow`, channels, repositories, platform objects, and mutable collections are
  not stable UI state. Collect, map, or wrap them before they enter composable
  parameters.
- Use `@NonSkippableComposable`, `@DontMemoize`, or similar escape hatches only
  with a nearby reason and measured need.

### State Reads And Effects

- Use `remember { derivedStateOf { ... } }` only when inputs change more often
  than the derived output or the calculation is meaningfully expensive. Include
  changing non-state captures in the `remember` key list.
- Prefer upstream `distinctUntilChanged`, `conflate`, or state mapping for
  chatty flows. Do not wrap `collectAsStateWithLifecycle()` output in
  `derivedStateOf` just to appear safe.
- Do not pass `Flow<T>` as a composable parameter. Collect lifecycle-aware at
  the route/holder boundary and pass values, state holders, or callbacks down.
- Choose the smallest side-effect API: `SideEffect` to publish after successful
  recomposition, `DisposableEffect` for register/unregister work,
  `LaunchedEffect` for keyed suspending work, `rememberCoroutineScope` for
  user-event launched work, and `snapshotFlow` for Compose state reads that
  drive Flow-based side effects.
- Key long-lived effects by the semantic lifecycle that should restart the
  work. Avoid `Unit` or a whole `UiState` key when individual inputs determine
  the lifecycle.
- Use `rememberUpdatedState` only to provide the latest callback or value to a
  long-lived effect without restarting it. Do not read it eagerly inside
  `remember { ... }`.
- Never use a remembered boolean event flag as a one-off effect queue. Emit a
  callback, command, event flow, or route effect from the state holder.

### Lazy Layouts And Subcomposition

- Every domain-backed lazy item should have a stable key from server/domain data
  rather than an index, random value, or mutable `hashCode`.
- Use `contentType` for heterogeneous lazy lists so item composition can be
  reused by shape.
- `Modifier.animateItem()` requires stable keys and stable item identity.
- Hoist expensive item allocations, painters, shapes, formatters, and mappers
  out of lazy item lambdas when measurement shows churn. Do not blindly
  `remember` cheap modifier chains.
- Avoid nested lazy layouts, `BoxWithConstraints`, nested `Scaffold`, and other
  subcomposition-heavy containers inside repeated lazy items unless the
  behavior requires them and the cost is measured.
- Configure lazy prefetch only for a real scroll bottleneck and verify with a
  release-like scroll measurement.

### Modifiers, Slots, Focus, And Animation

- Public composables that emit layout must expose `modifier: Modifier =
  Modifier` and apply it to the root once. Caller placement such as outer
  padding, width fill, or alignment usually belongs to the caller.
- Build modifier chains as one fluent value. Avoid mutable modifier variables
  and avoid hiding parent layout decisions inside leaf components.
- New custom modifiers should prefer `Modifier.Node` over legacy
  `Modifier.composed` unless the repo's Compose version or API surface prevents
  it.
- Use slot APIs for caller-owned icons, actions, media, supporting content, and
  trailing content. Optional slots should be nullable when absence should not
  reserve space.
- Pick the smallest animation API: `animate*AsState` for one value,
  `updateTransition`/`rememberTransition` for synchronized values,
  `AnimatedVisibility` when the subtree should mount/unmount, and alpha or draw
  changes when the subtree should remain mounted. Use `contentKey` for
  `AnimatedContent` by visual shape.
- Focusable controls should have explicit focus targets, stable ids in lazy
  lists, and tests for keyboard/D-pad/key input when focus behavior changes.

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

## Stability And Recomposition

Compose performance starts with stable inputs. Treat stability annotations as a
model contract, not an optimization trick:

- In Compose-aware UI modules, annotate screen `UiState`, UI display models,
  component-default holders, and design-system token holders with `@Immutable`
  when all public properties are immutable.
- Annotate sealed marker interfaces with `@Stable` only when all implementations
  are stable or immutable. Annotate leaf implementations with `@Immutable`.
- Do not add Compose annotations to pure domain, repository, or shared model
  modules just for the UI. Keep those types free of Compose runtime and map them
  into annotated UI models at the feature or design-system boundary.
- Use immutable collections for state that enters Compose. Prefer
  `ImmutableList` and persistent collection builders when the repo already uses
  `kotlinx.collections.immutable`.
- Avoid mutable properties, mutable collections, raw platform objects,
  repositories, flows, channels, and callbacks inside `UiState`.
- Keep painter, icon, resource, `Color`, `Dp`, and typography decisions in UI
  display models or design-system tokens, not domain models.
- If state can refresh while showing stale content, model that explicitly
  instead of layering `isLoading`, `error`, and nullable data in contradictory
  combinations.

When a screen still recomposes too broadly, inspect first instead of guessing:

- Check whether the same large `UiState` is passed into many sections.
- Check whether item models, keys, callbacks, or lists are recreated on every
  recomposition.
- Check whether a local state read was hoisted higher than necessary.
- Check whether the component API forces unstable product objects into a shared
  primitive.

## Advanced Stability Options

Use compiler and Gradle-level stability tools only after diagnosing a real
recomposition or performance issue:

- Check Compose compiler reports, Layout Inspector, benchmark traces, or another
  repo-local measurement before changing stability policy.
- Strong skipping is a compiler behavior, not a replacement for good state
  modeling. Check the repo's Kotlin/Compose compiler version before adding any
  explicit strong-skipping configuration, because newer toolchains may enable it
  by default.
- A Compose stability configuration file can mark external or standard-library
  types as stable, but it is a codebase-wide contract. Add entries only for
  types whose immutability and equality behavior the project can defend.
- If normal `List`, `Set`, or `Map` parameters keep a composable unstable, first
  prefer immutable collections or a small annotated wrapper in the UI boundary.
  Do not annotate a mutable collection holder only to silence compiler output.
- Use `@NonSkippableComposable` or equivalent opt-outs only when a composable has
  a deliberate side-effect or measurement contract that must run even with
  unchanged inputs, and document the reason near the call or component.
- Do not change compiler stability policy, add stability configuration, or move
  state across component boundaries without measurement or a concrete
  recomposition/jank reproduction.
- Do not use suspected performance as the reason to migrate a View screen to
  Compose, or a Compose screen back to View. Treat framework migration as a
  separate architecture task with its own evidence.
- Do not call feature-specific state, copy, routing, analytics, or permission
  policy a performance optimization by hiding it inside a shared component.

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

## Preview Implementation

Previews should be built from the stateless `Screen` or leaf component, with
sample state owned by a preview fixture. Keep sample data deterministic and
domain-safe.

```kotlin
private object ProfilePreviewData {
    val content = ProfileUiState(
        status = ProfileStatus.Content(
            ProfileViewData(
                id = ProfileId("preview"),
                name = "Ada Lovelace",
                subtitle = "Long subtitle that verifies wrapping and spacing",
                avatarUrl = null,
            ),
        ),
        canEdit = true,
    )

    val loading = ProfileUiState(status = ProfileStatus.Loading)
    val empty = ProfileUiState(status = ProfileStatus.Empty)
    val error = ProfileUiState(
        status = ProfileStatus.Error(UiMessage("Unable to load profile")),
    )
}

@Preview(name = "Profile content")
@Composable
private fun ProfileScreenContentPreview() {
    AppTheme {
        ProfileScreen(
            state = ProfilePreviewData.content,
            onAction = {},
        )
    }
}

@Preview(name = "Profile error")
@Composable
private fun ProfileScreenErrorPreview() {
    AppTheme {
        ProfileScreen(
            state = ProfilePreviewData.error,
            onAction = {},
        )
    }
}
```

Preview requirements:

- Add at least one content preview and one affected edge-state preview when the
  change touches loading, empty, error, permission, offline, disabled, or long
  text behavior.
- Add dark mode, font scale, small-width, or locale previews when the change is
  likely to break them and the repo already supports preview parameters or
  screenshot coverage.
- Keep preview data in `preview/`, `sample/`, or the same file for small local
  components according to repo convention.
- Do not create a fake ViewModel only to make a preview work. Preview the
  stateless composable instead.
- Do not hide missing previews behind "not runnable locally" unless a screenshot
  test, Compose UI test, or manual smoke path covers the visual state.

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
core/designsystem/.../tokens/
core/designsystem/.../component/
core/designsystem/.../component/<domain-free-group>/
core/designsystem/.../preview/
```

Keep generated resources, route contracts, domain models, repositories, and fake
services outside shared UI component packages unless the repo documents a more
specific boundary.

Design-system modules should own theme, semantic tokens, typography, shapes,
component defaults, accessibility semantics, and domain-free primitives. Feature
modules should own product copy, route events, analytics labels, permission
policy, domain-to-UI mapping, and feature-only cards or sections.

When a repo has design-system wrappers, feature modules should prefer those
wrappers over direct Material, platform, or third-party UI primitives. Direct
imports of raw UI primitives belong primarily inside the design system, or in a
feature-local one-off with a clear reason to avoid promotion.

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
- Defaults objects such as `FooButtonDefaults`, `FooCardDefaults`, and token
  holders should be stable or immutable and should read theme values through
  composable getters only when the value is theme-dependent.

## Reuse Decision

Before moving Compose UI into a shared package, ask:

- Is this a design-system primitive, a feature product component, or just a local
  screen section?
- Can the component be named without the original screen or feature name?
- Are product copy, route events, analytics, permissions, and business rules
  still owned by the caller?
- Can previews demonstrate the reusable states without feature setup?
- Will extraction reduce duplicated fixes without creating a flag-heavy API?
- Does the shared API use semantic tokens and slots instead of leaking one
  feature's exact colors, padding, copy, or route policy?

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
