---
keyflow_id: sys_android_module_structure
status: review
type: human-reviewed-needed
---

# Android Module Structure

Use when deciding Android Gradle modules, package layout, `api`/implementation
splits, feature ownership, build convention plugins, or where new code should
live.

This card follows current Android guidance: modularization is a tool for
maintainability, build isolation, visibility control, and replaceable
boundaries; it is not mandatory ceremony for every feature.

References:

- Android app modularization:
  `https://developer.android.com/topic/modularization`
- Android app architecture:
  `https://developer.android.com/topic/architecture`
- Android UI layer:
  `https://developer.android.com/topic/architecture/ui-layer`

## Default Rule

Start with the smallest owner boundary that works:

```text
package/private file -> feature package -> feature module -> api/impl pair
-> api/impl/assertions trio -> shared core or core-app module
-> public SDK-like contract
```

Use a single package or module unless a real caller, dependency, build,
navigation, testing, or ownership boundary needs a split. Multi-module apps need
clear dependency direction; otherwise the extra modules only move complexity into
Gradle.

## File And Class Split

Apply `../../common/code-structure-ownership.md` before growing Android runtime
files. Kotlin and Java source should default to one primary public or internal
top-level class, interface, object, composable screen/state owner, repository,
adapter, mapper, fake, or assertion subject per file.

Split files before adding behavior when a feature file contains separate owners
such as route contract, `NavEntry` mapping, screen rendering, ViewModel,
UiState, repository contract, repository implementation, DTO mapper, platform
adapter, fixture, recorder, and assertion DSL.

Review must fail when an Android runtime file keeps multiple independently
importable Kotlin/Java owners in one file: classes, objects, interfaces,
ViewModels, repositories, services, mappers, validators, DI bindings, platform
adapters, fakes, fixtures, or assertion subjects.

Do not:

- Put a ViewModel, screen, route key, repository, mapper, and DI binding in one
  file because they all belong to one feature.
- Keep multiple importable Kotlin/Java classes or objects in one file unless
  they are a small sealed/value family with one caller-facing contract.
- Introduce Kotlin `typealias` in Android runtime code. In Kotlin 2.x, aliases
  remain alternative names for existing types rather than new contracts. Prefer
  named value classes, interfaces/fun interfaces, data classes, or explicit
  types so domain, route, callback, and platform contracts stay reviewable.
- Use nested classes, companion objects, or extension files to hide unrelated
  UI, state, data, platform, or testing responsibilities.
- Create one-folder-per-type module structure without changing import rules;
  split files first, then packages or modules only when ownership demands it.

## Package Boundary Artifact

Before creating or moving Android packages, source sets, modules, or
namespaces, write a package boundary note. It must name the owner, allowed
imports, forbidden imports, exported contracts, consumers, and focused
verification.

Android package splits fail review when they only mirror a reference app, create
one folder per type, or move every file into a new package without changing an
import rule. Prefer a flat cohesive package until behavior, dependency
direction, or test ownership requires another boundary.

For `api` / `impl` / `assertions` module families:

- `api` owns caller-facing contracts: route keys, deep-link specs, events,
  commands, public models, value types, repository ports, provider contracts,
  and entrypoint interfaces. Subpackage only when callers should import one
  contract family without seeing the others.
- `impl` owns execution: `NavEntry` or entry-provider builders, route-to-screen
  mapping, Activity launch adapters, ViewModels, screens, DI bindings, SDK
  adapters, mappers, and state holders. Subpackage by behavior owner or
  dependency, not by matching every API file.
- `assertions` owns reusable test contracts: fixtures, builders, recording
  fakes, assertion subjects, matchers, and contract tests. It depends on `api`
  and must not depend on production `impl` by default.

Minimal shape:

```text
feature/profile/api
  ProfileRoute.kt
  ProfileEvent.kt
  ProfileRepository.kt
  model/Profile.kt

feature/profile/impl
  ProfileRouteHolder.kt
  ProfileViewModel.kt
  ProfileScreen.kt
  mapper/ProfileUiMapper.kt
  di/ProfileModule.kt

feature/profile/assertions
  ProfileFixtures.kt
  RecordingProfileRepository.kt
  ProfileRouteSubject.kt
```

