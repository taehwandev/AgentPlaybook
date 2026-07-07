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

## Agentic Control Plane

The workflow script is the agentic coding control plane for AgentPlaybook. It
gives the active agent a route manifest, required documents, required gates,
run-state expectations, delegation policy, and evidence policy so Codex, Claude
Code, Gemini CLI, GitHub Copilot coding agent, Cursor, Aider, Devin, Replit
Agent, or another coding agent can work with the same operating discipline.

Agentic behavior comes from connecting that manifest to execution: selecting
the right route, recording run state, deciding whether to work serially or
delegate to subagents, collecting evidence, recovering from missed gates, and
updating durable lessons when the same failure repeats. When the runtime
supports subagents or launchers, use the split decision and run-state evidence
as the delegation contract.

## Default Script

Run this shared router for every multi-step task when it exists:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route <command> --request "<USER_REQUEST>" [--platform <platform>] [--concern <concern>]
```

The route command requires request intake evidence. Pass the current user
request with `--request`, or pass `--request-classified` only after the request
was already classified or answered and include `--classification-evidence`
with the prior classification, answer-first handling, or user-visible alignment
checkpoint. Direct `workflow.py route --request-classified` without
classification evidence is a workflow failure. If the request is a direct
question, the script blocks routing so the agent answers before editing or
running project commands. Work routes require evidence that proves the request
is actionable, such as `clear-exact`, `clear-scoped`, `answered ... separate
actionable`, or `blockers resolved`; weak evidence such as `classified` or
`done` is not sufficient. Generic resolution markers such as `clarified` or
`no blockers` are also insufficient unless they name the resolved scope,
decision, blocker-question outcome, or remaining separate action.

When the request clarity or correct command profile is uncertain, classify first:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py classify "<request text>"
```

`classify` outputs the clarity label, effort level, recommended route command,
whether the Grill-Me protocol is needed, response mode, and a short reason. Use
the recommended route as the `<command>` argument to `route`. If `response_mode:
answer_first`, answer the user before routing or editing. When an answer-first
question asks how to start app, product, or feature work, the answer must include
PRD -> ARD -> implementation gates before lower-level coding steps. If
`grill_me: true` or legacy `question_drill: true`, run the recommended route
(typically `triage` or `ambiguity`) with `--request`, run a Grill-Me
`/grilling` session before implementation, and ask only the missing blocker
questions before proceeding. Prefer an installed Grill-Me skill when available;
otherwise use the built-in protocol from `common/task-intake-effort-routing.md`
and record its output.

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
- `local-tools`
- `llms`
- `llms-txt`
- `metering`
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
- `telemetry`
- `ui`
- `uikit`
- `usage`
- `verification`
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

Use the `metering`, `usage`, or `telemetry` concern for local runtime usage
metering, workflow label bridges, or Spill-related work. Do not use the
`tokens` concern for usage metering; `tokens` routes design-system token work.

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
- `parallel_execution`: use this phase manifest to decide what can run in
  parallel and what must stay serial. It is the executable hint for runtimes
  that otherwise treat the gate list as one ordered chain.
- `attempt_limit`: original execution plus one retry for the missed gate.
- `retry_limit`: maximum recovery retries for the missed gate; this should be
  `1`.
- `retry_scope`: where recovery resumes; this should be `first_missed_gate`.
- `notes`: apply these routing hints before choosing commands or edits.
- `missing`: stop if this is not empty; fix the playbook reference first.

Markdown output is optimized for direct agent reading. JSON output exposes the
same fields for wrappers, launchers, or CI checks.

## Automatic Gates

Work-producing, documentation, release, review, and retrospective routes must
include the relevant common gates below even when an individual command profile
forgets them:

