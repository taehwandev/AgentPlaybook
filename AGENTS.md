---
keyflow_id: sys_agent_entrypoint
status: stable
type: human-reviewed
---

# AgentPlaybook Shared Agent Instructions

This file is the entrypoint for agents that consult the shared AgentPlaybook library.

## Purpose

Use this library to prevent repeated mistakes across repositories. It provides
shared operating habits, review criteria, architecture principles, and platform
guidance. Repo-local instructions remain the source of truth for project paths,
commands, naming, domain rules, and product-specific policy.

## Project Discovery Entry

At the start of work, identify the target project from the user's request and
the current working directory. When the runtime starts from `~`, another
non-project directory, or a directory that may not be the requested target, use
the local project entry helpers before project work when they exist:

```text
<AGENTPLAYBOOK_ROOT>/scripts/agent-entry.py
<AGENTPLAYBOOK_ROOT>/scripts/project-discover.py
```

Continue only when discovery returns `selected`. If it returns `ambiguous` or
`not_found`, ask the user for the target project instead of guessing from the
prompt. Keep discovery cheap by preferring the current directory, explicit
paths, registry aliases, and known search roots over broad home-directory
scans. After selection, read the target project's local instructions before
using shared AgentPlaybook guidance.

When starting or relaunching a runtime, make the selected target project the
primary workspace. For Codex, use `codex -C <TARGET_REPO>`; add
`--add-dir <AGENTPLAYBOOK_ROOT>` only when the current task must include the
shared playbook root in the session workspace. Instruction files define agent
behavior; runtime launch roots define filesystem scope and prevent repeated
permission prompts.

When one product spans multiple repositories, keep that product as a local
workspace group in `~/.agentplaybook/projects.json`. Treat the first selected
repo as the primary repo for acceptance. If investigation shows that another
repo is the source of truth or must be written, stop before that write and
record a workspace scope checkpoint: starting primary, secondary/source-of-truth
repo, selected mode (`primary-led secondary read`, `primary-led secondary
write`, or `multi-session`), write scope, and cross-repo verification.

## Shared Guidance Boundary

Write AgentPlaybook guidance as a reusable common baseline, not as the operating
model of one product, service, vendor, customer, team, or repository. A rule
belongs in this shared library only when it remains correct after removing
service names, product policy, local paths, command names, account names,
environment names, API names, and domain vocabulary.

When a lesson comes from a specific service, generalize only the recurring risk,
decision rule, load condition, and verification question. Keep service-specific
workflows, permissions, role matrices, provider setup, deployment details, API
shapes, and product policy in the target repo's local instructions or in an
explicitly scoped platform or product-pattern document.

## Project LLM Wiki Boundary

Project-specific LLM wiki content belongs in the target project, not in this
shared library. This includes generated repo wikis, code-derived module
summaries, project runbooks, product decisions, local commands, local paths,
service setup, role matrices, and domain policy for one repo or product.

AgentPlaybook may define reusable rules for creating, reviewing, refreshing, and
reading LLM wiki pages. Those meta-rules live in:

```text
<AGENTPLAYBOOK_ROOT>/common/skills/llm-wiki-documentation/SKILL.md
<AGENTPLAYBOOK_ROOT>/common/skills/llm-wiki-documentation/references/current-guidance.md
```

When applying AgentPlaybook to a target repo, read the target repo's local LLM
wiki only after repo/runtime instructions, the workflow route, and the relevant
skill entrypoints. Treat project LLM wiki pages as navigation or source-derived
summaries unless the target repo explicitly marks a reviewed page as a source of
truth. Generated wiki pages must not override repo instructions, workflow gates,
human-authored design decisions, or source docs.

## Language Policy

Write shared agent library documents in English. This includes `AGENTS.md`,
`index.md`, `common/`, `platforms/`, `product-patterns/`, `workflows/`, and
`templates/`. Public-facing site copy under `docs/` may be localized, but it
must not become the source of truth for agent guidance.

