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
answer_first`, answer the user before routing or editing. When an answer-first
question asks how to start app, product, or feature work, the answer must include
PRD -> ARD -> implementation gates before lower-level coding steps. If
`question_drill: true`, run the recommended route (typically `triage` or
`ambiguity`) with `--request` and ask only the missing blocker questions before
proceeding.

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
- `workflow-setup`

Current platform values:

- `android`
- `application`
- `ios`
- `server`
- `web`

Current concern values:

- `accessibility`
- `aeo`
- `ai-mode`
- `ai-overviews`
- `ai-search`
- `ai-search-optimization`
- `answer-engine`
- `answer-engine-optimization`
- `api`
- `asset`
- `assets`
- `auth`
- `background`
- `billing`
- `cache`
- `canonical`
- `channel`
- `component`
- `component-api`
- `compose`
- `copy`
- `defensive`
- `dependency`
- `desktop`
- `discovery`
- `effort`
- `error`
- `errors`
- `generated`
- `failure`
- `generated`
- `generative-ai`
- `generative-ai-search`
- `geo`
- `intake`
- `invite`
- `interaction`
- `llms`
- `llms-txt`
- `module`
- `observability`
- `open-graph`
- `persistence`
- `platform`
- `prose`
- `react`
- `release`
- `reusability`
- `robots`
- `security`
- `seo`
- `sitemap`
- `stack`
- `state`
- `structure`
- `structured-data`
- `swiftui`
- `ui`
- `uikit`
- `voice`
- `widget`
- `wiki`
- `worktree`
- `writing`

Use `--concern` more than once when a task crosses risk areas. Use
`--format json` when another tool should parse the route.

The router also infers the canonical `seo` concern from explicit public
discovery keywords in `--request`, such as SEO, AI search, AEO, GEO, AI
Overviews, AI Mode, `llms.txt`, sitemap, robots, canonical, Open Graph, and
structured data. Inference is a convenience, not a replacement for adding
specific `--concern` values when local context shows the risk.

Some concerns are baseline concerns. `stack`, `failure`, and `interaction` are
valid concerns, but their core cards are already loaded by every route through
`CORE_DOCS`; selecting them may add a route note instead of changing the document
list.

Examples:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route product --request "<USER_REQUEST>" --platform android --concern security --concern ui
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route bugfix --request "<USER_REQUEST>" --platform server --concern api
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route docs-review --request "<USER_REQUEST>" --concern wiki
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route product --request "Show me how we build an app feature here" --platform android --concern ui
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py validate
```

Do not force broad app/product requests through the `feature` route. The router
blocks `feature` when request classification recommends `product`, because that
would skip the PRD and ARD gates.

## Output Contract

The route output is the command manifest for the agent:

- `docs`: read these documents in order before editing or reviewing.
- `request_classification`: classify evidence attached from `--request`, when
  provided.
- `gates`: use these as the task checklist and report against them.
- `gate_ledger`: mark and show each gate as executed when it completes.
- `signal`: public state for completed or failed gates: `SUCCESS` or `FAIL`.
- `attempt_limit`: original execution plus one retry for the missed gate.
- `retry_limit`: maximum recovery retries for the missed gate; this should be
  `1`.
- `retry_scope`: where recovery resumes; this should be `first_missed_gate`.
- `notes`: apply these routing hints before choosing commands or edits.
- `missing`: stop if this is not empty; fix the playbook reference first.

Markdown output is optimized for direct agent reading. JSON output exposes the
same fields for wrappers, launchers, or CI checks.

## Automatic Gates

Work-producing routes must include the common gates below even when an individual
command profile forgets them:

- `ambiguity check`: classify unknowns before implementation. If any blocker
  can change behavior, scope, risk, acceptance criteria, or verification, stop
  and ask the maintainer before editing. Do not continue with silent invented
  assumptions.
- `documentation`: update or create the relevant source-of-truth docs, or record
  why docs are not applicable or intentionally unchanged.
- `tests`: add, update, or run the closest useful test/check for code work. A
  skipped test must include the command skipped, reason, and residual risk.
- `multi-agent split decision`: for code work, choose parallel/multi-agent work
  when scopes are disjoint and useful. If work stays serial, record why the
  change is too small, same-file, contract-bound, or otherwise not safe to split.

`agent-finish-check.py` validates evidence for these gates. Missing evidence or
empty phrases such as "done" are not enough.

## Parallel Consumption

After `route` returns a document and gate manifest, optimize for parallel
read-only work:

- Read independent route documents in parallel when the runtime supports it.
  Do not serialize `sed`, `cat`, `rg`, `find`, stack inspection, git status, or
  other read-only commands unless one result decides whether another command is
  needed.
- `agent-preflight.py` may run in parallel with read-only orientation after the
  request has been answered or classified. Treat it as a gate dependency:
  implementation, setup, update, fix, commit, push, release, migration, and
  external-state changes must wait until preflight succeeds.
- Do not parallelize commands that write the same evidence file, mutate project
  files, stage or commit changes, install/update guardrails, run fixers, publish
  artifacts, deploy, migrate data, or depend on one another's output.
- If a parallel read-only command fails, classify the failure before editing.
  Do not continue only because the other parallel commands succeeded.

## Gate Execution Ledger

For every scripted route, maintain a gate ledger while working:

```text
Attempt for this gate: 1/2
- gate: ...
  signal: SUCCESS | FAIL
  status: executed | failed | missed
  evidence: command, file, diff, note, or manual check
```

Do not wait until the final response to reconstruct the ledger from memory.
Report a gate only when it succeeds or fails. Do not emit a public third state.