The `api` module exposes what callers need to compile. The `impl` module owns
how the feature runs. The `assertions` module owns reusable test helpers that
compile against `api` and avoid pulling app, DI, network, database, WebView,
camera, or other production implementations into tests.

Example API contract:

```kotlin
@JvmInline
value class ProfileId(val value: String)

data class ProfileRoute(val id: ProfileId)

sealed interface ProfileEvent {
    data class OpenProfile(val id: ProfileId) : ProfileEvent
    data object Back : ProfileEvent
}

interface ProfileRepository {
    suspend fun loadProfile(id: ProfileId): Profile
}
```

Example implementation boundary:

```kotlin
class ProfileViewModel(
    private val repository: ProfileRepository,
    private val noticeSink: NoticeSink,
    private val routeSink: RouteEventSink<ProfileEvent>,
) : ViewModel() {
    fun onAction(action: ProfileAction) {
        when (action) {
            ProfileAction.BackClick -> routeSink.tryEmit(ProfileEvent.Back)
            ProfileAction.RetryClick -> load()
        }
    }
}
```

Example assertions boundary:

```kotlin
class RecordingProfileRepository : ProfileRepository {
    val requestedIds = mutableListOf<ProfileId>()
    var nextProfile: Profile = ProfileFixtures.profile()

    override suspend fun loadProfile(id: ProfileId): Profile {
        requestedIds += id
        return nextProfile
    }
}

object ProfileFixtures {
    fun profile(id: ProfileId = ProfileId("profile-1")) = Profile(id = id)
}
```

Do not put the fake in the production implementation module only because it is
small. Once more than one test boundary needs it, move it to `assertions` so
tests can depend on the contract and fake without importing the production
screen, DI graph, network stack, or app module.

If the package note cannot explain who imports the package and which import is
forbidden, keep the code in the existing package and only split files by
responsibility.

For external Android skill source routing, also read
`android-external-skill-source-coverage.md`. That manifest is the no-omission
list for source `SKILL.md` and reference documents from the Android, Compose
performance, and Kotlin/Compose skill repositories.

## Reference Project Drill

When using a large Android reference app, copy the boundary lesson, not the
whole shape. Distill the reference into the current repo's scale:

- Keep transferable boundaries such as included `build-logic`, convention
  plugins, feature `api`/implementation splits, design-system modules,
  repository API/implementation splits, domain use cases, and deterministic fake
  or assertion modules.
- Rename plugin ids, packages, modules, and generated namespaces to the target
  repo. Never keep source-project names in shared build or source contracts.
- Drop source-only dependencies such as ads, billing, Firebase, Hilt, KSP,
  generated factories, signing, flavors, analytics, domain-specific SDKs, or
  verification tooling unless the current task explicitly needs them.
- Collapse deep reference folder hierarchies when the target has only one
  product area. A small app often needs `app`, `core:designsystem`,
  `core:model`, `core:domain`, `core:data`, and one feature module before it
  needs dozens of feature/common/holder modules.
- Treat reference code as evidence for module direction and package naming, not
  as authority over state, DI, security, or product policy when repo-local rules
  differ.

## Example-First Boundary Documentation

When a task uses a large reference app or external codebase to design Android
module structure, write an example packet before asking another agent to
implement the shape. The packet must be concrete enough that the agent can copy
the boundary pattern without inventing source names, packages, modules, or
missing contracts.

Include all of these fields:

```text
transferable lesson:
target boundary:
lowest acceptable ownership level:
minimal file/module sketch:
allowed imports:
forbidden imports:
first caller or test:
nearest verification:
collapse rule:
```

Example packet:

```text
transferable lesson: keep route contracts pure; execute Activity launches in runtime
target boundary: feature/settings/api + feature/settings/impl + core/route/runtime
lowest acceptable ownership level: feature-local until a second caller needs route data
minimal file/module sketch: SettingsRouteKey in api, SettingsRouteHolder in impl,
  ActivityRouteLauncher in runtime
allowed imports: api -> Kotlin value types; impl -> own api + Compose; runtime -> Android
forbidden imports: api -> Activity, Context, Intent, NavController, Compose UI
first caller or test: app route coordinator imports SettingsRouteKey only
nearest verification: compile api/impl/runtime and run route assertion tests
collapse rule: if no caller needs SettingsRouteKey without impl, keep one feature module
```