- `route docs read`: after routing and before code, implementation, review,
  edit, triage, or ambiguity work, read the route's `required_docs` / `Read
  First` list. Treat `reference_docs` / `Reference On Demand` as lazy context;
  open one only when the current task touches that concern, platform, gate, or
  verification path. Evidence must say that the required skill/guidance docs
  were read before work and name the applied rule, criterion, or takeaway used
  for this task, plus the immediate next action that applies it. Merely listing
  documents in the route output, or proving that the receipt matches the route
  manifest, is not evidence that the agent consumed or used them.
  Run the `docs-read` hook after preflight and before edits so finish-check can
  compare its receipt against the current preflight evidence file, route
  manifest, and required-document count. The hook must receive `--takeaway` and
  `--next-action`; generic wording such as "checked docs", "read guidance", or
  "receipt matched the manifest" is a missed gate.
- Required gates cannot pass by recording a skip, not-applicable,
  unable-to-run, deferred, or follow-up reason unless that specific gate allows
  the outcome and the evidence names the allowed reason. Evidence that names an
  unresolved, must-fix, should-fix, blocking, or deferred issue must report
  `FAIL`; do not convert it into a successful note. Use missed-gate recovery
  and retrospective learning to make the next action path fix the issue.
- `source docs`: before feature, product, build, bugfix, refactor,
  simplification, workflow-setup, release, shipping, or general task
  implementation, search for repo-local source-of-truth documents that match
  the work type. Sources may be PRD, spec, ARD, issue, design note, task doc,
  ADR/RFC, module README, API contract, runbook, migration note, release note,
  test plan, skill/platform/workflow card, agent instruction, or equivalent
  product/source-of-truth document. Open and read any matching source before
  code or edits. If none exists, record the no-source result and decide whether
  the smallest useful artifact must be created before code or whether the
  current user request is enough for a no-durable-doc slice. Evidence must name
  the discovered source or the no-source result and say how it affected the
  work or documentation artifact decision.
  This is a pre-edit hard gate. Do not start implementation first and
  reconstruct the source-doc search afterward.
- `documentation impact`: before code, implementation, install/repair, or other
  edit work, decide whether the requested change affects durable documentation.
  This is the thinking checkpoint, not the final doc-update proof. Evidence
  must name the selected artifact class, affected doc path or doc class, the
  intended decision (`updated`, `created`, `unchanged`, or `not applicable`),
  and why the changed behavior, workflow policy, public contract, operator
  action, or acceptance criteria do or do not require a documentation update.
  `Not applicable`, `unchanged`, or `no docs` is valid only with a
  no-durable-doc reason such as answer-only, purely local, mechanical, no
  public contract, no operator action, or no acceptance criteria. If source
  docs are missing and the task changes durable behavior, create or update the
  smallest useful artifact instead of treating documentation as absent. Do not
  wait until finish to discover that docs were relevant.
- `ambiguity check`: classify unknowns before implementation. If any blocker
  can change behavior, scope, risk, acceptance criteria, or verification, stop
  and ask the maintainer before editing. Do not continue with silent invented
  assumptions.
- `platform selection`: before PRD, ARD, architecture, or product
  implementation work, choose the affected platform card(s) or record why no
  platform is applicable. Do not write ARD or implementation plans while the
  platform surface is only a note.
- `alignment brief`: before requirements analysis, PRD/product delivery, or
  modification work, show the user a compact same/different/assumption summary.
  This is required even when the Grill-Me protocol is not needed. It should
  reduce later rework, not become a long questionnaire.
- `documentation`: update or create the relevant source-of-truth docs, or record
  why docs are not applicable or intentionally unchanged. Evidence must name the
  documentation decision, the affected source-of-truth doc path or doc class,
  and the reason the decision matches the behavior, workflow policy, public
  contract, operator action, or durable acceptance criteria changed.
- `tests`: add, update, or run the closest useful test/check for code work. A
  skipped test must include the command skipped, reason, and residual risk.
- `boundary plan`: before code edits, name the owned boundary, file/module
  scope, caller-facing contract, or existing same-file scope, plus the nearest
  verification that will prove the change.
- `multi-agent split decision`: for code work, decide whether to spawn
  subagents/parallel workers. Use them when owned files/modules are disjoint and
  the shared contract is stable. If work stays serial, record why the change is
  too small, same-file, contract-bound, or otherwise not safe to split.
- `agentic run state`: for work-producing or multi-agent routes, record the
  current state, the next transition or resume point, and the gate/command
  evidence that justifies that transition. This is the workflow's memory for
  continuation, retry, review, delegation, and retrospective restart; route
  output alone is not execution evidence.
- `cycle contract`: for work-producing routes, state the current cycle type,
  input/source scope, allowed and forbidden changes, acceptance or verification
  method, stop condition, and next cycle/checkpoint before editing. This turns
  the task into one bounded cycle instead of an open-ended loop. Code review is
  a separate review cycle; implementation work may prepare for review, but must
  not claim that review happened unless a review route actually ran.
- `side-effect audit`: after implementation and before final verification or
  handoff, inspect the final diff for unexpected generated files, lockfiles,
  public-contract changes, external-state surfaces, broad formatting churn, and
  unrelated behavior. If investigation finds a possible meaning, policy, route,
  gate, or pass/fail interpretation change, pause for a meaning checkpoint
  before editing unless the fix is mechanical and already covered by explicit
  tests.
- `review readiness`: for docs-review routes, report the reviewed Markdown
  scope's frontmatter readiness, `status`/`type` distribution, and
  human-review queue. Link/frontmatter validity alone is not enough when the
  review is meant to judge whether guidance is ready for broad agent use.

`agent-finish-check.py` validates evidence for these gates. Missing evidence or
empty phrases such as "done" are not enough.

## Workflow Metering Contract

When changing workflow commands, route profiles, hooks, runtime prompt bridges,
permissions, or local metering setup, preserve the workflow label contract:

- every route command in `workflow_catalog.COMMANDS` must have a matching
  `SPILL_ROUTE_LABELS` entry;
- every required workflow action must have a matching `SPILL_ACTION_LABELS`
  entry;
- labels must remain reusable safe slugs, not task text, project names, file
  names, branch names, user names, or private content;
- setup, permission, label, hook-load, mock-payload, and diagnostic signals must
  not be reported as proof of real token usage;
- `workflow.py validate` and the routing tests must fail when a route, action,
  or concern change drops the metering contract.

Use `common/local-tools.md` for the usage evidence boundary. For actual usage
proof, require exact queued/imported local usage event evidence or the runtime's
approved exact-usage success marker; otherwise record no usage event and avoid
private-content reconstruction.

## Parallel Consumption

After `route` returns a document and gate manifest, read the
`parallel_execution` section before starting work. The `gates` list is the
required checklist; `parallel_execution.phases` is the scheduling hint that
shows which parts can overlap safely.

- Read independent route documents in parallel when the runtime supports it.
  Do not serialize `sed`, `cat`, `rg`, `find`, stack inspection, git status, or
  other read-only commands unless one result decides whether another command is
  needed.
- When unrelated dirty files are present, narrow Review Hook checks to the task
  boundary with `--review-path <path>` after the boundary plan names the owned
  files or modules. Pathspec review narrows git status, diff, structure, and
  VibeGuard file scans; VibeGuard uses changed-only fallback when the installed
  CLI does not yet support explicit path filters. Use the default
  `--review-scope working-tree` only when the whole current diff is part of the
  requested review.
- Treat `mode: parallel` phases as safe opportunities for concurrent read-only
  orientation or independent verification, subject to repo-local tool limits.
- Treat `mode: conditional_parallel` phases as parallel only after the route's
  split-decision, role, owned-scope, forbidden-scope, contract, and verification
  gates are recorded. If those cannot be named, execute that phase serially and
  record the concrete reason.
- Treat `mode: serial` phases as ordering barriers. Do not cross them with
  writes, generated artifacts, dependency changes, release config, migrations,
  shared contracts, same-file edits, or final reporting.
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

## Run State Ledger

For work-producing and multi-agent routes, keep a compact run-state line beside
the gate ledger:

```text
run_state: scoped
transition: scoped -> acting
evidence: boundary plan + multi-agent split decision recorded
next: implementation
```

Use these state names unless repo-local workflow defines a stricter model:
`intake`, `oriented`, `scoped`, `acting`, `verifying`, `reviewing`, `done`,
`blocked`, and `retrospective`. Update the state only when the transition has
evidence. After a failed required gate, set the resume point to the first missed
gate or same failed scope instead of restarting unrelated work.

Do not use run-state notes to hide missing gate evidence. A run state is valid
only when the named route gates, commands, checks, or manual observations also
exist.

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

The route may promote additional `required_docs` from the root
`workflow-doc-surfaces.json` map when the request text or known/touched paths
show a specific work surface. Rules may match route command, selected platform,
request text, request path references, explicit `--surface-path` values, and
paths from `git status --short --untracked-files=all`. UI-capable platform
work must be covered as a matrix, not as a one-off Android rule: Android
Compose, Application desktop UI, Flutter widgets, iOS SwiftUI/UIKit, KMP
Compose, Swift design-system UI, and Web React UI should each promote the
matching UI, state, structure, review, visual verification, and performance
guidance. This surface routing is for document selection only: it does not
replace request classification, command/profile selection, repo-local
instructions, or the requirement to record a task-specific docs-read takeaway
before edits.

The route/search layer also maintains a local document graph derived from
Markdown links, compatibility stubs, and `workflow-doc-surfaces.json` document
sets. Natural-language matching should identify seed documents; graph expansion
should then surface directly connected skill entrypoints, detailed references,
and explicit document dependencies. Treat ordinary graph links as
`reference_docs` so broad surfaces do not overload required reading. Promote a
graph neighbor to `required_docs` only when the source declares an explicit
required relation such as frontmatter `requires_docs`.

Natural-language document discovery belongs in the routing/search layer, not in
the hook body. Hooks are enforcement points: they stop work until preflight,
docs-read receipts, and finish evidence exist. The router and `workflow.py
query` must carry the retrieval burden by expanding vague task language into
reusable facets such as cleanup, review, verification, UI feature work, skill
docs, or document routing, using the local document graph to add connected
candidates, then returning candidate `required_docs` and `reference_docs`
before the hook gate checks whether they were actually read.

The command includes task-specific arguments, but persistent runtime permission
prefixes must not. For Codex escalation, request only
`["python3", "/absolute/path/to/AgentPlaybook/scripts/agent-hook.py"]` as the
saved `prefix_rule`; for Claude and AGY, allow only the equivalent absolute
wrapper command plus the runtime's trailing argument wildcard. Never save
`--project`, `--request`, `--gate`, `$HOME`, `$(pwd)`, or user text in the
permission prefix.

`agent-hook.py start` runs the preflight logic in-process and writes the same
preflight evidence. Calling `agent-preflight.py` directly is acceptable only as
a lower-level wrapper path when the start hook is unavailable.

After preflight and before edits, reviews, commits, or completion reports, read
the route's required docs and write the route-doc receipt:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py docs-read --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> --takeaway "<doc-derived rule/takeaway>" --next-action "<immediate task action>"
```

