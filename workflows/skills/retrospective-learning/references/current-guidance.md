---
keyflow_id: sys_retrospective_learning_workflow
status: stable
type: human-reviewed-needed
---

# Retrospective Learning Decision Boundary

This document owns the separation between failure recovery and successful-task
skill learning. They share a desire to prevent repeated mistakes, but they do
not share a trigger, completion effect, or automation budget.

## Choose One Flow

| Event | Flow | Completion effect | Detailed reference |
| --- | --- | --- | --- |
| A required hook, gate, or finish check fails | Failure repair | Blocking | `failure-repair.md` |
| A successful task reveals a reusable gap in a skill actually used | Skill observation | Non-blocking | `skill-feedback.md` |

Failure repair protects the current task. It diagnoses the failed checkpoint,
improves a durable enforcement surface, verifies the repair, and resumes once.

Skill learning improves future tasks through separate stages: observation,
deterministic curation, bounded review, staged patch, and later canonical
maintenance. Successful work emits at most one content-free observation tied
to a skill actually used. It does not create or edit guidance. Missing storage,
token budget, reviewer capacity, or maintenance capacity defers the side
channel and never changes a successful finish result.

## Ordering

1. Run the required task gates and finish check.
2. If one fails, stop and use failure repair. Do not also treat that failure as
   ordinary successful-task feedback.
3. If the task succeeds, ask one bounded skill-feedback question. Emit only a
   reusable, content-free observation tied to a skill actually used; otherwise
   emit nothing and stop without ceremony.
4. Let a deterministic curator deduplicate observations by opaque occurrence
   key and queue review only after two distinct observations share the exact
   `skill_id + signal` identity.
5. Let a separate bounded reviewer choose `no_change` or `staged_patch`.
6. Apply a staged patch to canonical skill files only in a later bounded
   maintenance task that satisfies verification and approval policy.

## Automation Boundary

- Required gates and failure repair remain fail-closed.
- Skill observation is a best-effort side channel, not a gate and not finish
  evidence.
- Observation hooks only append allowlisted content-free facts; they never
  decide recurrence, queue review directly, or edit canonical guidance.
- Curation is deterministic over structured identities and distinct opaque
  observation ids. It must not infer truth from prose, prompt text, keyword
  matches, or persuasive model output.
- A curator may queue review after two distinct opaque occurrence keys share the
  exact `skill_id + signal` identity. It must not draft or apply a skill edit.
- Curation and retention enforce explicit caps for observations, review-ready,
  staged, and completed records. Terminal pruning also removes the matching
  passive observations so completed decisions cannot be re-queued.
- The reviewer is a separate bounded step and emits only `no_change` or
  `staged_patch`. Reviewer or token unavailability defers review without
  blocking ordinary work.
- A staged patch is not canonical guidance. Canonical writes happen only in a
  later bounded maintenance task with required verification and the applicable
  approval policy.
- `applied` is an observed state, not reviewer prose: it requires an actually
  changed canonical target linked to the staged promotion target and a zero
  exit status from an allowlisted verification kind.
- No successful-task stage may automatically mutate a canonical skill.
- Prefer a focused test, validator, or clearer decision rule over an
  ever-growing list of natural-language exceptions.

## Source Ownership

This skill bundle is the canonical shared owner. Keep `AGENTS.md`, workflow
routes, hooks, and README files as thin consumers of this contract rather than
parallel policy owners. Repo-specific lessons stay in the target repo's local
instructions or source-of-truth docs.