## Metadata Policy

Use frontmatter `status` as the readiness signal and `type` as provenance or
review state. Do not ignore a document only because `type` is `ai-generated`
when `status` is `review` or `stable`; instead, treat `draft` as provisional,
`review` as active, and `stable` as broad-use guidance. The `keyflow_id` field
is retained for metadata compatibility and should not be renamed casually.

## Priority

When instructions conflict, follow this order:

1. System and developer instructions from the active agent runtime.
2. The user's current request.
3. The target repo's local instructions, such as `AGENTS.md`, `CLAUDE.md`,
   `CODEX.md`, `.agents/README.md`, `CONTRIBUTING.md`, or an explicitly
   documented local override file.
4. More specific shared AgentPlaybook documents, such as platform or product-pattern docs.
5. Shared AgentPlaybook common cards.
6. General guidance in `README.md`.

If the conflict changes behavior, verification, security, or data handling, call
it out before or after the work.

## Always Read For Agent Work

For implementation, review, refactoring, debugging, documentation, or planning tasks, first consult:

```text
<AGENTPLAYBOOK_ROOT>/common/skills/agent-operating-skill/SKILL.md
```

Then load only the supporting documents relevant to the task.

## Document Output Conventions

When creating PRDs, specs, or ARDs, follow the path and naming rules in:

```text
<AGENTPLAYBOOK_ROOT>/common/skills/doc-conventions/SKILL.md
```

Repo-local instructions override this guide. Always state the output path in the
handoff.

## Required VibeGuard Gate

VibeGuard is mandatory for AgentPlaybook maintenance and for repos that apply
AgentPlaybook. Before documentation, code, configuration, dependency, data,
deployment, or credential changes, run the VibeGuard audit for the target repo.
When applying AgentPlaybook to another repo, do not run VibeGuard `setup` or
`update` blindly; use the application drill in `docs/skills/agent-bootstrap/SKILL.md` when
the target already has agent instructions or guardrails. Use `update` only when
the user explicitly chooses to refresh an existing managed VibeGuard block;
otherwise run audit with the current guardrails.
For this repo, use the current VibeGuard command policy documented in
`VIBEGUARD.md`. During local maintenance, prefer an installed `vibeguard`
binary when the environment provides one:

```text
vibeguard audit . --rules .
```

Use the published package command only when no trusted installed binary is
available or when a task explicitly needs the latest published package:

```text
npx --yes @taehwandev/vibeguard audit . --rules .
```

When actively developing or validating a local VibeGuard checkout, this fallback
is acceptable:

```text
node <VIBEGUARD_ROOT>/src/cli.js audit . --rules .
```

Run it again before finishing. Use `--fix` only for low-risk safety fixes, and
never print detected secret values. If VibeGuard cannot run, stop and report
the blocker instead of treating it as optional.

## Required Workflow Script