The docs-read hook reads each required doc from the preflight manifest and
writes `<TARGET_REPO>/.agentplaybook/route-docs-read.json` for the default
`preflight.json`, or `<preflight-stem>-route-docs-read.json` for a custom
preflight evidence file. The receipt includes path, size, doc hash, route
fingerprint, required-document count, and diagnostic preflight metadata. Use
`--receipt-output` only when the receipt must be written to a non-default path;
`--output` is a legacy alias for that docs-read receipt path.
Finish-check validates the receipt against the current route required-doc
manifest, preflight evidence path, and preflight evidence hash. If the
preflight file is refreshed, rerun `docs-read` for that preflight instead of
reusing an older receipt with the same route shape. A missing, stale, or
mismatched receipt is a missed `route docs read` gate. A matching receipt alone
is also a missed gate unless the hook records the task-specific required-doc
takeaway and immediate next action.

Before final report, commit, release, or handoff:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py finish --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT>
```

Do not wait until finish to write all gate evidence by hand. The default path
is a structured gate ledger at
`<TARGET_REPO>/.agentplaybook/gate-evidence.json`, bound to the current
preflight evidence hash and route fingerprint. Custom preflight evidence files
use `<preflight-stem>-gate-evidence.json` so parallel jobs do not overwrite one
another's ledger. `agent-hook.py finish` reads that ledger first, then applies
any explicit `--gate "<gate>=<evidence>"` arguments as compatibility overrides.

The `start`, `docs-read`, and `review` hooks record their own successful gate
evidence in the ledger. For gates that only the active agent can prove, batch
structured records instead of spawning one shell process per gate:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py gate-batch --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> --gate-record '[{"gate":"cycle contract","fields":{"cycle_type":"workflow_setup","input_scope":"<safe-source-scope>","allowed_changes":"<safe-scope>","forbidden_changes":"<safe-boundary>","acceptance_criteria":"<safe-criteria>","verification":"<check>","stop_condition":"<condition>","checkpoint":"<handoff-or-next-cycle>"}},{"gate":"boundary plan","fields":{"scope":"<owned-scope>","verification":"<nearest-check>"}}]'
```

