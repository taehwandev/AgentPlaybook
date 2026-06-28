---
keyflow_id: sys_775cd6266968
status: review
type: ai-generated
---

# Android Review

Use for Android app, Compose/ViewModel, permission, and UI flow review.

## Review

- Check Compose state hoisting, ViewModel ownership, Flow collection, and lifecycle safety.
- Check platform or heavy resource ownership: listeners, receivers, WebView,
  media players, bitmaps, file handles, and foreground notifications should
  have a matching cleanup path on dispose, failure, cancellation, and owner end.
- Check ViewModel, `UiState`, Flow, repository, and one-off event boundaries
  against `android-viewmodel-state.md` when state/data changed.
- Check Compose-observed `UiState` and UI display models for truthful
  `@Immutable`/`@Stable` contracts, immutable collections, stable defaults, and
  absence of mutable/platform/repository objects.
- Check advanced stability opt-ins such as strong skipping configuration,
  stability configuration files, compiler metrics, and `@NonSkippableComposable`
  annotations for measured need and documented contracts.
- Check performance changes for the actual bottleneck category: Compose
  recomposition, main-thread work, startup, duplicate network calls, cache
  freshness, media/WebView cost, dependency size, or build-time cost. Do not
  accept broad refactors, dependency additions, or framework migrations as
  performance fixes without reproduction or measurement evidence.
- Check stateful holder vs stateless screen/component boundaries.
- Check module/package boundaries against `android-module-structure.md` when new
  modules, package moves, API contracts, build logic, or repository splits are
  touched.
- Reject package/module splits that lack a boundary note naming owner, allowed
  imports, forbidden imports, callers, and focused verification. A package split
  that only creates one folder per type, mirrors a reference app, or moves files
  without changing dependency direction is structure churn, not architecture.
- For `api` / `impl` / `assertions`, verify that `api` exposes caller-facing
  contracts only, `impl` owns execution details, and `assertions` depends on
  `api` rather than production `impl` by default.
- Check design-system ownership when shared UI changes: tokens, wrappers,
  defaults, and accessibility contracts belong there; product copy, routes,
  analytics, permissions, fake data, and repository calls do not.
- Confirm meaningful screen, section, and reusable component changes include
  previews or a documented replacement check.
- Verify loading, empty, error, permission-denied, and offline states.
- Ensure repository/data source boundaries are not bypassed from UI.
- Check permission, activity result, navigation argument, and process recreation behavior.
- Confirm secrets and user data are not logged.
- Check WorkManager, foreground service, notification, and retry behavior when background work is touched.
- Review exported components, deep links, WebView bridges, PendingIntent mutability, and cleartext traffic when security surfaces change.
- When the change touches AGP, R8, Perfetto, XML-to-Compose migration,
  adaptive layouts, edge-to-edge, Compose Styles, CameraX, Credential Manager,
  Play Billing, Play Engage, Wear, XR/Glimmer, or AppFunctions, confirm the
  source-specific Android skill guidance from
  `android-external-skill-source-coverage.md` and
  `android-module-structure.md` was applied before accepting the
  implementation.

## Tools

- Static: Gradle lint, `ktlint` or `ktfmt` for formatting, and `detekt` for
  naming, complexity, size, and maintainability when configured. If the repo has
  no tool config, review against the strict static quality profile in
  `common/code-conventions.md` and document the missing automation.
- Unit: JVM tests for mapper, validator, policy, ViewModel state.
- Instrumented: AndroidJUnitRunner for framework-dependent behavior.
- UI: Compose UI Test or Espresso for screen interactions.
- Screenshot: Paparazzi or screenshot tests if the repo uses them.
- Flow: Turbine or equivalent for stream behavior when configured.
- Performance: Macrobenchmark or baseline profile for startup and critical flows when configured.
- Runtime performance: trace, log timing, profiler, or focused manual evidence
  for main-thread IO, bitmap/JSON work, duplicate calls, cache invalidation, or
  media/WebView loading when those paths changed.
- Compose stability: compiler metrics, Layout Inspector recomposition counts, or
  a focused before/after manual inspection when the repo already uses those
  tools or the change targets recomposition.
- Compose performance: prefer release or benchmark variant, R8 enabled, and
  physical-device evidence for frame time, scroll, jank, startup, or baseline
  profile claims. Debug/emulator evidence must be labeled diagnostic only.
- Perfetto: schema-backed SQL, metrics-first trace review, `utid`/`upid`, and
  chain-of-evidence notes for root-cause claims.

## UI Test Focus

- Screen renders expected state from fake ViewModel/state.
- Stateless screen and component previews cover the changed visual states.
- User actions emit correct events or trigger expected navigation.
- Lists use stable keys/content types when items reorder, update independently,
  animate, or hold local state.
- High-frequency state reads are deferred to the smallest composable or
  lambda-based modifier that needs them, and composable bodies do not perform
  backwards writes to state they just read.
- Flow values are collected lifecycle-aware at the route/holder boundary; raw
  `Flow<T>` is not passed through leaf composable parameters.
- Side effects use the smallest lifecycle-correct API and are keyed by semantic
  inputs rather than broad `UiState` objects or stale `Unit` keys.
- Custom modifiers prefer `Modifier.Node` for new code, and `Modifier.composed`
  has a compatibility reason when introduced.
- Lazy item animations use stable keys; heterogeneous lazy lists provide
  `contentType`; expensive item allocations are not repeated inside item
  lambdas without measurement.
- Optional slots do not reserve space when absent, and reusable component APIs
  keep product policy, route decisions, and analytics in the caller.
- Permission denied and retry flows are covered.
- Rotation, process death, or lifecycle changes do not lose critical state.
- Background jobs do not duplicate side effects after retry or process death.
- Release build configuration does not expose debug endpoints, secrets, or broad exported components.
- API modules do not leak implementation dependencies, DTOs, database rows, SDK
  models, or feature implementation types.
- Shared design-system/core modules do not import feature modules or product
  policy.
