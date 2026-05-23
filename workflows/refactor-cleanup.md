---
keyflow_id: sys_refactor_cleanup_workflow
status: review
type: human-reviewed-needed
---

# Refactor Cleanup Workflow

Use when behavior should stay the same and the goal is structure, naming,
ownership, deletion, or maintainability.

## Read

- `common/refactoring.md`
- `common/code-conventions.md`
- `common/change-size-policy.md`
- `common/testing.md`
- `common/verification-policy.md`
- matching platform architecture card from `index.md`
- `common/api-contract-compatibility.md` when routes, DTOs, schemas, events,
  persisted fields, generated clients, or public APIs may change
- `common/server-side-caching.md` when cache keys, tags, TTL, materialized read
  models, or invalidation may change
- generated-files, dependency, security, persistence, or release policy when
  those surfaces change

## Steps

1. Identify the current behavior and the next change that the refactor should make easier.
2. Identify the contracts, state owners, side effects, generated files, and tests
   near the change.
3. Choose one ownership boundary: UI, state, domain, data, platform, contract, or test.
4. Make the smallest move, rename, extraction, deletion, or adapter cleanup that improves that boundary.
5. Avoid changing product behavior, formatting unrelated files, or mixing dependency updates.
6. Verify behavior with the nearest existing check or a focused smoke path.
7. Report the preserved behavior, structural change, unchanged contracts, verification, and any follow-up left separate.

## Stop If

- The refactor needs product behavior changes to make sense.
- The diff is mostly mechanical churn that obscures the behavior boundary.
- No verification exists and the touched surface is risky enough to need one first.
- The cleanup changes a public contract, cache behavior, permission boundary, or
  persisted data shape without the matching compatibility and verification plan.