Use this ledger to capture what happened, not to craft magic validator prose.
If a structured entry is missing required fields, finish-check should fail and
the recovery is to complete or record the missing gate fact, not to add a vague
sentence. Use `agent-hook.py gate` only for a single immediate gate. Manual
`--gate` arguments are acceptable for one-off fallback or override, but they
should not become the normal finish path.

`agent-hook.py finish` runs the finish-check logic in-process. Calling
`agent-finish-check.py` directly is acceptable only as a lower-level wrapper path
when the finish hook is unavailable.

`agent-preflight.py` records the route manifest, current git status, and
VibeGuard audit result in `<TARGET_REPO>/.agentplaybook/preflight.json`.
It also records a content-free summary of accepted and promoted global lessons
from `~/.agentplaybook/` when that local store exists.
When `--request-classified` is used, it must also record
`--classification-evidence`; otherwise request intake is treated as skipped.
For work routes, that evidence must include a resolved-scope signal rather than
a generic `classified`, `done`, `handled`, `clarified`, or `no blockers`
marker.
`agent-finish-check.py` requires evidence for every route gate, runs
`workflow.py validate`, runs `git diff --check`, uses the task-local VibeGuard
audit cache when both the target project git state and AgentPlaybook rules git
state are unchanged. Failed VibeGuard invocations must not be cached; rerun the
tool after transient failures. Finish-check writes
`<TARGET_REPO>/.agentplaybook/finish.json`.
It also writes `gate_signals`, `missed_gates`, and
`retrospective_required`. When `retrospective_required` is true, it writes a
safe lesson candidate under `~/.agentplaybook/lessons/inbox/` when permitted.
If the route classification or stored request text requires Grill-Me, the finish
check must receive Grill-Me protocol evidence through a gate such as
`grill-me if needed=</grilling session/output evidence>`. Legacy
`question drill if needed=<evidence>` is accepted only when it still names the
Grill-Me protocol, skill, or `/grilling` session and output. Missing Grill-Me
evidence is a `🐱🔴 FAIL` signal and blocks completion until missed-gate
recovery and retrospective learning run.
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
6. If finish-check sets `retrospective_required`, run
   `workflows/retrospective-learning.md`, inspect the generated global lesson
   candidate when available, and restart at the first missed gate or same failed
   scope before any handoff, commit, release, or completion report.
7. If the same missed-gate scope fails again after retrospective restart, stop
   and promote the lesson to shared docs, tests, workflow validation, or hooks
   before continuing.

The missed gate gets one recovery retry: original execution plus one recovery
pass. If that recovery pass misses the gate again, stop and report the blocker,
the missed gate, the rollback status, and the retrospective summary.

## Command Profiles

The current script exposes these stable command profiles:

- `triage`: request clarity, effort routing, and Grill-Me blocker questions.
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
- `commit` / `git_commit`: lightweight local commit preparation. Run review
  first, stop on findings, then record commit readiness for the staged diff.
- `multi-agent`: delegated or parallel agent work with explicit write scopes.
- `release`: packaging, deployment, migration, or rollback-sensitive work.
- `retrospective`: capture a reusable lesson after a task or incident.

## Agent Consumption Rule

For a multi-step task:

1. Identify the target repo and repo-local instructions.
2. Run the workflow router before selecting task documents, editing, reviewing,
   committing, or reporting completion.
3. Read the route output as the task command manifest.
4. Load `required_docs` / `Read First` in order; load `reference_docs` only
   when the task touches that concern, platform, gate, or verification path.
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
