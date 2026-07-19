---
keyflow_id: sys_workflows_retrospective_learning_md_skill
status: stable
type: ai-generated
---

# Retrospective Learning Workflow

Use at the closeout of every workflow, when a required hook or gate failed, or
when completed work exposed a reusable gap in a skill the agent actually used.
This bundle is the single owner of the failure-repair and skill-learning
automation boundary.

## Read

- `references/current-guidance.md` for the two-flow decision boundary.
- `references/failure-repair.md` only after a required hook or gate fails.
- `references/skill-feedback.md` for the required closeout check, after
  successful work reveals a reusable skill gap, or during a bounded
  skill-maintenance task.
- Related `SKILL.md` entrypoints named by the reference before loading their detailed references.

## Process

1. Classify the event as blocking failure repair or successful-task closeout.
2. Open only the matching focused reference.
3. Keep failure repair inside the bounded repair-and-resume cycle.
4. After task verification and review, but before finish, inspect the skills
   actually loaded and applied and complete the required `retrospective check`.
5. Record the exact fields `skills_checked`, `outcome`, and `observation`.
   `outcome` must be `no_reusable_gap`, `reusable_gap`, or `no_skill_used`.
   `observation` must be `not_needed`, `recorded`, or `deferred`.
   Pair `no_reusable_gap` and `no_skill_used` with `not_needed`; pair
   `reusable_gap` with `recorded` or `deferred`. A reusable gap may produce at
   most one content-free observation tied to an actually used skill.
6. Keep observation storage, curation, review, staging, and later canonical
   maintenance separate and non-blocking. They remain outside required finish
   gates even though the retrospective check itself is required.

## Do Not

- Do not look for legacy flat compatibility paths; load this skill bundle as the canonical context-loading target.
- Do not load broad references for unrelated work just because this skill was nearby in the route.
- Do not let a successful-task feedback write, review, or promotion block task completion.
- Do not skip the retrospective check merely because no reusable gap is
  expected; record `no_reusable_gap` or `no_skill_used` explicitly.
- Do not treat prose keywords as truth, recurrence, or promotion evidence.
- Do not let an observation hook, curator, or reviewer mutate a canonical skill.
- Do not collapse observation, deterministic curation, bounded review, staged
  patching, and canonical maintenance into one execution.

## Verification

- If route wiring changes, confirm the route loads this `SKILL.md` entrypoint.
- If detailed guidance changes, validate links and frontmatter for all three references.
- If routing changes, prove every route requires `retrospective check`, its
  structured evidence is validated, and every skill-learning hook remains
  optional.
- Prove successful-task feedback remains non-blocking when storage, tokens, or
  a reviewer are unavailable.
- Prove only later staged maintenance can write canonical skill files, subject
  to its verification and approval policy.