Stop instead of generating structure when the packet cannot name a real caller,
forbidden import, verification path, and collapse rule. In that case keep the
code local, add a TODO with the missing evidence, or ask for the source example
that proves the split. Do not fill gaps by copying a reference app's full module
tree, broad base classes, generated registries, DI graph, or source-specific
package names.

Use examples at these boundaries before creating shared modules:

| Boundary | Minimum Example Required | Collapse Or Stop When |
| --- | --- | --- |
| `feature-api` plus implementation | One route key/event or public port, one implementation file, one caller that should avoid implementation dependencies. | The API has no caller without the implementation. |
| Repository `api` plus implementation | One stable entity or repository port, one DTO/cache mapper kept inside implementation, one feature or use case caller. | Callers would still import DTOs, SDK types, or concrete data sources. |
| `assertions` module | Fixture, recording fake, and assertion subject that depend on `api` only. | Only one test needs the helper, or the fake imports production `impl`. |
| App-runtime helper | One small contract, one runtime adapter/host, and one caller that should not know Android/Compose details. | The helper starts owning product route policy, repositories, analytics, or screen state. |
| Activity/deep-link route execution | Pure route or plan object, runtime launcher or entry mapping, and explicit Back/Up/result expectation. | The design hides parsing, planning, and execution inside `BaseActivity`. |
| Convention plugin | Two modules sharing the same build setup and one before/after dependency sketch. | Only one module needs the setup or the plugin would encode product behavior. |

## Module Families

Use repo-local names first. A large Android app commonly separates these module
families:

| Family | Owns | Must Not Own |
| --- | --- | --- |
| `app` | Application class, build types/flavors, app-level DI graph, startup, top-level navigation wiring. | Feature implementation, repository implementation details, shared UI primitives. |
| `build-logic` | Convention plugins, common Android/Kotlin/Compose/test settings, dependency bundles. | Product behavior or runtime code. |
| `core` | Pure Kotlin or implementation-neutral contracts such as models, domain interfaces, route contracts, network contracts, dispatchers, resource-provider contracts, and test-support contracts. | Android/Compose runtime, feature product policy, or screen-specific UI. |
| `core-ui` / `core-app` / `core-runtime` | Android/Compose app-runtime commonization such as design system, resources, permission helpers, ActivityRoute launch adapters, WebView runtime, notice or alert hosts, toast/dialog rendering, and app UI infrastructure. | Feature-specific copy, route policy, analytics policy, or repository calls. |
| `data` / `core-data` | Repository contracts, repository implementations, local/remote data sources, DTO mapping, DataStore/Room/cache ownership. | Compose UI, navigation decisions, screen state. |
| `domain` | Optional use cases and product policies reused across screens or risky enough to test independently. | Pass-through wrappers around one repository call. |
| `feature-api` | Navigation contracts, public entrypoints, route data, events, small caller-facing models. | Screens, ViewModels, repository implementations, DI bindings with heavy dependencies. |
| `feature` / `feature-impl` | Route holders, stateless screens, ViewModels, feature-local components, UI mappers, feature DI. | Shared design primitives or cross-feature data contracts. |
| `feature-common` / `holder` | Reused product UI or workflow holders with a named owner and stable caller contract. | Dumping ground for unrelated screen fragments. |
| `dev` / `testing` / `assertions` | Dev-only screens, reusable fakes, recording adapters, fixture builders, assertion DSLs, and contract test helpers. | Production-only behavior that callers need at runtime, or dependencies on production implementation modules by default. |

## Core Is A Capability Namespace

Do not treat `core` as a promise that every module under it is pure Kotlin.
Treat it as a stable capability namespace whose Gradle plugin and dependencies
must match the capability it exports.

Choose the module type by import contract:

- Use pure Kotlin modules for platform-free value types, route keys, repository
  ports, domain rules, error models, fakes, fixtures, and assertion DSLs.
- Use Android library modules for contracts or adapters that need resources,
  `Context`, `ActivityResultRegistry`, system services, WebView, credentials,
  permissions, notifications, or Android SDK types.