For every multi-step task, run the shared workflow router before selecting
documents manually, editing, reviewing, committing, or reporting completion:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route <command> --request "<USER_REQUEST>" [--platform <platform>] [--concern <concern>]
```

Use the script output as a document and gate manifest, then execute the task with
the target repo's local commands. The route command must receive the current
user request or `--request-classified --classification-evidence "<evidence>"`
after the request was already classified or answered. Do not use
`--request-classified` to bypass direct-question, ambiguity, or Grill-Me
handling. Classification evidence that still says `vague-action`,
`broad-product`, `risky-unclear`, `direct-question`, `answer_first`,
`clarify_first`, `ambiguous`, `unclear`, `grill_me: true`, or
`question_drill: true` and their obvious hyphen/space variants must route only
to `triage` or `ambiguity` until the evidence states clear scope, a separate
actionable request, or resolved blockers. For work routes, weak evidence such
as `classified`, `done`, or `handled` is not enough; the evidence must contain
a positive resolved-scope signal such as `clear-exact`, `clear-scoped`,
`answered ... separate actionable`, or `blockers resolved`. Evidence that says
`not clarified`, `unresolved`, `open questions`, or equivalent blocker-open
language remains blocked even if it also contains a resolution word. Generic
resolution markers such as `clarified` or `no blockers` are not enough unless
they name the resolved scope, decision, blocker-question outcome, or remaining
separate action. If the request is a direct question,
answer it before editing,
routing, or running project-specific work. If the script is unavailable, cannot
run, or the route is missing a clearly relevant concern, stop and report the gap
before continuing. Use `index.md` as a fallback only for simple answer-only work
or after the user explicitly accepts the fallback.

The workflow router also promotes required docs from
`workflow-doc-surfaces.json` when request intent or known/touched paths reveal a
specific work surface. This is the root-level document routing map for common
agent tasks such as workflow script changes, request classifier work, tests,
skill cards, agent instruction files, UI-capable platform work, and shared
playbook docs. Request-intent rules may match the route command, selected
platform, request text, and reusable document sets; for example screen, list,
favorites, or explicit framework choices on Android, Application, Flutter, iOS,
KMP, Swift, and Web promote the matching UI, state, structure, review, visual
verification, and performance guidance. `workflow.py route` automatically
extracts path-like references from `--request`, and `agent-preflight.py` also
adds paths from `git status --short --untracked-files=all`. Use
`--surface-path <path>` only when a launcher already knows an in-scope path that
does not appear in the request or current git status. Surface promotion may
move a document from `reference_docs` to `required_docs`; it never replaces
repo-local instructions or the normal route command/profile selection.
The router also builds a local document graph from Markdown links, canonical
skill-bundle entrypoints, and `workflow-doc-surfaces.json` document sets. Natural
language search should find seed docs; the graph then follows nearby relations
so agents see connected guidance without the user naming every keyword. Loose
graph relations become `reference_docs`; only explicit required relations such
as frontmatter `requires_docs` may promote an additional doc to `required_docs`.

Natural-language document discovery is a router responsibility, not a hook
responsibility. Hooks must enforce preflight, docs-read receipts, and finish
evidence, but the router/search layer must expand vague task language such as
cleanup, review, screen work, or document routing into reusable task facets and
candidate required docs before the hook gate runs.

Discover valid commands, platforms, and concerns with:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py list
```

