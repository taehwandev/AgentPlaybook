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
- `common/task-intake-effort-routing.md` before loading broad context or using
  deep effort
- `common/stack-discovery.md` when commands, dependencies, runtime, or framework
  APIs matter
- `common/agent-editing-safety.md`
- `common/agent-interaction.md` when a blocker question or approval is needed
- `common/local-tools.md` when commands or local tools matter
- `common/tool-failure-recovery.md` when a command fails
- `common/verification-policy.md` when the task has a checkable result
- `index.md` to select only task-specific cards

## Steps

1. Intake: identify the user goal, target project, task type, constraints, and
   whether the user asked for edits or only analysis. Classify request clarity
   and effort before loading broad context. If the user asked a direct question,
   answer it before starting work.
2. Local rules: read repo-local instructions before project-specific work.
3. Stack discovery: inspect manifests, lockfiles, wrappers, and repo scripts
   before choosing commands or framework-specific APIs.
4. Risk scan: mark touched surfaces such as secrets, external state, auth,
   billing, data, release, generated files, dependencies, or local tools.
5. Route: for multi-step tasks, run `scripts/workflow.py route ... --request
   "<USER_REQUEST>"` before manually choosing workflow cards. Use `index.md`
   only for simple answer-only work or an explicitly accepted fallback when the
   script cannot run.
6. Gate ledger: create a ledger for every route gate, mark each gate when it is
   executed, and show a short traffic-light gate signal after each completed
   gate or task step.
7. Inspect: read existing code, docs, tests, commands, and current user changes
   before editing or judging.
8. Decide: make a reasonable assumption when safe; ask only when ambiguity
   changes result or risk.
9. Act: execute the scoped work with periodic progress updates for long tasks.
10. Verify: collect evidence with the narrowest reliable command or manual check.
11. Recover: when a command fails, diagnose stdout/stderr and make the smallest
    correction before retrying.
12. Ledger check: before finalizing, compare required gates against executed
    evidence and traffic-light state. Completion requires every required gate to
    be `🐱🟢 GREEN`. If any required gate is missing, `🐱🟡 YELLOW`, or
    `🐱🔴 RED`, follow the corresponding pause or missed-gate recovery rule in
    `workflows/scripted-agent-workflow.md`.
13. Review: inspect the final diff, output, or artifact against the request and
    risks.
14. Report: state what changed or was found, verification status, skipped
    checks, and residual risk.

## Route To

- Product or feature delivery with PRD/ARD gates: `workflows/product-architecture-delivery.md`
- Request clarity, effort routing, or question drill: `workflows/request-triage.md`
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
- The user asked a direct question and it has not been answered.
- The task requires external-state changes without clear user approval.
- The same blocker repeats and no meaningful progress is possible without user
  input or an external change.
