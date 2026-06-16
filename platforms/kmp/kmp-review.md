---
keyflow_id: sys_kmp_review
status: review
type: human-reviewed-needed
---

# KMP Review

Use when reviewing Kotlin Multiplatform, Compose Multiplatform, shared Kotlin
modules, source-set changes, platform actuals, or target app integration.

## Findings Priority

1. Cross-target behavior mismatch, unsupported target hidden as success, or data loss.
2. Security, credential, file, shell, permission, or native interop risk.
3. Shared source-set dependency leak or platform API import in common code.
4. Missing target build/test evidence.
5. UI/state ownership, cancellation, cleanup, or lifecycle bug.
6. Maintainability, naming, package layout, or duplicated adapters.

## Check

- Does the route use the target repo's local KMP/Gradle/module rules?
- Are module and source-set boundaries checked against
  `kmp-module-structure.md` when Gradle modules, umbrella frameworks, or package
  moves changed?
- Are source-set dependencies intentional and compileable for every affected target?
- Is shared code free of accidental Android, desktop, iOS, JVM-only, or native-only APIs?
- Do actual implementations satisfy the same contract or return typed unsupported failures?
- Are platform resources cleaned up on cancellation, failure, lifecycle teardown, and app quit?
- Are state, effects, repositories, and platform adapters owned by the right layer?
- Is verification run for every affected target, or is the skipped target and
  residual risk stated?
- Do presentation modules avoid data implementation, database entity, network
  DTO, generated client, and platform SDK imports?
- Are feature/domain/data/database/presentation splits justified by ownership,
  dependency leakage, source-set pressure, offline/sync behavior, or test
  boundaries rather than template ceremony?
- Are build logic and version catalog changes limited to shared build setup,
  with product routes, DI membership, secrets, signing values, and environment
  policy kept out?
- Does offline-first code use a durable local source of truth, explicit sync
  state, retry/backoff, migration, conflict handling, and logout/account-switch
  invalidation?
- Does auth/network code skip token refresh loops, clear cached tokens on
  logout, redact debug output, and map session expiry into typed state?
- Are debug-only tools disabled or replaced with no-op release variants?
- Are Compose screens split into root/state holder and stateless screen, with
  typed state/actions/effects and previews or visual checks for changed states?
- Are Flow, Channel, StateFlow, SharedFlow, callbacks, and suspend APIs tested
  with deterministic coroutine control when behavior changed?
- Are release checks covering serialization/minification rules, signing,
  framework export, package identifiers, config injection, and target smoke
  paths when release surfaces changed?

## Output

Lead with concrete findings:

```text
Findings:
- [High] platforms/kmp/... - issue, impact, recommendation, verification
```

If no findings remain, say so and list target/test gaps that were not checked.