- Use Compose-enabled Android library modules for reusable composables, state
  holders, app roots, notice hosts, design-system primitives, or lifecycle-aware
  Compose effects.
- Use names such as `kotlin-extensions`, `compose-extensions`, `runtime`,
  `base`, or `designsystem` only when the exported capability and forbidden
  imports are clear. Otherwise prefer a capability name such as `notice`,
  `router`, `permission`, `webview`, `activity`, or `resource`.

Review should stop when a module is called `core`, `common`, `shared`,
`extensions`, or `base` but callers cannot tell whether it is safe for pure
Kotlin, Android runtime, Compose runtime, tests, or app-shell code. Split the
module, rename it, or keep the helper local until the import surface is clear.

If the repo already uses convention plugins, apply the nearest plugin instead of
copying dependency blocks by hand. If no convention exists, update or add one
only when at least two modules will share the same setup.

## Android Boundary Naming Stops

Module family names are examples, not required names. Do not keep `app`,
`core-app`, `core-ui`, `core-runtime`, `base`, `runtime`, `common`, `shared`, or
"feedback" as a broad Android bucket unless the repo's package layout and
public exports make the concrete capability clear.

Stop and rename or split when any of these happen:

- A caller cannot tell whether a module provides route contracts, route
  execution, Activity launchers, deep-link parsing, notice rendering,
  permissions, WebView runtime, design-system components, or base lifecycle
  setup.
- Pure Kotlin contracts and Android/Compose runtime APIs live in the same
  stable import surface.
- A notice/toast/snackbar/dialog/alert/error surface is hidden behind a vague
  "feedback" module name.
- A `BaseActivity` or `BaseViewModel` becomes the place for product route
  registration, feature screen mapping, repository calls, analytics, permission
  policy, network error copy, and visual component ownership.
- Test fixtures, fakes, assertion subjects, and Activity or repository
  recorders are exported from one catch-all testing file.

Accept broad module names only when the next level is precise. For example, an
existing `core-app` module may contain capability packages such as `activity`,
`route`, `notice`, `permission`, `environment`, `webview`, or `launcher`, but it
must not make all of them available through one grab-bag import.

## Convention Plugin Shape

Use `build-logic` to remove repeated Gradle setup, not to hide product behavior.
A small Android repo usually needs only a few additive convention plugins:

```text
<repo>.android.application
<repo>.android.library
<repo>.android.library.compose
<repo>.kotlin.library
```

Add specialized plugins only after repeated module setup proves the need, such
as repository, Room, test-fixture, screenshot, or feature-implementation
conventions. Keep convention plugins responsible for:

- Android SDK versions, Java/Kotlin targets, test options, namespaces, and
  Compose enablement
- shared dependency bundles already used by multiple modules
- debug-only dependencies such as Compose tooling
- static analysis and test wiring when the repo has those tools configured
- optional Compose compiler reports or metrics when the repo uses them for
  stability diagnosis; keep them opt-in or scoped so normal builds are not noisy

Do not put product routes, DI graph decisions, repository bindings, signing
secrets, flavor policy, generated module discovery, or one-off module behavior
inside a shared convention plugin.

## Android DI Build Logic

When an Android repo chooses Hilt, treat it as the default Android DI baseline
until the repo explicitly migrates. Do not mix Hilt and Metro in one object
graph. Metro can be recorded as a future migration candidate only after the repo
accepts the ecosystem, annotation-processing, and migration risk.

Apply DI through a small additive convention plugin instead of repeating Gradle
setup in each module:

```text
<repo>.android.hilt
```

That plugin may own only DI tool wiring:

- apply the Hilt Gradle plugin
- apply the active annotation processor plugin, usually KSP for AGP built-in
  Kotlin projects and KAPT only when the repo already supports KAPT
- add `hilt-android` and the matching Hilt compiler dependency

Keep product bindings out of `build-logic`. Product graph decisions still live
in app, runtime, data, or feature implementation modules through Hilt modules.

Use this placement:

```text
app                         @HiltAndroidApp, @AndroidEntryPoint activities
core/runtime or core-app     runtime bindings such as ActivityRouteLauncher
feature/<name>/impl          feature-owned @IntoSet entries and adapters
core/domain or feature/api   pure contracts with no Hilt dependency
build-logic                  the <repo>.android.hilt convention only
```

