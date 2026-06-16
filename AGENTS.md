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
3. The target repo's local instructions, such as `AGENTS.md`,
   `AGENTS.override.md`, `CLAUDE.md`, `CODEX.md`, `.agents/README.md`, or
   `CONTRIBUTING.md`.
4. More specific shared AgentPlaybook documents, such as platform or product-pattern docs.
5. Shared AgentPlaybook common cards.
6. General guidance in `README.md`.

If the conflict changes behavior, verification, security, or data handling, call
it out before or after the work.

## Always Read For Agent Work

For implementation, review, refactoring, debugging, documentation, or planning tasks, first consult:

```text
<AGENTPLAYBOOK_ROOT>/common/agent-operating-skill.md
```

Then load only the supporting documents relevant to the task.

## Required VibeGuard Gate

VibeGuard is mandatory for AgentPlaybook maintenance and for repos that apply
AgentPlaybook. Before documentation, code, configuration, dependency, data,
deployment, or credential changes, run the VibeGuard audit for the target repo.
When applying AgentPlaybook to another repo, do not run VibeGuard `setup` or
`update` blindly; use the application drill in `docs/agent-bootstrap.md` when
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
user request or `--request-classified` after the request was already classified
or answered. If the request is a direct question, answer it before editing,
routing, or running project-specific work. If the script is unavailable, cannot
run, or the route is missing a clearly relevant concern, stop and report the gap
before continuing. Use `index.md` as a fallback only for simple answer-only work
or after the user explicitly accepts the fallback.
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
external dependencies. Use it instead of reading all of `index.md` when the
concern is narrow or the document name is unknown. Then load only the matched
documents relevant to the task.

The route output contains `request_classification`, `docs`, `gates`,
`gate_ledger`, `attempt_limit`, `retry_limit`, `retry_scope`, `notes`, and
`missing`. Read
listed documents in order, follow the gates as the task checklist, and stop if
`missing` is not empty. Public gate and hook signals must use only
`🐱🟢 SUCCESS` or `🐱🔴 FAIL`. Do not introduce any third state in human-visible
reports or machine-readable hook status. Completion requires every required
gate to be `🐱🟢 SUCCESS`. If a
required gate fails or lacks evidence, report `🐱🔴 FAIL`, follow missed-gate
recovery, and do not finalize. On the first `FAIL`, request exactly one retry
for the same hook or gate scope. On the second `FAIL` for that scope, stop and
run `workflows/retrospective-learning.md` before handoff, commit, release, or a
completion report. See `workflows/scripted-agent-workflow.md` for the full
consumption rules.

## Required Executable Evidence Gate

For multi-step tasks, use the executable wrappers when they are available. Before
editing, reviewing, committing, or reporting completion, create preflight
evidence with the current target project and selected AgentPlaybook rule source:

When executing wrapper commands from an agent runtime, replace
`<AGENTPLAYBOOK_ROOT>` with the resolved absolute path first. Do not leave
`$HOME`, `${HOME}`, `~`, or a relative path in the executable command; those
forms can bypass narrow permission-prefix matching and cause repeated approval
prompts.

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-preflight.py --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> --command <command> --request "<USER_REQUEST>" [--platform <platform>] [--concern <concern>]
```

Before final report, commit, release, or handoff, run the finish check and pass
evidence for every required route gate:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-finish-check.py --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> --gate "request intake=<evidence>" --gate "orient=<evidence>" --gate "scope=<evidence>" --gate "act=<evidence>" --gate "verify=<evidence>" --gate "report=<evidence>"
```

The wrappers write local JSON evidence under `<TARGET_REPO>/.agentplaybook/`.
That directory is local runtime evidence and should usually be gitignored.

Missing preflight evidence, missing finish-check evidence, or missing gate
evidence is non-compliant even when the final code or documentation appears
correct. `agent-preflight.py --request-classified` must include
`--classification-evidence`; otherwise request intake is treated as skipped.
If route classification or stored request text says `question_drill: true` or
explicitly asks for a question drill, `agent-finish-check.py` must receive
question-drill gate evidence such as `question drill if needed=<evidence>` or
`ask blockers=<evidence>`. Missing drill evidence is `🐱🔴 FAIL` and sets
`retrospective_required: true`.

If the wrappers are unavailable, the fallback is still strict: run the
workflow router, `git status --short --untracked-files=all`, VibeGuard before
work, VibeGuard again before finishing, and report each required gate with
concrete evidence. Do not claim wrapper evidence exists unless the wrapper was
actually run.

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
<AGENTPLAYBOOK_ROOT>/common/stack-discovery.md
<AGENTPLAYBOOK_ROOT>/common/llm-coding-discipline.md
<AGENTPLAYBOOK_ROOT>/common/code-conventions.md
<AGENTPLAYBOOK_ROOT>/common/tool-failure-recovery.md
<AGENTPLAYBOOK_ROOT>/common/agent-interaction.md
<AGENTPLAYBOOK_ROOT>/common/agent-editing-safety.md
```

## Workflow Documents

```text
<AGENTPLAYBOOK_ROOT>/workflows/agent-task-lifecycle.md
<AGENTPLAYBOOK_ROOT>/workflows/agent-handoff-continuation.md
<AGENTPLAYBOOK_ROOT>/workflows/scripted-agent-workflow.md
<AGENTPLAYBOOK_ROOT>/workflows/ambiguity-gate.md
<AGENTPLAYBOOK_ROOT>/workflows/product-architecture-delivery.md
<AGENTPLAYBOOK_ROOT>/workflows/development-cycle.md
<AGENTPLAYBOOK_ROOT>/workflows/multi-agent-collaboration.md
<AGENTPLAYBOOK_ROOT>/workflows/multi-perspective-review.md
<AGENTPLAYBOOK_ROOT>/workflows/retrospective-learning.md
<AGENTPLAYBOOK_ROOT>/workflows/planning-research.md
<AGENTPLAYBOOK_ROOT>/workflows/documentation-update.md
<AGENTPLAYBOOK_ROOT>/workflows/feature-implementation.md
<AGENTPLAYBOOK_ROOT>/workflows/bugfix-debugging.md
<AGENTPLAYBOOK_ROOT>/workflows/refactor-cleanup.md
<AGENTPLAYBOOK_ROOT>/workflows/release-readiness.md
<AGENTPLAYBOOK_ROOT>/workflows/review-and-commit.md
```

## Operating Rule

Do not copy this whole library into a repo. Link only the documents relevant to
that repo. Keep repo-specific paths, commands, role matrices, API names, and
domain language in the repo-local instructions.

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