When the right document is not obvious from `index.md`, search by keyword:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py query <keyword> [<keyword> ...]
```

The query command ranks all playbook documents by relevance and returns the top
matches with one-line descriptions. It works tool-agnostically and requires no
external dependencies. It may also expand natural-language task descriptions
into reusable facets such as code cleanup, change review, verification, UI
feature work, skill docs, or document routing, then use the local document
graph to surface connected skill entrypoints and references. Use it instead of
reading all of `index.md` when the concern is narrow or the document name is
unknown. Then load only the matched documents relevant to the task.

The route output contains `request_classification`, `docs`, `required_docs`,
`reference_docs`, `gates`, `gate_ledger`, `attempt_limit`, `retry_limit`,
`retry_scope`, `notes`, and `missing`. Read `required_docs` in order before
editing or reviewing. Treat `docs` as the full candidate manifest and
`reference_docs` as lazy, on-demand context; open a reference only when the
current task touches that concern, platform, gate, or verification path. Follow
the gates as the task checklist, and stop if `missing` is not empty. Public gate
and hook signals must use only
`🐱🟢 SUCCESS` or `🐱🔴 FAIL`. Do not introduce any third state in human-visible
reports or machine-readable hook status. Completion requires every required
gate to be `🐱🟢 SUCCESS`. If a
required gate fails or lacks evidence, report `🐱🔴 FAIL`, follow missed-gate
recovery, and do not finalize. On the first `FAIL`, run an actionable
retrospective for that hook or gate scope, record the immediate correction
plan, apply safe scoped fixes, and then use the one allowed retry for that same
scope. The retry must cite or apply the retrospective correction plan. On the
second `FAIL` for that scope, stop and promote the lesson to shared docs, tests,
workflow validation, or hooks, or hand off the blocker before continuing. See
`workflows/skills/scripted-agent-workflow/SKILL.md` for the full consumption
rules.

For local commit creation or commit preparation, use the lightweight `commit`
route, or `git_commit` when the runtime labels the task that way. Do not route
a clear commit request through `review`, `task`, or `triage` unless the request
is genuinely unclear. The commit route is intentionally small: read the commit
workflow entrypoints, run the lightweight review hook first, stop before
committing when review finds issues, and record only commit readiness before
creating the local commit.

## Required Executable Evidence Gate

For multi-step tasks, use the executable wrappers when they are available. Before
editing, reviewing, committing, or reporting completion, create preflight
evidence with the current target project and selected AgentPlaybook rule source:

When executing wrapper commands from an agent runtime, replace
`<AGENTPLAYBOOK_ROOT>` with the resolved absolute path first. Do not leave
`$HOME`, `${HOME}`, `~`, or a relative path in the executable command; those
forms can bypass narrow permission-prefix matching and cause repeated approval
prompts. Always register and request command permissions using the parameter-free
script path prefix (e.g., `python3 /absolute/path/to/script.py` or `node /absolute/path/to/script.mjs`)
instead of the full command with changing arguments. If a permission is saved
with arguments, any change to those arguments (e.g., different project paths or
options) will fail prefix matching and trigger repeated prompts.
For Codex `exec_command` escalations, set `prefix_rule` to only the executable
and resolved wrapper path, such as
`["python3", "/absolute/path/to/AgentPlaybook/scripts/agent-hook.py"]`; never
include `--project`, `--request`, `--gate`, `$(pwd)`, `$HOME`, or other runtime
arguments in the saved prefix. AGY permission allowlists must follow the same
shape with only an absolute wrapper command plus a trailing argument wildcard
when the runtime permission syntax requires one. Claude managed user-level
hooks must use the stable launcher installed by `setup-agent-hooks.py` at
`~/.agentplaybook/bin/agentplaybook-hook`; setup refreshes
`~/.agentplaybook/agentplaybook-root` after moves or migrations so the Claude
hook command does not point at a stale checkout path.

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-preflight.py --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> --command <command> --request "<USER_REQUEST>" [--platform <platform>] [--concern <concern>]
```