Prefer Hilt multibindings for additive registrations such as activity route
launch handlers, route event handlers, deep-link specs, app initializers,
notice renderers, and route entry providers. The app shell should inject a
`Set<Handler>` or registry contract instead of manually constructing
`listOf(FeatureHandler())`.

When a handler set is injected, keep the owner that consumes the set injectable
too. Use a route graph, router factory, coordinator, or registry class with an
`@Inject` constructor instead of a Kotlin `object` that reaches into static
state. Pure route keys and deep-link specs can be `object` values; product graph
assembly and runtime creation should not be object singletons.

Hilt adoption should remove app-shell manual construction, not only add
annotations to a few handlers. Put environment, network, repository, auth, and
runtime graph decisions in Hilt modules at the boundary that owns the concrete
implementation:

```text
app/di                       BuildConfig config, app-wide repository selection,
                             auth gateway selection, qualified network clients
core/runtime/di              runtime adapters that need Android APIs
feature/<name>/impl/di       feature-owned @IntoSet handlers and route entries
feature/api or core/domain   pure contracts, no Hilt annotations
```

Activity/AppRoot code must not call constructors for network clients,
repositories, auth gateways, token providers, credential providers, route
graphs, router factories, or production ViewModel factories. It should inject a
small set of coordinators and let Hilt create `@HiltViewModel` instances through
the default Compose/ViewModel integration. If tests need direct construction,
keep that constructor test-friendly while production still uses Hilt.

Use qualifiers for same-type values such as API URLs, `String` client ids,
network clients, and dispatchers. A module that provides two `NetworkClient`
instances without qualifiers is incomplete even when it compiles by accident in
the current app shape.

Example:

```kotlin
@Module
@InstallIn(ActivityComponent::class)
abstract class ActivityRouteLauncherModule {
    @Binds
    abstract fun bindActivityRouteLauncher(
        impl: DefaultActivityRouteLauncher,
    ): ActivityRouteLauncher
}

@Module
@InstallIn(ActivityComponent::class)
abstract class WebViewActivityRouteModule {
    @Binds
    @IntoSet
    abstract fun bindWebViewActivityRouteLaunchHandler(
        impl: WebViewActivityRouteLaunchHandler,
    ): ActivityRouteLaunchHandler
}
```

Do not:

- make every `core` module a Kotlin-only module by default when the capability
  requires Android context, Activity, Compose, resource, or lifecycle APIs
- put Hilt annotations in pure API modules
- use a singleton object or manual service locator to avoid multibinding
- keep the product route graph or router factory as a Kotlin `object` while
  only the handlers are DI-managed
- keep a central app-shell `listOf(...)` that casts every feature route event
  family, Activity route handler, initializer, or route-entry provider; that
  list becomes a module-boundary failure as soon as growth is expected
- construct network clients, repositories, auth gateways, token providers,
  credential providers, route graphs, router factories, or production
  ViewModelProvider factories in the Activity or app root after Hilt is the
  repo baseline
- add Metro beside Hilt without a repo-level migration plan and equivalence test

## Split Decision

Choose a single feature module when:

- only one screen or flow owns the code
- no other module needs to compile against the contract
- navigation is local or can be wired from the current module
- implementation dependencies are acceptable to callers
- the boundary is still changing quickly

If the repo's architecture baseline is `api` plus implementation modules, follow
that convention, but keep the SOLID reason explicit. The `api` module is the
caller-facing interface: role-sized contracts, route/deep-link events, ports,
entities, and delegates. The implementation module owns concrete screens,
ViewModels, adapters, mappers, DI bindings, platform launchers, and runtime
wiring. Do not let the split become two files that mirror each other without
reducing imports, cycles, test weight, or implementation leakage.

Choose a `feature-api` plus `feature` implementation pair when:

- another feature, holder, app module, or navigation graph must reference the
  destination without depending on implementation
- route data, activity/fragment/Compose entrypoints, or public events cross the
  feature boundary
- the implementation has heavy dependencies such as camera, webview, ads,
  billing, SDK integrations, or large UI libraries
- the split prevents circular dependencies
- a fake, dev, paid/free, flavor-specific, or replaceable implementation is
  realistic

