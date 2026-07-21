---
keyflow_id: sys_platforms_android_android_memory_lifecycle_md_skill
status: review
type: ai-generated
---

# Android Memory And Lifecycle

Use when creating, reviewing, or moving Android resources whose lifetime can
outlive a screen, view, composition, coroutine, or worker.

## Read

- `references/current-guidance.md` for owner, release, and verification rules.
- `../android-compose-ui/SKILL.md` for Compose state/effect boundaries.
- `../android-background-work/SKILL.md` for durable work and retry ownership.

## Process

1. Name the resource owner before creating or retaining the resource.
2. Pair every registration or allocation with release on dispose, cancellation,
   failure, replacement, and owner end as applicable.
3. Verify the lifecycle path that changed; compile success alone is not proof of
   lifecycle safety.

## Do Not

- Do not retain Activity, Fragment, View, or Composition references in long-lived
  objects.
- Do not create heavy resources on every recomposition or list-item render.
- Do not introduce a pool, singleton, or helper without an eviction or release
  owner.

## Verification

Use the focused reference, a diff review of allocation/release ownership, and a
manual or automated scenario covering the affected lifecycle transition.
