---
keyflow_id: sys_scripted_agent_workflow
status: review
type: human-reviewed-needed
---

# Scripted Agent Workflow

Use when an agent task should be resolved by an executable workflow route instead
of only by reading prose. For multi-step tasks, this route generation is
mandatory when the script is available. The script is the command manifest
generator. The documents remain the source of truth for judgment, constraints,
and verification detail.

## Purpose

Simple or repeated workflows should be represented as a small Python script when
manual routing would create inconsistent behavior across agents. The script
selects the workflow, platform cards, concern cards, and gates for a command.
The agent then reads the generated route and performs the work in the target
repo.

## Default Script

Run this shared router for every multi-step task when it exists:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route <command> --request "<USER_REQUEST>" [--platform <platform>] [--concern <concern>]
```

The route command requires request intake evidence. Pass the current user
request with `--request`, or pass `--request-classified` only after the request
was already classified or answered. If the request is a direct question, the
script blocks routing so the agent answers before editing or running project
commands.

When the request clarity or correct command profile is uncertain, classify first:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py classify "<request text>"
```

`classify` outputs the clarity label, effort level, recommended route command,
whether a question drill is needed, response mode, and a short reason. Use the
recommended route as the `<command>` argument to `route`. If `response_mode:
answer_first`, answer the user before routing or editing. If `question_drill:
true`, run the recommended route (typically `triage` or `ambiguity`) with
`--request` and ask only the missing blocker questions before proceeding.

Discover the supported values from the script itself:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py list
```

Current command profiles:

- `ambiguity`
- `bugfix`
- `docs`
- `docs-review`
- `feature`
- `multi-agent`
- `planning`
- `prd`
- `product`
- `refactor`
- `release`
- `retrospective`
- `review`
- `task`
- `triage`

Current platform values:

- `android`
- `application`
- `ios`
- `server`
- `web`

Current concern values:

- `accessibility`
- `api`
- `asset`
- `assets`
- `auth`
- `background`
- `billing`
- `cache`
- `component`
- `component-api`
- `compose`
- `defensive`
- `dependency`
- `desktop`
- `discovery`
- `effort`
- `error`
- `errors`
- `generated`
- `failure`
- `intake`
- `invite`
- `interaction`
- `module`
- `observability`
- `persistence`
- `react`
- `release`
- `reusability`
- `security`
- `seo`
- `stack`
- `state`
- `structure`
- `swiftui`
- `ui`
- `uikit`
- `wiki`
- `worktree`

Use `--concern` more than once when a task crosses risk areas. Use
`--format json` when another tool should parse the route.

Some concerns are baseline concerns. `stack`, `failure`, and `interaction` are
valid concerns, but their core cards are already loaded by every route through
`CORE_DOCS`; selecting them may add a route note instead of changing the document
list.

Examples:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route product --request "<USER_REQUEST>" --platform android --concern security --concern ui
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route bugfix --request "<USER_REQUEST>" --platform server --concern api
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route docs-review --request "<USER_REQUEST>" --concern wiki
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py validate
```

## Output Contract

The route output is the command manifest for the agent:

- `docs`: read these documents in order before editing or reviewing.
- `request_classification`: classify evidence attached from `--request`, when
  provided.
- `gates`: use these as the task checklist and report against them.
- `gate_ledger`: mark and show each gate as executed when it completes.
- `signal`: traffic-light state for each gate: `PENDING`, `GREEN`, `YELLOW`, or
  `RED`.
- `attempt_limit`: original execution plus one retry for the missed gate.
- `retry_scope`: where recovery resumes; this should be `first_missed_gate`.
- `notes`: apply these routing hints before choosing commands or edits.
- `missing`: stop if this is not empty; fix the playbook reference first.

Markdown output is optimized for direct agent reading. JSON output exposes the
same fields for wrappers, launchers, or CI checks.

## Gate Execution Ledger

For every scripted route, maintain a gate ledger while working:

```text
Attempt for this gate: 1/2
- gate: ...
  signal: PENDING | GREEN | YELLOW | RED
  status: pending | executed | blocked | missed
  evidence: command, file, diff, note, or manual check
```

Do not wait until the final response to reconstruct the ledger from memory. Mark
and show each gate when it is executed.

## Gate Traffic Lights

The traffic light is part of the workflow gate ledger, not a separate report.
Check it at two points:

1. Immediately after each gate or task step completes.
2. Before final report, commit, release, or handoff.

Use these meanings:

- `PENDING`: the gate has not been reached yet.
- `GREEN`: the gate was executed and has evidence.
- `YELLOW`: the gate is blocked, paused, or waiting for approval; do not report
  completion.
- `RED`: the gate was missed or has no evidence after it should have run; follow
  missed-gate recovery.