After preflight and before editing, reviewing, committing, or reporting
completion, run the docs-read receipt hook whenever the route includes
`route docs read`:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py docs-read --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> --takeaway "<doc-derived rule/takeaway>" --next-action "<immediate task action>"
```

The docs-read hook reads the route's `required_docs` from the preflight route
manifest and writes `<TARGET_REPO>/.agentplaybook/route-docs-read.json` for the
default `preflight.json`, or `<preflight-stem>-route-docs-read.json` for a
custom preflight evidence file. When a legacy route has no `required_docs`, it
falls back to `docs`. Finish-check must reject `route docs read` evidence when
this receipt is missing or does not match the current preflight evidence file,
route manifest, and required-document count. The finish gate evidence must also
name the rule, criterion, or takeaway from the required docs that was applied to
the current task and the immediate next action that applies it; receipt or
manifest matching alone is not enough. The docs-read hook must fail until the
agent turns the discovered required docs into that task-specific takeaway and
next action. Use
`--receipt-output` only when a non-default receipt path is required; `--output`
is a legacy docs-read alias.

For work-producing tasks, do not wait until final reporting to think about
documentation. Treat `documentation impact` as a pre-code/pre-edit checkpoint:
select the artifact class first, name the affected doc path or doc class, choose
`updated`, `created`, `unchanged`, or `not applicable`, and state why the
changed behavior, workflow policy, public contract, operator action, or
acceptance criteria does or does not require a doc update. Artifact classes can
include PRD/spec/ARD, ADR/RFC, module README, API contract, runbook, migration
note, release note, test plan, skill/platform/workflow card, repo
`AGENTS.md`, or another source-of-truth class that fits the work. Do not treat
PRD as the only documentation shape. `Not applicable` or `no docs` is valid
only when the evidence states a no-durable-doc reason such as answer-only,
purely local, mechanical, no public contract, no operator action, or no
acceptance criteria. `Unchanged` is never a self-granted default: it is valid
only when the evidence names the concrete existing doc path (for example
`app/README.md`, not just a doc class), proves that doc was actually
opened/inspected/read this task, and states why the already-read doc already
covers the change. A bare coverage assertion without the inspection proof, or
without a named doc path, fails the gate. The `documentation` gate must always
run and carry non-empty evidence — it cannot be skipped or left blank — and it
must prove the actual update, or the grounded unchanged decision. Skipping
documentation (a not-applicable/no-docs/skipped decision on the `documentation`
gate) is never self-approved by the agent, and a no-durable-doc reason alone is
not sufficient: when you believe docs should genuinely not be written, ask the
user "문서를 스킵할까요? / Should I skip the doc?", get explicit approval, and
record that approval in the evidence — otherwise write the doc. The full,
updatable gate contract and the exception process are the source of truth in
`workflows/skills/documentation-update/SKILL.md`; add new exceptions there rather
than self-judging, and load that card in Grill-Me or self-review to check the
current work before completion.

Before final report, commit, release, or handoff, run the finish check and pass
evidence for every required route gate:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-finish-check.py --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> --gate "request intake=<evidence>" --gate "orient=<evidence>" --gate "scope=<evidence>" --gate "act=<evidence>" --gate "verify=<evidence>" --gate "report=<evidence>"
```

The wrappers write local JSON evidence under `<TARGET_REPO>/.agentplaybook/`.
The gate ledger is `<TARGET_REPO>/.agentplaybook/gate-evidence.json` for the
default `preflight.json`; custom preflight evidence files use
`<preflight-stem>-gate-evidence.json` so concurrent or delegated runs do not
overwrite one another.
That directory is local runtime evidence and should usually be gitignored.
The wrappers may also read or write safe cross-agent lessons under
`~/.agentplaybook/`. That user-global store is for content-free lesson metadata
only: missed gate slugs, failure types, root-cause categories, next actions, and
promotion status. It must not contain prompts, responses, commands, file paths,
repo names, branch names, diffs, logs, source content, environment values,
secrets, or project-specific display names.

Missing preflight evidence, missing finish-check evidence, or missing gate
evidence is non-compliant even when the final code or documentation appears
correct. `agent-preflight.py --request-classified` must include
`--classification-evidence`; otherwise request intake is treated as skipped.
For required gates, a skip, not-applicable, unable-to-run, deferred, or
follow-up reason is not completion unless that gate explicitly allows that
outcome and the evidence names the allowed reason. Evidence that names an
unresolved, must-fix, should-fix, blocking, or deferred issue must fail the gate
instead of passing with a note; use missed-gate recovery and retrospective
learning to fix the process.
If route classification or stored request text says `grill_me: true`, legacy
`question_drill: true`, or explicitly asks for Grill-Me, `agent-finish-check.py`
must receive Grill-Me protocol evidence such as
`grill-me if needed=</grilling session/output evidence>`. Legacy
`question drill if needed=<evidence>` or `ask blockers=<evidence>` is accepted
only when the evidence still names the Grill-Me protocol, skill, or
`/grilling` session and output.
Missing Grill-Me evidence is `🐱🔴 FAIL` and sets
`retrospective_required: true`.

If the wrappers are unavailable, the fallback is still strict: run the
workflow router, `git status --short --untracked-files=all`, VibeGuard before
work, VibeGuard again before finishing, and report each required gate with
concrete evidence. Do not claim wrapper evidence exists unless the wrapper was
actually run.