For Navigation 3-style apps, keep navigation keys, route data, deep-link
contracts, and public route events in the feature `api` module. Keep `NavEntry`,
entry-provider builders, composable content, and screen state holders in the
feature implementation or app-shell module. The app module assembles entry
providers, synthetic back stacks, host/scheme policy, and Activity task-stack
behavior.

Choose a repository `api` plus implementation pair when:

- feature modules need a repository interface and stable entities
- DTOs, Retrofit/Room/DataStore, SDK clients, or cache implementations should
  not leak into callers
- test modules need an assertion or fake implementation
- multiple repository implementations can exist for flavors, dev tools, or
  platform-specific behavior

Do not create `api` modules that contain only one unused interface and no caller
that benefits from avoiding the implementation dependency.

Choose an `assertions` module or source set when:

- two or more test boundaries need the same fake, fixture, recording helper, or
  assertion DSL
- a route, repository, adapter, or platform boundary needs reusable contract
  tests
- tests should compile against the stable API contract without depending on the
  production implementation module
- the reusable helper avoids booting the app shell, DI graph, network stack,
  database, WebView, camera, billing, or other heavy implementation dependency

Do not create an `assertions` module for one test, preview-only sample data, or
a helper that must import production implementation code to be useful. In those
cases, keep the helper local or put the test in the implementation module.

Inside an Android `assertions` module, split source files by testing role rather
than by convenience:

- fixtures or sample route/data keys in one focused file
- recording fakes/spies in files named for the contract they record
- assertion subjects or matchers in files named for the contract they assert
- builders/factories in files named for the value they construct
- contract tests in their own test source files

Do not put every fake, fixture, route key, recorder, and assertion DSL into one
module-level bucket file. The module is already the shared boundary; files
inside it still need SOLID responsibility and Interface Segregation. A test
that needs only a route fixture should not import an Activity launcher fake,
repository recorder, WebView helper, or production implementation dependency.

Choose a `core-app` module when:

- the shared code needs Android or Compose runtime APIs
- the code is app-shell infrastructure reused by several features, such as
  notice or alert hosts, permission adapters, ActivityRoute launching, WebView
  runtime, resources, or app-level composition helpers
- the caller-facing API can stay free of feature copy, product route policy,
  analytics policy, repository calls, and screen-specific state

Keep pure contracts in `core`; move Android/Compose runtime commonization to
`core-app`, `core-ui`, or a repo-specific runtime module only when a real
shared app-runtime boundary exists.
Avoid broad `BaseActivity`, `BaseFragment`, or universal `BaseViewModel`
hierarchies. Prefer small contracts such as app environment, route coordinator,
notice host, permission host, and platform adapter interfaces.

For ViewModel-adjacent runtime capabilities, prefer interfaces and delegates
over inheritance. A notice, router, deep-link, permission, or launcher delegate
can own reusable effect plumbing, but the ViewModel remains the action/state
owner. The delegate exists to avoid broad base classes, not to hide product
policy or screen state.

A reusable Compose Activity base may own only the narrow Activity template:
edge-to-edge setup, content installation, lifecycle-aware intent/deep-link
handoff, environment access, and explicit extension hooks. Keep product route
registration, Navigation 3 entry-provider assembly, feature screen mapping,
ViewModel creation, repository calls, analytics, and screen state outside that
base.

## Dependency Direction

Keep dependencies acyclic and predictable:

```text
app
  -> feature-api and selected feature implementations
feature implementation
  -> own feature-api, design system, core utilities, repository-api, domain
feature-api
  -> small route/data contracts and stable core contracts only
repository implementation
  -> repository-api, network/local data sources, mappers, config
repository-api
  -> stable entities and repository interfaces only
core/designsystem
  -> platform primitives, resources, tokens, reusable UI contracts
```

Forbidden edges:

- `feature-api -> feature implementation`
- `repository-api -> repository implementation`
- `repository -> feature`
- `core/designsystem -> feature`
- `domain -> UI, Compose, Android framework UI types, DTO transport models`
- `app -> concrete repository internals` except app-level DI binding when the
  repo intentionally centralizes bindings there

## Feature Package Layout

Inside a feature implementation module, prefer packages that reveal behavior and
dependency direction:

