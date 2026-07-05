---
keyflow_id: sys_android_compose_performance_source_map
status: review
type: human-reviewed-needed
---

# Compose Performance Source Map

Use this reference when a task touches
`https://github.com/skydoves/compose-performance-skills`. Current snapshot:
`1b32f81724c0d71fe9ef093ca44697f559fdab6e`.

Open the upstream `SKILL.md` named below before applying a local rule. Open the
reference files named here when the task changes implementation or verification.

## Audit And Measurement

- `audit/auditing-compose-performance/SKILL.md`: use for broad audits. Apply
  measure -> diagnose -> fix one cause -> verify. Do not report a performance
  fix from code inspection alone.
- `measurement/testing-compose-in-release-mode/SKILL.md`: use when validating
  frame time, startup, scroll, or recomposition behavior. Debug builds and
  emulators are diagnostic only unless clearly labeled.
- `measurement/generating-baseline-profiles/SKILL.md`: use for Baseline Profile
  generation and validation. Reference `macrobenchmark-harness.md` for harness
  structure.
- `measurement/tracing-recompositions-at-runtime/SKILL.md`: use when release
  recomposition traces are needed after Layout Inspector or compiler evidence.

Local rule: performance claims need release-like measurement or a labeled
diagnostic source. Keep before/after numbers attached to the scenario.

## Recomposition

- `recomposition/debugging-recompositions/SKILL.md`: use Layout Inspector
  Argument Change Reasons; name Changed, Unchanged, Uncertain, Static, or
  Unknown before choosing a fix.
- `recomposition/choosing-derivedstateof/SKILL.md`: use only when an input
  changes more often than the UI should update and equality reduces downstream
  invalidation.
- `recomposition/deferring-state-reads/SKILL.md`: use when state can be read in
  layout/draw instead of composition. Reference `three-phases.md`.
- `recomposition/avoiding-subcomposition-pitfalls/SKILL.md`: use for nested
  lazy containers, `BoxWithConstraints`, `SubcomposeLayout`, and measurement
  loops that amplify composition work.
- `recomposition/using-strong-skipping-correctly/SKILL.md`: use when Kotlin or
  Compose compiler behavior affects skippability. Reference `escape-hatches.md`.

Local rule: move reads to the latest correct phase; do not add stability
annotations or `derivedStateOf` before proving the invalidation source.

## Stability

- `stability/diagnosing-compose-stability/SKILL.md`: read compiler reports
  before changing types. References: `reading-classes-txt.md` and
  `reading-composables-txt.md`.
- `stability/stabilizing-compose-types/SKILL.md`: use the three-tier order:
  immutable collections/wrappers first, then annotations, then stability config
  only when the contract is true. Reference `stability-config-syntax.md`.
- `stability/understanding-stability-inference/SKILL.md`: use when explaining
  compiler inference. References: `bitmask-encoding.md` and
  `twelve-phase-algorithm.md`.
- `stability/enforcing-stability-in-ci/SKILL.md`: use when adding or reviewing
  stability report checks.
- `stability/using-stability-analyzer-ide-plugin/SKILL.md`: use for IDE-assisted
  diagnosis, not as final proof.
- `stability/visualizing-recomposition-cascades/SKILL.md`: use when a stable
  fix must be traced through parent/child invalidation.

Local rule: stability configuration is a codebase-wide promise. Do not mark
mutable or externally changing types as stable to silence reports.

## Lazy Layouts And Lists

- `lists/optimizing-lazy-layouts/SKILL.md`: use for unstable keys, missing
  `contentType`, heterogeneous rows, nested lazy lists, and item allocation.
- `lists/configuring-lazy-prefetch/SKILL.md`: use only after keys, content type,
  item stability, and allocation issues have been measured.

Local rule: fix identity and item model stability before prefetch tuning.

## Side Effects And Flow Collection

- `side-effects/collecting-flows-safely/SKILL.md`: use for Flow collection,
  lifecycle boundaries, `collectAsStateWithLifecycle`, and avoiding raw
  `Flow<T>` leaf parameters.
- `side-effects/using-efficient-effects/SKILL.md`: use for effect key
  correctness, avoiding restart churn, and choosing `LaunchedEffect`,
  `DisposableEffect`, `SideEffect`, `produceState`, or `rememberUpdatedState`.

Local rule: collect at lifecycle-aware holder boundaries and pass state/events
down as values/callbacks.

## Modifiers

- `modifiers/migrating-to-modifier-node/SKILL.md`: use for new custom modifiers
  and migration away from `composed {}`. Reference `modifier-node-anatomy.md`.
- `modifiers/ordering-modifier-chains/SKILL.md`: use when hit testing, visual
  padding, clipping, graphics layers, or touch target behavior depends on
  modifier order.

Local rule: prefer `Modifier.Node` for new custom modifiers when supported.
Modifier order is behavior, not style.

## R8 And Hot Reload

- `build/configuring-r8-for-compose/SKILL.md`: use when keep rules, minify,
  obfuscation, or Compose release optimization changes. Trust current consumer
  rules by default.
- `hot-reload/setting-up-compose-hotswan/SKILL.md`,
  `hot-reload/understanding-hot-reload-limits/SKILL.md`,
  `hot-reload/preserving-state-across-reloads/SKILL.md`, and
  `hot-reload/iterating-with-ai-and-mcp/SKILL.md`: use only for projects that
  intentionally use HotSwan/MCP iteration. Keep hot-reload evidence separate
  from production performance evidence.

Local rule: hot reload is an iteration loop, not verification of runtime
correctness or performance.
