---
keyflow_id: sys_agent_task_lifecycle_workflow
status: review
type: human-reviewed-needed
---

# Agent Task Lifecycle Workflow

Use for any agent task, including implementation, review, documentation,
debugging, planning, local tool inspection, and operational handoff.

This is the agent-level workflow. It decides which development, review, release,
or task-specific workflow to load next.

## Read

- `common/agent-operating-skill.md`
- `common/agent-editing-safety.md`
- `common/local-tools.md` when commands or local tools matter
- `common/verification-policy.md` when the task has a checkable result
- `index.md` to select only task-specific cards

## Steps

1. Intake: identify the user goal, target project, task type, constraints, and whether the user asked for edits or only analysis.
2. Local rules: read repo-local instructions before project-specific work.
3. Risk scan: mark touched surfaces such as secrets, external state, auth, billing, data, release, generated files, dependencies, or local tools.
4. Route: choose the smallest workflow and cards from `index.md`; do not load the whole library by default.
5. Inspect: read existing code, docs, tests, commands, and current user changes before editing or judging.
6. Decide: make a reasonable assumption when safe; ask only when ambiguity changes result or risk.
7. Act: execute the scoped work with periodic progress updates for long tasks.
8. Verify: collect evidence with the narrowest reliable command or manual check.
9. Review: inspect the final diff, output, or artifact against the request and risks.
10. Report: state what changed or was found, verification status, skipped checks, and residual risk.

## Route To

- Product or feature delivery with PRD/ARD gates: `workflows/product-architecture-delivery.md`
- Lower-level coding work: `workflows/development-cycle.md`
- Feature behavior: `workflows/feature-implementation.md`
- Bug or regression: `workflows/bugfix-debugging.md`
- Refactor or cleanup: `workflows/refactor-cleanup.md`
- Release-sensitive work: `workflows/release-readiness.md`
- Final review or commit: `workflows/review-and-commit.md`
- Repeatable lesson after task, handoff, incident, or missed signal:
  `workflows/retrospective-learning.md`
- Long-running, interrupted, or transferred work: `workflows/agent-handoff-continuation.md`

## Stop If

- The target project cannot be identified safely.
- Required repo-local instructions or referenced task documents are unavailable.
- The task requires external-state changes without clear user approval.
- The same blocker repeats and no meaningful progress is possible without user
  input or an external change.
