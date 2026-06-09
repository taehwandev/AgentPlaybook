---
keyflow_id: sys_android_viewmodel_state
status: review
type: human-reviewed-needed
---

# Android ViewModel And State

Use when creating, changing, moving, or reviewing Android ViewModels, `UiState`,
`Flow`, use cases, repositories, persistence, permission state, or navigation
events.

For Compose screen/component structure, also read `android-compose-ui.md`. For
background work, also read `android-background-work.md`. For reusable extraction,
also read `../../common/reusable-code-design.md`.

## State Ownership

Use this shape unless the repo has a stricter local pattern:

```text
Route/Composable -> ViewModel -> Use Case -> Repository -> DataSource/Adapter
```

- Route/Composable collects state, sends user intent, and handles lifecycle-aware
  UI effects.
- ViewModel owns screen state, user intent handling, cancellation, and event
  output.
- Use case owns product rules and orchestration when logic is reused, risky, or
  independently testable.
- Repository owns source coordination, caching, DTO/domain mapping, and error
  normalization.
- Data sources/adapters own Room, DataStore, files, sensors, permissions,
  notifications, SDKs, and network clients.

Do not add a use case or repository only as a pass-through. Add it when it
protects a product rule, side effect, test boundary, cache boundary, or platform
API boundary.

## State Holder Selection

Choose the state holder by logic scope:

- Use local `remember` state for simple UI element state owned by one composable,
  such as expanded, focused, selected tab, gesture, animation, and scroll state.
- Use a plain UI state holder class when UI logic is complex but lifecycle
  dependent and does not need business/data-layer work. Examples include drawer,
  pager, sheet, text-field formatter, drag/drop, and focus orchestration.
- Use `ViewModel` when screen state is produced from data/domain layers, must
  survive configuration changes, handles user actions that affect app data, or
  emits navigation and platform effects.
- Use a reducer/store when the transition graph is complex enough that actions,
  state transitions, and effects should be testable without Android framework
  objects.

If a plain UI state holder needs data or domain information, pass the required
stable values from the ViewModel or screen state. Do not make lifecycle-dependent
UI logic depend directly on repositories or long-lived business state.

## ViewModel Contract

ViewModels should expose one observable state stream and explicit intent methods
or typed actions:

```kotlin
@Immutable
data class ProfileUiState(
    val content: ProfileViewData? = null,
    val status: LoadStatus = LoadStatus.Loading,
    val permission: PermissionState = PermissionState.Unknown,
    val isSubmitting: Boolean = false,
)

sealed interface ProfileAction {
    data object Retry : ProfileAction
    data object Edit : ProfileAction
    data object DismissMessage : ProfileAction
}
```

Rules:

- Prefer immutable `data class` or sealed state over scattered `MutableState`
  and nullable fields.
- Keep `MutableStateFlow` private and expose `StateFlow`.
- Use lifecycle-aware collection from UI.
- Convert DTO/domain models into UI models before state reaches Compose.
- Keep permission denied, offline, empty, loading, error, disabled, and submitted
  states representable when the flow can reach them.
- Keep one-off effects separate from persistent state. Use a typed effect stream
  or route callback for navigation, snackbar, permission launch, external
  activity, and file/share actions.

## Feature Actions, Feedback, And I18n Text

Feature events should stay feature-owned. Do not create one global action type
for unrelated screens, and do not make a reusable feedback model carry a generic
action payload. Actions are UI intents/events, similar to reducer or React-style
actions: clicks, retries, dismissals, item selections, and form changes are
modeled as feature-specific sealed values.

```kotlin
sealed interface InboxAction {
    data object Refresh : InboxAction
    data object RetryLoadClick : InboxAction
    data object DismissFeedbackClick : InboxAction
    data class MessageClick(val item: InboxMessageItem) : InboxAction
}
```

In Compose, pass one dispatch function down from the stateful route to the
stateless screen or components. The screen emits actions; the ViewModel handles
them:

```kotlin
@HiltViewModel
class InboxViewModel @Inject constructor() : ViewModel() {
    fun send(action: InboxAction) {
        when (action) {
            InboxAction.Refresh -> refresh()
            InboxAction.RetryLoadClick -> retryLoad()
            InboxAction.DismissFeedbackClick -> dismissFeedback()
            is InboxAction.MessageClick -> openMessage(action.item)
        }
    }
}

@Composable
fun InboxRoute(viewModel: InboxViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    InboxScreen(
        state = state,
        onAction = viewModel::send,
    )
}

@Composable
private fun InboxScreen(
    state: InboxUiState,
    onAction: (InboxAction) -> Unit,
) {
    InboxMessageList(
        items = state.messages,
        onMessageClick = { item -> onAction(InboxAction.MessageClick(item)) },
        onRetryClick = { onAction(InboxAction.RetryLoadClick) },
    )
}
```