```text
<feature>/
  <Feature>Route.kt          ViewModel/lifecycle/navigation/effect wiring
  <Feature>ViewModel.kt      screen state owner
  model/                     UiState, UiAction, UiEffect, UI display models
  compose/ or ui/            stateless screen composables
  compose/component/         feature-local components
  preview/                   PreviewParameterProvider and sample states
  convert/ or mapper/        domain/repository -> UI model mapping
  di/                        feature-local bindings
  navigation/                local graph or route registration when needed
```

For small screens, keeping `Route`, `Screen`, `UiState`, and preview provider in
one package is fine. Split packages when each area has a separate owner, many
files, or tests.

## Repository Package Layout

Inside a repository implementation module, keep API contracts and transport
details separate:

```text
repository-<name>-api/
  <Name>Repository.kt        caller-facing interface
  model/                     stable entities returned to domain/UI

repository-<name>/
  <Name>RepositoryImpl.kt    source coordination and error normalization
  <Name>Api.kt               Retrofit or remote source contract
  local/                     Room/DataStore/file source if present
  model/                     request/response DTOs
  mapper/ or convert/        DTO/cache -> entity mapping
  di/                        implementation bindings
```

Repository entities should be stable for callers. DTOs, request bodies,
response wrappers, database rows, SDK models, and generated network models stay
inside implementation packages unless the repo explicitly treats them as public
contracts.

## Shared UI And Holder Modules

Create a shared UI, holder, or feature-common module only when it has a stable
caller contract and repeated use:

- Use design-system modules for domain-free primitives, tokens, typography,
  buttons, list rows, dialogs, sheets, and accessibility contracts.
- Put theme, semantic color/type/shape tokens, component defaults, app UI
  wrappers, and preview fixtures in the design-system module when they are
  reused across features.
- Use feature-common modules for product UI patterns shared by several feature
  owners.
- Use holder modules for reusable workflow entrypoints or embedded surfaces that
  own their own state/effects and have a clear lifecycle.
- Keep analytics labels, permission policy, route decisions, and repository
  calls in the caller or holder state owner, not in a leaf component.
- Keep feature product cards, screen headers, fake data, route events, and
  domain-to-UI mapping in feature modules or feature-common modules, not in the
  design system.

If a shared module needs many feature flags, product-specific callbacks, or a
full screen `UiState`, keep the code feature-local instead.

## Migration Strategy

When modernizing an old Android feature:

1. Record the current owner boundary and imports before moving files.
2. Extract stable contracts first: route data, repository interface, public
   entities, or UI component API.
3. Compile or typecheck the contract boundary before moving implementation.
4. Move implementation behind the contract in the smallest reviewable slice.
5. Add or update tests/previews for the moved boundary.
6. Remove only old code that is no longer referenced.

Do not combine broad module moves with behavior changes unless the behavior
change is necessary to make the split correct.

## Android Skill Source Coverage

When an Android task touches one of these surfaces, apply the corresponding
source-specific guidance in addition to this AgentPlaybook card. Do not copy
external skill files into the repo by default; distill the rule into the task
plan and cite the source when reporting. This section is a summary; the complete
source document list lives in `android-external-skill-source-coverage.md`.

- Android CLI and device inspection: use the Android CLI surface for SDK
  management, device runs, screenshots, layout inspection, doc lookup, and
  installed Android skill discovery before guessing tool behavior.
- AGP upgrades: check the current AGP version first, respect Gradle/JDK/Kotlin
  compatibility, do not use AGP 9 guidance for KMP projects, avoid `clean` as a
  default verification step, and verify with sync/help/dry-run style checks.
- R8 and keep rules: inspect Gradle/R8 configuration before editing, prefer
  quantitative analyzer evidence when available, treat broad package-wide keep
  rules as review risk, and validate runtime-sensitive removals with
  Macrobenchmark or focused smoke evidence.
- Perfetto SQL and trace analysis: use schema-backed queries, idempotent
  Perfetto SQL, `utid`/`upid` instead of recycled process/thread ids, `GLOB`
  instead of `LIKE`, metrics-first investigation, and chain-of-evidence notes
  before concluding root cause.