When `agent-finish-check.py` marks `retrospective_required`, run the
retrospective workflow before retrying or reporting completion, record the
immediate correction plan, apply safe scoped fixes, then resume at the first
missed gate or same failed scope. The resumed attempt must cite or apply that
plan. Repeated or high-risk lessons should be promoted from
`~/.agentplaybook/lessons/inbox/` into shared docs, tests, workflow validation,
or hooks.

VibeGuard `Needs review` is not completion unless the agent explicitly reports
the review state and passes `--allow-vibeguard-review "<reason>"`. `🐱🔴 FAIL`,
command failure, or missing VibeGuard output remains a blocker.
Human-visible finish-check output must include only `🐱🟢 SUCCESS` and
`🐱🔴 FAIL`; the machine-readable JSON keeps the same stable `SUCCESS` and
`FAIL` values.

## Supporting Documents

Use `index.md` as the full document map. Do not duplicate the full index in
repo-local instructions. Start with these direct routes, then load only the
specific cards selected by `index.md`.

Release, versioning, platform, product-pattern, and other task-specific cards
are intentionally selected through `index.md` or `scripts/workflow.py` instead
of being listed as baseline direct routes here.

```text
<AGENTPLAYBOOK_ROOT>/index.md
<AGENTPLAYBOOK_ROOT>/common/skills/stack-discovery/SKILL.md
<AGENTPLAYBOOK_ROOT>/common/skills/llm-coding-discipline/SKILL.md
<AGENTPLAYBOOK_ROOT>/common/skills/code-conventions/SKILL.md
<AGENTPLAYBOOK_ROOT>/common/skills/tool-failure-recovery/SKILL.md
<AGENTPLAYBOOK_ROOT>/common/skills/agent-interaction/SKILL.md
<AGENTPLAYBOOK_ROOT>/common/skills/agent-editing-safety/SKILL.md
```

## Workflow Documents

```text
<AGENTPLAYBOOK_ROOT>/workflows/skills/agent-task-lifecycle/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/agent-handoff-continuation/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/scripted-agent-workflow/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/ambiguity-gate/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/product-architecture-delivery/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/development-cycle/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/multi-agent-collaboration/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/multi-perspective-review/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/retrospective-learning/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/planning-research/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/documentation-update/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/feature-implementation/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/bugfix-debugging/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/refactor-cleanup/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/release-readiness/SKILL.md
<AGENTPLAYBOOK_ROOT>/workflows/skills/review-and-commit/SKILL.md
```

## Operating Rule

Do not copy this whole library into a repo. Link only the documents relevant to
that repo. Keep repo-specific paths, commands, role matrices, API names, and
domain language in the repo-local instructions.

Keep reusable agent knowledge single-owned and provider-neutral. Runtime files
are thin adapters or pointers unless behavior is genuinely runtime-specific;
do not maintain parallel Codex, Claude, or Antigravity/AGY copies of the same
operational rule or skill. Follow
`docs/skills/agentplaybook-skill-bundle-migration/references/source-of-truth-ownership.md`
for the canonical ownership and duplicate-audit rule.

When applying AgentPlaybook to another repo, reuse an existing usable local or
repo-pinned AgentPlaybook root by default. Do not download, clone, vendor, copy,
overwrite, or add a second root while one exists unless the user explicitly
approves after being told the found path.

When adding AgentPlaybook routing to a target repo, keep `AGENTS.md` as the
canonical instruction file when that runtime reads it. If existing
runtime-specific files such as `CLAUDE.md`, `CODEX.md`, `.agents/README.md`, or
Antigravity CLI docs are present, update their AgentPlaybook pointer in the same
pass or point them back to `AGENTS.md`; do not create extra runtime-specific
files only for duplication.