Keep user-visible text localizable at the UI/resource boundary. ViewModels may
emit Android string resource ids, such as `R.string.retry`, as stable message
keys when the repo uses that convention. They should not resolve those ids with
`Context`, `Resources`, `getString()`, or `stringResource`, and should not
hardcode user-visible copy. The Route, Activity, Fragment, or Composable
renderer resolves message keys into localized platform resources. Safe server
fallback messages may be carried as values only when the app's error policy
allows them.

Keep feature-owned copy in the module that owns the screen, and promote only
repeated generic copy to a design-system or app-ui resource owner. A dedicated
resources module is optional, not a default; naming prefixes, review rules, and
translation export can provide centralized management without turning one
resource module into a catch-all dependency.

Toast-like effects are poor retry surfaces because they cannot reliably own
actions. Use snackbar, banner, dialog, alert, or full-page error effects when
the user needs retry, dismiss, confirm/cancel, or an alternative action.
Feedback buttons are UI triggers; they should dispatch the relevant feature
action through `onAction(InboxAction.RetryLoadClick)` or `viewModel.send(...)`
instead of becoming part of the action model itself. The renderer should not run
business logic directly.

## UiState Stability Contract

For Compose-observed state, make stability an explicit contract instead of an
afterthought:

- In Compose-aware UI modules, annotate top-level screen state and display-model
  data classes with `@Immutable` when every public property is immutable and
  equality represents the visible state.
- Annotate sealed UI-state marker interfaces such as `FooStatus` or `FooUiItem`
  with `@Stable` only when every implementation keeps the same stability
  contract. Annotate leaf data classes or data objects with `@Immutable`.
- Actions and effects can stay unannotated unless repo-local convention uses
  annotations for Compose-visible UI contracts. They should still be immutable
  value objects.
- Do not add Compose runtime annotations to pure domain, repository, or model
  modules only to satisfy UI stability. Keep those modules structurally immutable,
  then map to annotated UI models in the feature or design-system boundary.
- Avoid `var`, mutable collections, mutable maps, arrays, raw SDK objects,
  unguarded `Context`, `Activity`, `NavController`, `CoroutineScope`, or
  repository references inside `UiState`.
- Use immutable or persistent collections for lists that cross into Compose,
  especially high-churn `LazyColumn` or `LazyRow` models. If the repo uses
  `kotlinx.collections.immutable`, prefer `ImmutableList` plus `persistentListOf`
  for default states and mapper output.
- Keep callbacks and one-off commands out of `UiState`. Actions and effects are
  separate contracts.
- Treat `@Stable` and `@Immutable` as promises to the Compose compiler, not lint
  suppressions. Remove the annotation or fix the model when the promise is false.

Prefer deterministic default state owned by the state model or preview fixture:

```kotlin
@Immutable
data class ProfileUiState(
    val status: ProfileStatus = ProfileStatus.Loading,
    val items: ImmutableList<ProfileRow> = persistentListOf(),
    val canEdit: Boolean = false,
)

@Stable
sealed interface ProfileStatus {
    data object Loading : ProfileStatus

    @Immutable
    data class Content(val profile: ProfileViewData) : ProfileStatus

    @Immutable
    data class Error(val message: UiMessage) : ProfileStatus
}
```

## Implementation Pattern

Use repo-local naming and DI first, but keep this contract intact:

```kotlin
@Immutable
data class ProfileUiState(
    val status: ProfileStatus = ProfileStatus.Loading,
    val canEdit: Boolean = false,
)

@Stable
sealed interface ProfileStatus {
    data object Loading : ProfileStatus
    data object Empty : ProfileStatus
    @Immutable
    data class Content(val profile: ProfileViewData) : ProfileStatus
    @Immutable
    data class Error(val message: UiMessage) : ProfileStatus
    data object PermissionDenied : ProfileStatus
}

sealed interface ProfileAction {
    data object RetryClick : ProfileAction
    data object BackClick : ProfileAction
    data object EditClick : ProfileAction
}

sealed interface ProfileEffect {
    data object NavigateBack : ProfileEffect
    data class OpenEditor(val id: ProfileId) : ProfileEffect
    data class ShowSnackbar(val message: UiMessage) : ProfileEffect
}
```

```kotlin
class ProfileViewModel(
    private val loadProfile: LoadProfileUseCase,
) : ViewModel() {
    private val _state = MutableStateFlow(ProfileUiState())
    val state: StateFlow<ProfileUiState> = _state.asStateFlow()

    private val _effects = Channel<ProfileEffect>(Channel.BUFFERED)
    val effects: Flow<ProfileEffect> = _effects.receiveAsFlow()

    fun onAction(action: ProfileAction) {
        when (action) {
            ProfileAction.RetryClick -> load()
            ProfileAction.BackClick -> emitEffect(ProfileEffect.NavigateBack)
            ProfileAction.EditClick -> openEditor()
        }
    }

    private fun load() {
        viewModelScope.launch {
            _state.update { it.copy(status = ProfileStatus.Loading) }
            // Map domain result into typed UI state, including empty/error.
        }
    }

    private fun openEditor() {
        val content = _state.value.status as? ProfileStatus.Content ?: return
        emitEffect(ProfileEffect.OpenEditor(content.profile.id))
    }

    private fun emitEffect(effect: ProfileEffect) {
        viewModelScope.launch { _effects.send(effect) }
    }
}
```

