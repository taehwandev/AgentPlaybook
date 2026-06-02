---
keyflow_id: sys_775cd6266968
status: review
type: ai-generated
---

# Android Review

Use for Android app, Compose/ViewModel, permission, and UI flow review.

## Review

- Check Compose state hoisting, ViewModel ownership, Flow collection, and lifecycle safety.
- Check ViewModel, `UiState`, Flow, repository, and one-off event boundaries
  against `android-viewmodel-state.md` when state/data changed.
- Check Compose-observed `UiState` and UI display models for truthful
  `@Immutable`/`@Stable` contracts, immutable collections, stable defaults, and
  absence of mutable/platform/repository objects.
- Check advanced stability opt-ins such as strong skipping configuration,
  stability configuration files, compiler metrics, and `@NonSkippableComposable`
  annotations for measured need and documented contracts.
- Check stateful holder vs stateless screen/component boundaries.
- Check module/package boundaries against `android-module-structure.md` when new
  modules, package moves, API contracts, build logic, or repository splits are
  touched.
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

## Tools

- Static: Gradle lint, ktlint/detekt if configured.
- Unit: JVM tests for mapper, validator, policy, ViewModel state.
- Instrumented: AndroidJUnitRunner for framework-dependent behavior.
- UI: Compose UI Test or Espresso for screen interactions.
- Screenshot: Paparazzi or screenshot tests if the repo uses them.
- Flow: Turbine or equivalent for stream behavior when configured.
- Performance: Macrobenchmark or baseline profile for startup and critical flows when configured.
- Compose stability: compiler metrics, Layout Inspector recomposition counts, or
  a focused before/after manual inspection when the repo already uses those
  tools or the change targets recomposition.

## UI Test Focus

- Screen renders expected state from fake ViewModel/state.
- Stateless screen and component previews cover the changed visual states.
- User actions emit correct events or trigger expected navigation.
- Lists use stable keys/content types when items reorder, update independently,
  animate, or hold local state.
- High-frequency state reads are deferred to the smallest composable or
  lambda-based modifier that needs them, and composable bodies do not perform
  backwards writes to state they just read.
- Permission denied and retry flows are covered.
- Rotation, process death, or lifecycle changes do not lose critical state.
- Background jobs do not duplicate side effects after retry or process death.
- Release build configuration does not expose debug endpoints, secrets, or broad exported components.
- API modules do not leak implementation dependencies, DTOs, database rows, SDK
  models, or feature implementation types.
- Shared design-system/core modules do not import feature modules or product
  policy.