User-level runtime bridges must be fail-closed. If a bridge cannot confirm the
current project root, the project-root instruction file for the active runtime,
or the required AgentPlaybook/VibeGuard evidence gates, the agent must stop
before routing, editing, testing, committing, or reporting completion and ask
for bridge repair. Generated or managed runtime bridges must also enforce
silent background behavior: do not mention setup helpers, hook commands,
permission allowlists, label commands, or background metering status in normal
conversation unless the user explicitly asks about that subsystem. Runtime
bridges must distinguish setup or diagnostic evidence from usage evidence: a
label command, permission prompt, hook configuration, hook process start, command
log, or mock payload is not proof that real token usage was recorded. When exact
runtime usage is unavailable, the compliant action is to skip usage event
creation or record content-free diagnostics according to the local product
contract, not to estimate or infer from private content. A bridge that only
apologizes after exposing those details is non-compliant; it must change the
next action path or stop.

`<AGENTPLAYBOOK_ROOT>` means the directory containing this shared library. In
committed or shared repo-local instructions, do not replace it with a personal
absolute path such as `/Users/.../AgentPlaybook`. Use `${AGENTPLAYBOOK_HOME}`
when each machine can set the variable, or a repo-relative pinned path such as
`.agents/AgentPlaybook` when the root is committed or pinned with the target
repo. Personal absolute paths are acceptable only in uncommitted local runtime
bridges, one-shot prompts, or shell environment setup for a specific user.
`${KEYFLOW_AGENT_ROOT}` is accepted only as a legacy local alias when already
configured.

<!-- vibeguard:start version=1 -->
## VibeGuard

For every task that may change code, configuration, dependencies, data,
deployment, or credentials:

1. Run `vibeguard audit .` before editing.
2. If the audit reports stale VibeGuard guardrails, run `npx --yes @taehwandev/vibeguard@latest update .` once, then rerun `vibeguard audit .`. The default refresh interval is 7 days; do not update more often unless the user asks or the audit reports stale guardrails.
3. If `vibeguard` is unavailable, run `npx --yes @taehwandev/vibeguard@latest audit .` instead and use the same `npx --yes @taehwandev/vibeguard@latest ...` form for fixes.
4. If fixable findings exist, run `vibeguard audit . --fix` before implementing.
5. Never print detected secret values. Keep real secrets only in ignored runtime env files and keep env templates such as `.env.example` and `.env.sample` value-free.
6. Ask before deleting data, running migrations, deploying to production, increasing paid API/model usage, adding recurring infrastructure, or changing credentials.
7. Prefer cost-aware architecture. Before adding a paid service, database, queue, background worker, model call, analytics SDK, or cloud resource, explain why existing code or a simpler local/server-side design is insufficient.
8. For web apps, commonize repeated API/model/provider calls behind shared server-side helpers or endpoints. Prefer server-side caching, batching, and rate limits before adding new client-side call paths.
9. Before commit or push, verify `git remote -v`, repository visibility, and changed files. If the repository is public or visibility is unknown, stop before pushing secrets, env files, credentials, deployment, infrastructure, or paid-service changes.
10. After editing, run relevant tests and `vibeguard audit .` again before finishing.
11. Before creating a commit, run `vibeguard audit .`; before pushing or publishing, run `vibeguard audit . --strict`.
12. If execution evidence is available, run `vibeguard evidence .` before the final response and do not claim tests or audits ran unless they were observed.
13. Keep secrets server-side. Do not expose provider keys, database URLs, signing secrets, service-role keys, or webhook secrets to client code.
14. If the user pastes a secret in chat, treat it as exposed. Do not repeat it, put it in commands/logs/files/GitHub secrets/deployment settings/servers, or continue with deployment using that value. Guide the user to rotate it and enter a new value only through a local provider UI or secret-store prompt.
15. Keep VibeGuard scoped to guardrails. Do not clone, vendor, install, or link external playbooks or rule libraries unless the user explicitly asks for that separate setup.
16. Preserve existing repo-local instructions. Only update the managed VibeGuard block between the `vibeguard:start` and `vibeguard:end` markers.

Refresh this managed block only when `vibeguard audit .` reports stale guardrails, or manually with `vibeguard update .` / `npx --yes @taehwandev/vibeguard@latest update .`.
<!-- vibeguard:end -->