After each completed gate or task step, emit a short progress signal in the
active conversation or handoff record:

```text
Gate signal: GREEN | gate: <gate> | evidence: <command, file, diff, note, or manual check> | next: <next gate>
```

Keep the signal short. It exists so humans and later agents can notice missed
gates immediately instead of discovering them only in the final report.

Before finalizing, compare the route's `gates` with the ledger:

- Every required gate must be marked `executed` with evidence.
- Every required gate must be `GREEN` before completion is reported.
- `YELLOW` can pause or hand off work, but it cannot be called complete.
- If any required gate is missing, do not continue finalization.
- Treat a missing gate as an execution error even when the final code or docs
  look correct.
- If a route gate is truly irrelevant, stop and correct the route before
  editing; do not silently skip the gate inside a completion report.

## Missed Gate Recovery

If the agent missed any required gate:

1. Stop the current attempt before final report, commit, release, or handoff.
2. Identify the exact gate that was skipped and what work happened after it.
3. Resume at the first missed gate only; do not restart the whole route.
4. Roll back only dependent agent-made changes after the missed gate when safe.
   Preserve pre-existing user changes and ask before destructive cleanup.
5. Re-execute the missed gate once, then refresh any downstream gate evidence
   that depended on work after the missed gate.
6. Run `workflows/retrospective-learning.md` because at least one gate was
   missed.

The missed gate gets one retry: original execution plus one recovery pass. If
the recovery pass misses that gate again, stop and report the blocker, the
missed gate, the rollback status, and the retrospective summary.

## Command Profiles

The current script exposes these stable command profiles:

- `docs-review`: documentation review with wiki/doc-maintenance checks.
- `task`: general multi-step agent work.
- `ambiguity`: classify blockers, researchable unknowns, assumptions, and
  out-of-scope items before planning or implementation.
- `prd`: produce or update a PRD/product requirements note before ARD or code.
- `product`: PRD -> ARD -> review -> code -> review -> tests -> UI tests ->
  commit readiness.
- `feature`: scoped feature implementation.
- `bugfix`: reproduce, isolate, fix, and regression-check.
- `refactor`: behavior-preserving cleanup.
- `docs`: documentation-only update.
- `planning`: research, compare, and recommend before implementation.
- `review`: review and commit-readiness check.
- `multi-agent`: delegated or parallel agent work with explicit write scopes.
- `release`: packaging, deployment, migration, or rollback-sensitive work.
- `retrospective`: capture a reusable lesson after a task or incident.

## Agent Consumption Rule

For a multi-step task:

1. Identify the target repo and repo-local instructions.
2. Run the workflow router before selecting task documents, editing, reviewing,
   committing, or reporting completion.
3. Read the route output as the task command manifest.
4. Load the listed documents in order.
5. Follow the listed gates before editing, reviewing, testing, or committing.
6. Execute project commands only from trusted repo-local instructions.
7. Report verification and residual risk against the route gates.

If the script output conflicts with repo-local instructions, repo-local
instructions win. If the route is missing a concern that the task clearly touches,
add the concern manually and report the gap.

If the workflow router is unavailable, rejects a route, or cannot run, stop and
report the blocker before continuing. Use prose-only routing from `index.md`
only for simple answer-only work or after the user explicitly accepts the
fallback.

## Script Creation Rule

Create or update a Python workflow script when all of these are true:

- The workflow is repeated across projects or agent runtimes.
- The steps can be represented as command profiles, document routes, gates, or
  checklists.
- The script can run without network access and without project-specific secrets.
- The script improves consistency without hiding judgment from the agent.

Do not put product-specific paths, credentials, private service names, local
branch names, or repo-only commands in a shared workflow script. Keep those in
repo-local instructions or repo-local scripts.

## Script Safety

Shared workflow scripts should default to route generation and validation. They
should not execute arbitrary project commands, mutate a repo, install
dependencies, or call external services unless a repo-local trusted wrapper asks
for that behavior explicitly.

Every shared workflow script should support a validation mode that checks its
referenced documents or profiles. Agents should run validation after changing the
script or adding/removing routed documents.

## Handoff Output

When a scripted route was used, include this in the final report:

```text
Workflow route:
- command: ...
- platform: ...
- concerns: ...

Verified:
- python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py validate
- ...task-specific checks...

Gate ledger:
- signal: GREEN / gate: ... / evidence: ...
```

## Stop If

- The script references missing documents or stale command profiles.
- The script route conflicts with repo-local instructions on security, data,
  release, cost, or verification.
- The route omits a platform or concern that the task clearly touches.
- The script would need to mutate the target repo, execute project commands,
  install dependencies, deploy, spend money, or access credentials.
