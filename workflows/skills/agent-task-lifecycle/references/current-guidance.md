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
- `common/local-tools.md` when commands, local tools, runtime usage telemetry,
  or metering evidence matter
- `common/tool-failure-recovery.md` when a command fails
- `common/verification-policy.md` when the task has a checkable result
- `common/definition-of-done.md` before final report, handoff, commit, release,
  or PR creation
- `index.md` to select only task-specific cards

## Agentic Run State

AgentPlaybook supports agentic coding by making the active agent's state,
delegation decision, evidence, and recovery point explicit. Runtime-specific
agents, subagents, or external launchers can use this state to continue,
delegate, review, and recover work without guessing what already happened.

Use this compact state model for multi-step work:

```text
intake -> oriented -> scoped -> acting -> verifying -> reviewing -> done
                                   |-> blocked -> retrospective -> scoped/acting
```

Record the current state, the next transition, and the gate or command evidence
that justified the transition. If the task is interrupted, transferred, or fails
a gate, resume from the last evidenced state instead of reconstructing the work
from memory.

## Steps

1. Intake: identify the user goal, target project, task type, constraints, and
   whether the user asked for edits or only analysis. Classify request clarity
   and effort before loading broad context. If the user asked a direct question,
   answer it before starting work.
2. Local rules: read repo-local instructions before project-specific work.
3. Stack discovery: inspect manifests, lockfiles, wrappers, and repo scripts
   before choosing commands or framework-specific APIs.
4. Risk scan: mark touched surfaces such as secrets, external state, auth,
   billing, data, release, generated files, dependencies, local tools, runtime
   bridges, or usage metering evidence.
5. Route: for multi-step tasks, run `scripts/workflow.py route ... --request
   "<USER_REQUEST>"` before manually choosing workflow cards. Use `index.md`
   only for simple answer-only work or an explicitly accepted fallback when the
   script cannot run.
6. Route docs read: read the route's listed docs before editing, coding,
   reviewing, or running project-specific work. When the route includes
   `route docs read`, record evidence that the routed skill/guidance docs were
   read before code, implementation, or edits. The evidence must match the
   `docs-read` receipt for the preflight route manifest; generic "docs checked"
   wording is a missed gate.
7. Gate ledger: create a ledger for every route gate, mark each gate when it is
   executed, and show a short `SUCCESS` or `FAIL` gate signal after each
   completed or failed gate or task step.
8. Agentic run state: record the current run state, next transition or resume
   point, and the gate/command evidence. This is required before implementation
   work on scripted work-producing routes and before delegating work to
   subagents or parallel sessions.
9. Global lessons: when preflight includes accepted or promoted lessons from
   `~/.agentplaybook/`, check whether any apply to the current task before
   editing or reviewing.
10. Alignment brief: before requirements analysis or modification work, record
   the shared understanding, possible mismatches, and unsupported assumptions or
   minimal blocker questions. Do this even when the task is too small for a full
   PRD or Grill-Me session.
11. Cycle contract: for work-producing routes, record the cycle type,
    input/source scope, allowed and forbidden changes, acceptance or
    verification method, stop condition, and checkpoint or next cycle before
    editing. Keep code review as a separate review cycle unless the current
    route is explicitly review or review-response work.
12. Inspect: read existing code, docs, tests, commands, and current user changes
   before editing or judging.
13. Decide: make a reasonable assumption when safe; ask only when ambiguity
   changes result or risk.
14. Act: execute the scoped work with periodic progress updates for long tasks.
15. Verify: collect evidence with the narrowest reliable command or manual
    check. For usage telemetry, distinguish setup, label, hook, and diagnostic
    evidence from exact queued/imported usage event evidence.
16. Recover: when a command fails, diagnose stdout/stderr and make the smallest
    correction before retrying.
17. Ledger check: before finalizing, compare required gates against executed
    evidence and `SUCCESS`/`FAIL` state. Completion requires every required gate
    to be `🐱🟢 SUCCESS`. If any required gate is missing, blocked, failed, or
    lacks evidence, report `🐱🔴 FAIL` and follow missed-gate recovery in
    `workflows/scripted-agent-workflow.md`.
18. Definition of Done: before final report, handoff, commit, release, or PR
    creation, compare the final diff and evidence against
    `common/definition-of-done.md`.
19. Retrospective restart: when finish-check sets `retrospective_required`, run
    `workflows/retrospective-learning.md`, use or update the generated global
    lesson candidate when safe, then restart at the first missed gate or same
    failed scope.
20. Review: inspect the final diff, output, or artifact against the request and
    risks.
21. Report: state what changed or was found, verification status, skipped
    checks, and residual risk.

## Route To

- Product or feature delivery with PRD/ARD gates: `workflows/product-architecture-delivery.md`
- Request clarity, effort routing, or Grill-Me: `workflows/request-triage.md`
- Bounded work cycles and stop conditions: `workflows/cycle-contract.md`
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
- The current agentic run state, resume point, or responsible owner cannot be
  identified after interruption, delegation, or failed-gate recovery.
- The same blocker repeats and no meaningful progress is possible without user
  input or an external change.