## Gate Signals

Gate signals are part of the workflow gate ledger, not a separate report. Check
them at two points:

1. Immediately after each gate or task step completes.
2. Before final report, commit, release, or handoff.

Use these meanings:

- `🐱🟢 SUCCESS`: the gate was executed and has evidence.
- `🐱🔴 FAIL`: the gate was missed, blocked, failed, or has no evidence after it
  should have run; follow missed-gate recovery.

After each completed gate or task step, emit a short progress signal in the
active conversation or handoff record:

```text
Gate signal: 🐱🟢 SUCCESS | gate: <gate> | evidence: <command, file, diff, note, or manual check> | next: <next gate>
```

Keep the signal short. It exists so humans and later agents can notice missed
gates immediately instead of discovering them only in the final report. Use only
`🐱🟢 SUCCESS` or `🐱🔴 FAIL` in human-visible text. Keep the plain `SUCCESS` or
`FAIL` value inside machine-readable fields so automation can still parse the
ledger.

Before finalizing, compare the route's `gates` with the ledger:

- Every required gate must be marked `executed` with evidence.
- Every required gate must be `🐱🟢 SUCCESS` before completion is reported.
- If the route includes a `review hook` gate, run
  `python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py review ...` and record
  the hook result as that gate's evidence. Do not replace it with a memory-only
  manual review unless the hook is unavailable and the fallback is reported.
- If any required gate is missing, do not continue finalization.
- Treat a missing gate as an execution error even when the final code or docs
  look correct.
- If a route gate is truly irrelevant, stop and correct the route before
  editing; do not silently skip the gate inside a completion report.

## Executable Evidence Wrappers

When available, use the wrapper scripts to make the route and gate ledger
auditable instead of relying on memory.

The route output also contains a `Required Hooks` section. Treat it as the
workflow's executable checklist:

- `start` runs preflight before edits, reviews, commits, or completion reports.
- `review` runs after meaningful edits and before finish, commit, release, or
  handoff when the route marks it required.
- `finish` runs before final report, commit, release, or handoff and verifies
  route gate evidence.

Before editing, reviewing, committing, or reporting completion:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py start --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> --command <command> --request "<USER_REQUEST>" [--platform <platform>] [--concern <concern>]
```

`agent-hook.py start` delegates to `agent-preflight.py` and writes the same
preflight evidence. Calling `agent-preflight.py` directly is acceptable only as
a lower-level wrapper path when the start hook is unavailable.

Before final report, commit, release, or handoff:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py finish --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> --gate "request intake=<evidence>" --gate "orient=<evidence>" --gate "scope=<evidence>" --gate "act=<evidence>" --gate "verify=<evidence>" --gate "report=<evidence>"
```

`agent-hook.py finish` delegates to `agent-finish-check.py`. Calling
`agent-finish-check.py` directly is acceptable only as a lower-level wrapper path
when the finish hook is unavailable.

`agent-preflight.py` records the route manifest, current git status, and
VibeGuard audit result in `<TARGET_REPO>/.agentplaybook/preflight.json`.
When `--request-classified` is used, it must also record
`--classification-evidence`; otherwise request intake is treated as skipped.
`agent-finish-check.py` requires evidence for every route gate, runs
`workflow.py validate`, runs `git diff --check`, reruns VibeGuard, and writes
`<TARGET_REPO>/.agentplaybook/finish.json`.
It also writes `gate_signals`, `missed_gates`, and
`retrospective_required`. If the route classification or stored request text
requires a question drill, the finish check must receive drill evidence through
a gate such as `question drill if needed=<evidence>` or
`ask blockers=<evidence>`. Missing drill evidence is a `🐱🔴 FAIL` signal and
blocks completion until missed-gate recovery and retrospective learning run.
Human-visible wrapper output uses only `🐱🟢 SUCCESS` and `🐱🔴 FAIL`.

Treat missing wrapper evidence as non-compliant. If the wrappers are unavailable,
the agent must still run the same underlying checks manually and report the
fallback explicitly. VibeGuard `Needs review` cannot be called complete unless
the state is reported and an explicit `--allow-vibeguard-review` reason is
recorded. Command failure, `🐱🔴 FAIL`, missing route evidence, or missing
VibeGuard output remains a blocker.

## Missed Gate Recovery

If the agent missed any required gate:

1. Stop the current attempt before final report, commit, release, or handoff.
2. Identify the exact gate that was skipped and what work happened after it.
3. Resume at the first missed gate only; do not restart the whole route.
4. Roll back only dependent agent-made changes after the missed gate when safe.
   Preserve pre-existing user changes and ask before destructive cleanup.
5. Re-execute the missed gate one time, then refresh any downstream gate
   evidence that depended on work after the missed gate.
6. If the single retry fails, run `workflows/retrospective-learning.md` before
   any handoff, commit, release, or completion report.

The missed gate gets one recovery retry: original execution plus one recovery
pass. If that recovery pass misses the gate again, stop and report the blocker,
the missed gate, the rollback status, and the retrospective summary.

## Command Profiles

The current script exposes these stable command profiles:

- `triage`: request clarity, effort routing, and blocker-question drill.
- `workflow-setup`: local agent prompt, hook, workflow label bridge, or metering setup.
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
- signal: SUCCESS / gate: ... / evidence: ...
```

## Stop If

- The script references missing documents or stale command profiles.
- The script route conflicts with repo-local instructions on security, data,
  release, cost, or verification.
- The route omits a platform or concern that the task clearly touches.
- The script would need to mutate the target repo, execute project commands,
  install dependencies, deploy, spend money, or access credentials.
