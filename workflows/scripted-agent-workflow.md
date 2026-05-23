---
keyflow_id: sys_scripted_agent_workflow
status: review
type: human-reviewed-needed
---

# Scripted Agent Workflow

Use when an agent task should be resolved by an executable workflow route instead
of only by reading prose. The script is the command manifest generator. The
documents remain the source of truth for judgment, constraints, and verification
detail.

## Purpose

Simple or repeated workflows should be represented as a small Python script when
manual routing would create inconsistent behavior across agents. The script
selects the workflow, platform cards, concern cards, and gates for a command.
The agent then reads the generated route and performs the work in the target
repo.

## Default Script

Use this shared router when it exists:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route <command> [--platform <platform>] [--concern <concern>]
```

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
- `product`
- `refactor`
- `release`
- `retrospective`
- `review`
- `task`

Current platform values:

- `android`
- `application`
- `ios`
- `server`
- `web`

Current concern values:

- `accessibility`
- `api`
- `auth`
- `background`
- `billing`
- `cache`
- `defensive`
- `dependency`
- `generated`
- `failure`
- `invite`
- `interaction`
- `observability`
- `persistence`
- `release`
- `security`
- `stack`
- `ui`
- `wiki`
- `worktree`

Use `--concern` more than once when a task crosses risk areas. Use
`--format json` when another tool should parse the route.

Examples:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route product --platform android --concern security --concern ui
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route bugfix --platform server --concern api
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route docs-review --concern wiki
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py validate
```

## Output Contract

The route output is the command manifest for the agent:

- `docs`: read these documents in order before editing or reviewing.
- `gates`: use these as the task checklist and report against them.
- `gate_ledger`: mark each gate as executed with evidence before final report.
- `attempt_limit`: maximum total attempts for a route after a missed gate.
- `notes`: apply these routing hints before choosing commands or edits.
- `missing`: stop if this is not empty; fix the playbook reference first.

Markdown output is optimized for direct agent reading. JSON output exposes the
same fields for wrappers, launchers, or CI checks.

## Gate Execution Ledger

For every scripted route, maintain a gate ledger while working:

```text
Attempt: 1/2
- gate: ...
  status: executed | missed
  evidence: command, file, diff, note, or manual check
```

Do not wait until the final response to reconstruct the ledger from memory. Mark
each gate when it is executed.

Before finalizing, compare the route's `gates` with the ledger:

- Every required gate must be marked `executed` with evidence.
- If any required gate is missing, do not continue finalization.
- Treat a missing gate as an execution error even when the final code or docs
  look correct.
- If a route gate is truly irrelevant, stop and correct the route before
  editing; do not silently skip the gate inside a completion report.

## Missed Gate Recovery

If the agent missed any required gate:

1. Stop the current attempt before final report, commit, release, or handoff.
2. Identify the exact gate that was skipped and what work happened after it.
3. Roll back only agent-made changes from the failed attempt when safe. Preserve
   pre-existing user changes and ask before destructive cleanup.
4. Restart from the first gate and keep a new ledger.
5. Run `workflows/retrospective-learning.md` because at least one gate was
   missed.

Do not exceed two total attempts. If the second attempt misses any required gate,
stop and report the blocker, the missed gate, the rollback status, and the
retrospective summary.

## Command Profiles

The current script exposes these stable command profiles:

- `docs-review`: documentation review with wiki/doc-maintenance checks.
- `task`: general multi-step agent work.
- `ambiguity`: classify blockers, researchable unknowns, assumptions, and
  out-of-scope items before planning or implementation.
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
2. Run the workflow router when available.
3. Read the route output as the task command manifest.
4. Load the listed documents in order.
5. Follow the listed gates before editing, reviewing, testing, or committing.
6. Execute project commands only from trusted repo-local instructions.
7. Report verification and residual risk against the route gates.

If the script output conflicts with repo-local instructions, repo-local
instructions win. If the route is missing a concern that the task clearly touches,
add the concern manually and report the gap.

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
- gate: ... / executed / evidence: ...
```

## Stop If

- The script references missing documents or stale command profiles.
- The script route conflicts with repo-local instructions on security, data,
  release, cost, or verification.
- The route omits a platform or concern that the task clearly touches.
- The script would need to mutate the target repo, execute project commands,
  install dependencies, deploy, spend money, or access credentials.
