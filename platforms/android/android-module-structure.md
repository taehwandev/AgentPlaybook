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

## Reference Project Drill

When using a large Android reference app, copy the boundary lesson, not the
whole shape. Distill the reference into the current repo's scale:

- Keep transferable boundaries such as included `build-logic`, convention
  plugins, feature `api`/implementation splits, design-system modules,
  repository API/implementation splits, domain use cases, and deterministic fake
  or assertion modules.
- Rename plugin ids, packages, modules, and generated namespaces to the target
  repo. Never keep reference-project names in shared build or source contracts.
- Drop reference-only dependencies such as ads, banking SDKs, billing, Firebase,
  Hilt, KSP, generated factories, signing, flavors, analytics, or enterprise
  verification tooling unless the current task explicitly needs them.
- Collapse deep reference folder hierarchies when the target has only one
  product area. A small app often needs `app`, `core:designsystem`,
  `core:model`, `core:domain`, `core:data`, and one feature module before it
  needs dozens of feature/common/holder modules.
- Treat reference code as evidence for module direction and package naming, not
  as authority over state, DI, security, or product policy when repo-local rules
  differ.

## Module Families

Use repo-local names first. A large Android app commonly separates these module
families:

| Family | Owns | Must Not Own |
| --- | --- | --- |
| `app` | Application class, build types/flavors, app-level DI graph, startup, top-level navigation wiring. | Feature implementation, repository implementation details, shared UI primitives. |
| `build-logic` | Convention plugins, common Android/Kotlin/Compose/test settings, dependency bundles. | Product behavior or runtime code. |
| `core` | Pure Kotlin or implementation-neutral contracts such as models, domain interfaces, route contracts, network contracts, dispatchers, resource-provider contracts, and test-support contracts. | Android/Compose runtime, feature product policy, or screen-specific UI. |
| `core-ui` / `core-app` | Android/Compose app-runtime commonization such as design system, resources, permission helpers, ActivityRoute launch adapters, WebView runtime, feedback hosts, toast/dialog rendering, and app UI infrastructure. | Feature-specific copy, route policy, analytics policy, or repository calls. |
| `data` / `core-data` | Repository contracts, repository implementations, local/remote data sources, DTO mapping, DataStore/Room/cache ownership. | Compose UI, navigation decisions, screen state. |
| `domain` | Optional use cases and product policies reused across screens or risky enough to test independently. | Pass-through wrappers around one repository call. |
| `feature-api` | Navigation contracts, public entrypoints, route data, events, small caller-facing models. | Screens, ViewModels, repository implementations, DI bindings with heavy dependencies. |
| `feature` / `feature-impl` | Route holders, stateless screens, ViewModels, feature-local components, UI mappers, feature DI. | Shared design primitives or cross-feature data contracts. |
| `feature-common` / `holder` | Reused product UI or workflow holders with a named owner and stable caller contract. | Dumping ground for unrelated screen fragments. |
| `dev` / `testing` / `assertions` | Dev-only screens, reusable fakes, recording adapters, fixture builders, assertion DSLs, and contract test helpers. | Production-only behavior that callers need at runtime, or dependencies on production implementation modules by default. |

If the repo already uses convention plugins, apply the nearest plugin instead of
copying dependency blocks by hand. If no convention exists, update or add one
only when at least two modules will share the same setup.

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

## Split Decision

Choose a single feature module when:

- only one screen or flow owns the code
- no other module needs to compile against the contract
- navigation is local or can be wired from the current module
- implementation dependencies are acceptable to callers
- the boundary is still changing quickly

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
  feedback hosts, permission adapters, ActivityRoute launching, WebView runtime,
  resources, or app-level composition helpers
- the caller-facing API can stay free of feature copy, product route policy,
  analytics policy, repository calls, and screen-specific state

Keep pure contracts in `core`; move Android/Compose runtime commonization to
`core-app` or `core-ui` only when a real shared app-runtime boundary exists.
Avoid broad `BaseActivity`, `BaseFragment`, or universal `BaseViewModel`
hierarchies. Prefer small contracts such as app environment, route coordinator,
feedback host, permission host, and platform adapter interfaces.

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
- Did the change update convention plugins instead of duplicating Gradle setup
  across modules?
- Are previews, ViewModel tests, repository tests, or import-direction checks
  covering the new boundary?