- Navigation 3: keep typed route keys and deep-link contracts in API
  boundaries, map them to `NavDisplay` entries in app/impl boundaries, use
  synthetic back stacks for advanced deep links, support multiple back stacks,
  conditional flows, results, dialogs, bottom sheets, and adaptive scenes only
  where the product behavior requires them.
- XML-to-Compose migration: migrate one XML candidate at a time, capture visual
  baseline or screenshots when possible, keep interop theming minimal, add a
  Compose preview, validate parity, then remove only unused XML resources.
- Adaptive Compose: require Compose and Navigation 3 first, verify form factors,
  adapt navigation areas with `NavigationSuiteScaffold`, use Navigation 3 scene
  strategies for list-detail/supporting panes, and add screenshot coverage for
  phone, foldable, tablet, and desktop-sized layouts when the repo supports it.
- Edge-to-edge and IME: make each Activity explicit with `enableEdgeToEdge()`
  before `setContent`, use `adjustResize` for soft keyboard owners, pass
  `Scaffold` insets to scrollable `contentPadding`, avoid double insets, and
  verify text fields, FABs, lists, dialogs, and system bar icon contrast.
- Compose Styles: treat the Styles API as experimental, require the documented
  compileSdk/Foundation or BOM version and opt-in, use it only for custom
  components/themes, and validate with screenshot or preview parity before
  replacing direct style parameters.
- Testing setup: inventory existing DI, unit, mocking, Robolectric, Compose,
  Espresso, screenshot, and E2E tools before adding dependencies; prefer fakes
  over mocks for platform/data seams; cover navigation, deep links, restoration,
  window sizes, and changed visible states.
- CameraX migration: remove legacy Camera1/manual lifecycle code, bind use
  cases through `ProcessCameraProvider` and a `LifecycleOwner`, use
  `CameraXViewfinder` for Compose, update target rotation, and always close
  `ImageProxy`.
- Credential Manager and verified email: client parsing is not security
  validation. Generate a fresh nonce, send raw credential response and nonce to
  a server for cryptographic verification, and use WebView bridges only as a
  native handoff to Credential Manager.
- Play Billing: detect the effective library version from both dependency and
  deprecated API usage, plan direct or stepped migration, follow every relevant
  version checklist item, and verify builds/tests at migration boundaries.
- Play Engage: identify vertical, cluster, request structure, entity mapping,
  data source, worker/publisher/receiver responsibilities, and required static
  plus dynamic receiver registration before generating code.
- Wear Compose Material3: use latest stable compatible versions, sync before
  refactoring, read version-matched component samples, prefer
  `TransformingLazyColumn`, pass `ScreenScaffold` padding, and use Navigation 3
  `SwipeDismissableSceneStrategy` for new Wear navigation.
- XR/Glimmer: use a projected Activity and Glimmer components/theme instead of
  Material, keep a pure black root background for additive displays, respect
  minimum readable text and contrast, map one-dimensional inputs/focus, and
  show one primary piece of information at a time.
- AppFunctions: require the documented target/compile SDK level, discover
  high-value workflows before implementing, immediately refine KDoc for agent
  discovery, verify with ADB, and never expose sensitive or destructive actions
  without confirmation.

## Review Checklist

- Is this package/module the lowest boundary that protects the real owner?
- Does each `api` module have at least one caller that should avoid the
  implementation dependency?
- Does each `assertions` module expose role-sized fixtures, fakes, recorders,
  builders, and assertion subjects instead of one catch-all testing file?
- Can tests import the assertion helper they need without depending on
  production `impl` modules or unrelated platform/runtime helpers?
- Are DTOs, SDK models, database rows, and Android framework objects kept out of
  stable feature/domain contracts?
- Can a feature implementation depend on repository APIs without importing
  repository internals?
- Are design-system modules free of product routes, analytics, permissions, and
  repository calls?
- Can a new feature import only the capability it needs, or does it have to
  depend on a broad `core-app`, `common`, `base`, `runtime`, or "feedback"
  bucket?
- Is any reusable `BaseActivity` limited to Activity template work instead of
  owning product routing, DI, repositories, ViewModel creation, or screen state?
- Did the change update convention plugins instead of duplicating Gradle setup
  across modules?
- Are previews, ViewModel tests, repository tests, or import-direction checks
  covering the new boundary?