Implementation rules:

- Keep action handling centralized in the ViewModel or reducer; do not scatter
  business actions across composables.
- Use `Channel`/`receiveAsFlow`, `SharedFlow`, or repo-local event primitives
  intentionally. Effects should not replay after rotation unless replay is the
  product contract.
- Convert repository/domain errors into typed UI messages or state. Do not pass
  raw exceptions to Compose.
- For `suspend` API calls, do not make sealed `Success/Failure` network results
  the default shape only to re-wrap exceptions. Let successful suspend calls
  return the value, normalize library-specific HTTP responses at the network or
  API boundary, and throw typed transport/protocol/domain exceptions for failure.
  The ViewModel or reducer should catch those typed failures and map them to
  screen state or one-off effects.
- When a Retrofit or HTTP stack exposes raw response handles, prefer a
  `CallAdapter`, client interceptor, or API boundary adapter that centralizes
  success, non-2xx, empty body, body conversion failure, network failure, and
  cancellation handling. Do not spread the same response parsing and exception
  wrapping across every repository method.
- Preserve cancellation semantics. Cancellation should escape as cancellation,
  not become a generic user-visible failure or retryable network error.
- If the server returns presentation hints such as toast/banner, alert/dialog,
  full-page error, retry metadata, or a deep-link action, treat them as an API
  contract hint. The ViewModel maps supported hints into Compose state/effects;
  the feature UI should not parse raw server envelopes or transport responses.
- Put required content data inside the `Content` state, or use another explicit
  state shape when stale content can coexist with refresh/error. Avoid nullable
  payloads that contradict the status.
- Prefer a single `onAction(ProfileAction)` surface when a screen has many
  events. Explicit callbacks are fine for small screens.
- Persist only durable inputs needed for process recreation. Do not persist
  snackbars, transient navigation effects, or one-frame UI commands.

## Flow And Coroutine Rules

- Use `viewModelScope` for work owned by the ViewModel.
- Use `viewModelScope.launch { ... }` for one-shot suspend work such as loading,
  submit, retry, or save actions.
- Use `onEach { ... }.launchIn(viewModelScope)` for long-lived Flow
  subscriptions owned by the ViewModel, such as event buses, repositories, or
  platform callbacks that should keep collecting while the ViewModel is active.
- Use `stateIn(viewModelScope, started, initial)` when a Flow is transformed
  into UI-observed `StateFlow`; do not use `launchIn` only to copy Flow values
  into mutable UI state when `stateIn` can express the state owner directly.
- Inject dispatchers, clocks, and schedulers when tests need control.
- Cancel or replace in-flight work when query, account, permission, or route
  arguments change.
- Suppress stale results from older requests.
- Use `stateIn` or `shareIn` intentionally; define initial value, sharing
  policy, and stop timeout.
- Avoid collecting infinite flows inside use cases without a clear owner.
- Map errors into user-visible state or typed domain errors before UI.

## Persistence And Cache

- Room entities, DataStore schemas, files, and cache records should not leak
  directly into UI state.
- Version persisted data that can survive app upgrades.
- Define cleanup on logout, account switch, org/workspace change, permission
  revoke, and downgrade.
- Define invalidation for offline caches and remote refresh.
- Handle corrupt DataStore/files, failed migrations, missing permissions, and
  storage quota or disk errors.

## Navigation And Events

- Parse navigation arguments at the route boundary and pass typed values to the
  ViewModel.
- Do not hide route decisions in random booleans inside `UiState`.
- Navigation, snackbar, permission prompt, file picker, and external app launch
  should be explicit outputs from the state owner.
- Events must not replay after rotation unless replay is the intended behavior.

## Tests

Choose the closest checks configured in the repo:

- ViewModel tests for state transitions, retry, submit, permission denied,
  stale result suppression, and one-off effects.
- Reducer or action tests when the feature uses MVI-style state transitions.
- Use case tests for product rules, auth/tenant/billing policy, and side-effect
  orchestration.
- Repository tests for cache, mapper, error, migration, and source selection.
- Coroutine tests with injected dispatchers and deterministic clocks.
- Compose UI tests for lifecycle collection, rendering state, and emitted
  actions.

Review the final diff for direct data-source calls from UI, public mutable
state, impossible UI state combinations, replaying one-off events, missing
logout cleanup, and untested coroutine timing.
