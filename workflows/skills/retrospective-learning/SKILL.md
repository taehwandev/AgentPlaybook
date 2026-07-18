---
keyflow_id: sys_workflows_retrospective_learning_md_skill
status: stable
type: ai-generated
---

# Retrospective Learning Workflow

Use when a required hook or gate failed, or when a successful task exposed a
reusable gap in a skill the agent actually used. This bundle is the single
owner of the failure-repair and skill-learning automation boundary.

## Read

- `references/current-guidance.md` for the two-flow decision boundary.
- `references/failure-repair.md` only after a required hook or gate fails.
- `references/skill-feedback.md` only after successful work reveals a reusable
  skill gap, or during a bounded skill-maintenance task.
- Related `SKILL.md` entrypoints named by the reference before loading their detailed references.

## Process

1. Classify the event as blocking failure repair or non-blocking skill feedback.
2. Open only the matching focused reference.
3. Keep failure repair inside the bounded repair-and-resume cycle.
4. For successful work, emit at most one content-free observation tied to an
   actually used skill; emit nothing when there is no reusable signal.
5. Keep curation, review, staging, and later canonical maintenance separate and
   best-effort. They remain outside required finish gates.

## Do Not

- Do not look for legacy flat compatibility paths; load this skill bundle as the canonical context-loading target.
- Do not load broad references for unrelated work just because this skill was nearby in the route.
- Do not let a successful-task feedback write, review, or promotion block task completion.
- Do not treat prose keywords as truth, recurrence, or promotion evidence.
- Do not let an observation hook, curator, or reviewer mutate a canonical skill.
- Do not collapse observation, deterministic curation, bounded review, staged
  patching, and canonical maintenance into one execution.

## Verification

- If route wiring changes, confirm the route loads this `SKILL.md` entrypoint.
- If detailed guidance changes, validate links and frontmatter for all three references.
- If routing changes, prove `post-task learning` is not a required gate and
  every skill-learning hook remains optional.
- Prove successful-task feedback remains non-blocking when storage, tokens, or
  a reviewer are unavailable.
- Prove only later staged maintenance can write canonical skill files, subject
  to its verification and approval policy.
