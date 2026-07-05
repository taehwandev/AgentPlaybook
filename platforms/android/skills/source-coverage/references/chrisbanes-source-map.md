---
keyflow_id: sys_android_chrisbanes_source_map
status: review
type: human-reviewed-needed
---

# Chris Banes Source Map

Use this reference when a task touches
`https://github.com/chrisbanes/skills`. Current snapshot:
`10e5158f9d674d340531c6559ce311b22e3f6457`.

Chris Banes skills are mostly self-contained `SKILL.md` files without
additional `references/`. Coverage therefore requires routing to the correct
upstream skill, not only listing the file.

## Router

### `skills/using-chrisbanes-skills/SKILL.md`

Read for broad Compose or Kotlin tasks. It is the source router for deciding
which narrower skill to load.

Local rule: do not load every Chris Banes skill for a broad task. Use the router
to pick state, effects, layout/modifier, testing, performance, Kotlin Flow,
coroutines, KMP, or value-class guidance.

## Compose State And UI Boundaries

- `skills/compose-state-holder-ui-split/SKILL.md`: use for screen refactors, ViewModel
  boundaries, state/event/callback split, and plain UI versus state holder.
- `skills/compose-state-hoisting/SKILL.md`: use for ownership decisions, plain state
  holders, saving state, and composition ownership.
- `skills/compose-state-authoring/SKILL.md`: use for `remember`, local `var`,
  snapshot back-writing, `@ReadOnlyComposable`, and state authoring mistakes.
- `skills/compose-state-deferred-reads/SKILL.md`: use when state reads can move from
  composition to layout/draw or provider lambdas.

Local rule: broad screen work starts with state-holder/UI split before
performance, animation, focus, or testing specialization.

## Compose Effects, Flow, And Events

- `skills/compose-side-effects/SKILL.md`: use for `LaunchedEffect`, `DisposableEffect`,
  `SideEffect`, `produceState`, `rememberUpdatedState`, snackbar/focus/analytics
  effects, and one-off event handling.
- `skills/kotlin-flow-state-event-modeling/SKILL.md`: use for `StateFlow`,
  `SharedFlow`, sentinels, `update`, `stateIn`, `.value`, and event/state
  modeling.
- `skills/kotlin-coroutines-structured-concurrency/SKILL.md`: use for stored scopes,
  init launches, background loops, cancellation, `runBlocking`, and explicit
  lifecycle ownership.

Local rule: one-off effects and Flow events should be modeled at the state
holder boundary, not pushed into leaf composables.

## Compose Components, Modifiers, Focus, Animation, And Tests

- `skills/compose-slot-api-pattern/SKILL.md`: use when reusable components need slots,
  receiver scopes, nullable optional regions, and `XxxDefaults`.
- `skills/compose-modifier-and-layout-style/SKILL.md`: use for caller-owned
  `Modifier`, layout primitives, padding/size ownership, and component API
  shape.
- `skills/compose-focus-navigation/SKILL.md`: use for focus targets, `FocusRequester`
  ownership, directional navigation, key events, focus restoration, and tests.
- `skills/compose-animations/SKILL.md`: use to choose the smallest animation API and
  verify lifecycle/identity/performance behavior.
- `skills/compose-ui-testing-patterns/SKILL.md`: use for semantics-first tests,
  callback testing, injected `MutableInteractionSource`, screenshot states,
  fake images, and platform service fakes.

Local rule: component API work pairs modifier/layout style with slots when both
placement and content flexibility are in play.

## Compose Performance And Stability

- `skills/compose-recomposition-performance/SKILL.md`: use for recomposition diagnosis
  and performance review.
- `skills/compose-stability-diagnostics/SKILL.md`: use when type stability or compiler
  reports drive the fix.

Local rule: do not patch UI API shape based on recomposition suspicion alone.
Name the unstable or changing parameter and verify after the fix.

## Kotlin And Multiplatform

- `skills/kotlin-multiplatform-expect-actual/SKILL.md`: use for semantic common APIs,
  expect/actual boundaries, platform leaf composables, and fakes/DI decisions.
- `skills/kotlin-types-value-class/SKILL.md`: use for single-value domain wrappers,
  Compose stability contracts, serialization/API changes, and hot-path boxing.

Local rule: use `expect/actual` only when common callers need a semantic API
with thin actuals. Interfaces are often better when testing or DI matters.

## Automation

- `skills/shepherd/SKILL.md`: use for external CI/comment shepherding. It is not an
Android implementation source; route it only for PR/CI process work.
