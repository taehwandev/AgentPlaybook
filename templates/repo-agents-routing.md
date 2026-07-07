---
keyflow_id: sys_850baab06765
status: stable
type: ai-generated
---

# Repo Agent Routing Template

Add this to repo-local agent instructions for Codex, Claude, Antigravity, or
another coding agent runtime. Prefer `AGENTS.md` as the canonical file when the
runtime reads it. If `CLAUDE.md`, `CODEX.md`, `.agents/README.md`, or
Antigravity CLI docs already exist, update their pointer in the same pass or
point them back to `AGENTS.md`; do not create duplicate runtime-specific files
only for this block.

```text
Shared AgentPlaybook library:
<AGENTPLAYBOOK_ROOT>/AGENTS.md
<AGENTPLAYBOOK_ROOT>/index.md
<AGENTPLAYBOOK_ROOT>/scripts/agent-entry.py
<AGENTPLAYBOOK_ROOT>/scripts/project-discover.py
<AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py
<AGENTPLAYBOOK_ROOT>/scripts/workflow.py
<AGENTPLAYBOOK_ROOT>/scripts/agent-preflight.py
<AGENTPLAYBOOK_ROOT>/scripts/agent-finish-check.py

Use repo-local instructions first. If this block is being installed into a
personal or global runtime instructions file, and the runtime starts outside the
target repo or the request does not name one clear repo, run
`agent-entry.py` or `project-discover.py` first and stop when it returns
`ambiguous` or `not_found`. If `agent-entry.py` returns `selected`, prefer
starting or relaunching the runtime with that selected repo as the primary
workspace. For Codex, use `codex -C <TARGET_REPO>`; add
`--add-dir <AGENTPLAYBOOK_ROOT>` only when the task needs the shared
AgentPlaybook root in the session workspace. Repo instruction files define
behavior; runtime launch options define filesystem scope. Explicitly read the
current target project's
instruction file for this runtime before using AgentPlaybook: Codex-style
agents read `AGENTS.md`, Claude reads `CLAUDE.md` when
present, Codex-specific setups read `CODEX.md` when present, Antigravity reads
`AGENTS.md`, and generic agents read their configured project instruction
document or `.agents/README.md` when used.
If the request names a product/workspace alias that may map to multiple repos,
use the local `~/.agentplaybook/projects.json` workspace group when available.
Do not guess a single repo from the alias alone. If work starts in one primary
repo and investigation shows a secondary repo must be written, stop before that
write and record a workspace scope checkpoint: starting primary, secondary or
source-of-truth repo, selected mode (`primary-led secondary read`,
`primary-led secondary write`, or `multi-session`), write scope, session model,
and cross-repo verification. When finish-check evidence is used and a secondary
repo was written, pass it as `workspace scope checkpoint=<evidence>`,
`scope expansion checkpoint=<evidence>`, or
`cross-repo scope checkpoint=<evidence>`.
Use the shared index only to select the smallest relevant document set.
Do not create repo-local skill documents merely to copy shared AgentPlaybook
behavior. Keep repo-local skills, workflows, wiki pages, or runbooks only when
they contain product-specific facts, commands, domain policy, or verification
that cannot be shared safely.
VibeGuard is required before documentation, code, config, dependency, data,
deployment, or credential changes. Apply the current VibeGuard package command
flow with <AGENTPLAYBOOK_ROOT> as the rule source before editing and again
before finishing. The VibeGuard site is a human reference and does not need to
be fetched by the agent. Do not run VibeGuard `setup` or `update` blindly. If
this repo already has custom agent instructions,
`.vibeguard.json`, `VIBEGUARD.md`, or a managed VibeGuard block, ask a short
application drill first: add pointer vs merge vs pin; audit-only vs refresh
with update vs first-time setup; apply now vs prepare instructions only.
Default to preserving current guardrails and running audit only unless the user
chooses to refresh the managed block.
For multi-step tasks, run `agent-hook.py start` first with `--request
"<USER_REQUEST>"`; it runs workflow routing/preflight and reports the required
hooks for the route. Use its output as the command manifest before selecting
task documents, editing, reviewing, committing, or reporting completion. If the
current user message is a direct question, answer it before routing or editing.
Do not wait for the user to name document keywords. Let routing/search infer
the work surface from the request, platform, concern, and touched files; use
`workflow-doc-surfaces.json` and the local document graph as inputs; read the
route `required_docs` before editing or reviewing; and treat graph neighbors as
`reference_docs` unless the route promotes them to `required_docs`. If
routing/search misses a clearly relevant platform, concern, or document
surface, stop and report the gap instead of proceeding from memory.
If the direct question asks how to start app, product, or feature work, answer
with the PRD -> ARD -> implementation path before lower-level coding steps. If
the work then proceeds into code, use the `product` route unless an existing
PRD/ARD or repo-local instruction makes the slice clearly trivial.
If the workflow router or start hook cannot run, stop and report the blocker
before continuing. Keep its gate execution ledger current; each required gate
must have evidence before completion. Show a short gate signal after each
completed or failed gate or task step. Completion requires every required gate
to be 🐱🟢 SUCCESS. Use only two cat signal badges in human-visible reports:
🐱🟢 SUCCESS means executed with evidence, and 🐱🔴 FAIL means blocked, failed,
missed, or missing evidence and triggers missed-gate recovery: stop
finalization, roll back only dependent agent-made changes after the missed gate
when safe, return to the first missed gate only, and run the retrospective
workflow. The missed gate gets one recovery retry; do not restart the whole
route. Do not report any third gate state.
When the wrapper scripts are available, run `agent-hook.py start` before
editing, `agent-hook.py review` after the scoped diff is ready, and
`agent-hook.py finish` before final report, commit, release, or handoff. Pass
evidence for every route gate to the finish check. The wrappers write local
evidence under
`.agentplaybook/`; this directory is runtime evidence and should usually be
gitignored. When executing wrapper commands from an agent runtime, resolve
`<AGENTPLAYBOOK_ROOT>` to an absolute path first; do not leave `$HOME`,
`${HOME}`, `~`, or a relative path in the executable command. Missing wrapper
evidence or missing route gate evidence is
non-compliant even when the final files look correct. VibeGuard `Needs review`
must be reported explicitly and can pass the finish check only with an
`--allow-vibeguard-review` reason. `--request-classified` must include
`--classification-evidence`; work routes require resolved-scope evidence such
as `clear-scoped`, `answered ... separate actionable`, or `blockers resolved`,
not weak markers such as `classified`, `done`, `clarified`, or `no blockers`.
If a request asks for Grill-Me or classification returns `grill_me: true`,
missing Grill-Me protocol or `/grilling` session evidence is 🐱🔴 FAIL and
requires missed-gate recovery.
Do not load every shared document by default.
Replace `<AGENTPLAYBOOK_ROOT>` with a portable root reference. In committed
repo-local instructions, use `${AGENTPLAYBOOK_HOME}` for shared local installs
or a repo-relative pinned path such as `.agents/AgentPlaybook`; do not commit a
personal absolute path such as `/Users/.../AgentPlaybook`. Full local paths
belong only in shell environment setup, one-shot prompts, or uncommitted
user-level runtime bridges. Use legacy `${KEYFLOW_AGENT_ROOT}` only when the
environment already provides it.
Keep repo paths, commands, components, role matrices, and domain terms in this repo.
```

For one-shot runtime prompting without editing repo instructions, use
`templates/use-agentplaybook-prompt.md`.

Core direct routes:

```text
Document index: <AGENTPLAYBOOK_ROOT>/index.md
Agent operating skill: <AGENTPLAYBOOK_ROOT>/common/agent-operating-skill.md
Task intake/effort routing: <AGENTPLAYBOOK_ROOT>/common/task-intake-effort-routing.md
Stack discovery: <AGENTPLAYBOOK_ROOT>/common/stack-discovery.md
LLM discipline: <AGENTPLAYBOOK_ROOT>/common/llm-coding-discipline.md
Code conventions: <AGENTPLAYBOOK_ROOT>/common/code-conventions.md
Code structure/ownership: <AGENTPLAYBOOK_ROOT>/common/code-structure-ownership.md
Reusable code design: <AGENTPLAYBOOK_ROOT>/common/reusable-code-design.md
Component API design: <AGENTPLAYBOOK_ROOT>/common/component-api-design.md
State modeling: <AGENTPLAYBOOK_ROOT>/common/state-modeling.md
Error modeling: <AGENTPLAYBOOK_ROOT>/common/error-modeling.md
Tool failure recovery: <AGENTPLAYBOOK_ROOT>/common/tool-failure-recovery.md
Agent interaction: <AGENTPLAYBOOK_ROOT>/common/agent-interaction.md
LLM wiki documentation: <AGENTPLAYBOOK_ROOT>/common/llm-wiki-documentation.md
Editing safety: <AGENTPLAYBOOK_ROOT>/common/agent-editing-safety.md
Worktree hygiene: <AGENTPLAYBOOK_ROOT>/common/worktree-hygiene.md
Defensive boundaries: <AGENTPLAYBOOK_ROOT>/common/defensive-boundaries.md
UI visual verification: <AGENTPLAYBOOK_ROOT>/common/ui-visual-verification.md
Workflow script: <AGENTPLAYBOOK_ROOT>/scripts/workflow.py
Agent hook wrapper: <AGENTPLAYBOOK_ROOT>/scripts/agent-hook.py
Agent entry manifest: <AGENTPLAYBOOK_ROOT>/scripts/agent-entry.py
Project discovery: <AGENTPLAYBOOK_ROOT>/scripts/project-discover.py
Preflight evidence script: <AGENTPLAYBOOK_ROOT>/scripts/agent-preflight.py
Finish evidence script: <AGENTPLAYBOOK_ROOT>/scripts/agent-finish-check.py
Android architecture: <AGENTPLAYBOOK_ROOT>/platforms/android/android-architecture.md
Android Compose UI: <AGENTPLAYBOOK_ROOT>/platforms/android/android-compose-ui.md
Android module/package structure: <AGENTPLAYBOOK_ROOT>/platforms/android/android-module-structure.md
Android ViewModel/state: <AGENTPLAYBOOK_ROOT>/platforms/android/android-viewmodel-state.md
Android state/data: <AGENTPLAYBOOK_ROOT>/platforms/android/android-state-data.md
Android DataStore persistence: <AGENTPLAYBOOK_ROOT>/platforms/android/references/android-datastore.md
Android background work: <AGENTPLAYBOOK_ROOT>/platforms/android/android-background-work.md
Android security: <AGENTPLAYBOOK_ROOT>/platforms/android/android-security.md
Android review: <AGENTPLAYBOOK_ROOT>/platforms/android/android-review.md
KMP architecture: <AGENTPLAYBOOK_ROOT>/platforms/kmp/kmp-architecture.md
KMP module/source-set structure: <AGENTPLAYBOOK_ROOT>/platforms/kmp/kmp-module-structure.md
KMP Compose UI: <AGENTPLAYBOOK_ROOT>/platforms/kmp/kmp-compose-ui.md
Flutter architecture: <AGENTPLAYBOOK_ROOT>/platforms/flutter/flutter-architecture.md
Flutter project/package structure: <AGENTPLAYBOOK_ROOT>/platforms/flutter/flutter-project-structure.md
Flutter widget UI: <AGENTPLAYBOOK_ROOT>/platforms/flutter/flutter-widget-ui.md
iOS target/package structure: <AGENTPLAYBOOK_ROOT>/platforms/ios/ios-module-structure.md
iOS SwiftUI UI: <AGENTPLAYBOOK_ROOT>/platforms/ios/ios-swiftui-ui.md
iOS UIKit UI: <AGENTPLAYBOOK_ROOT>/platforms/ios/ios-uikit-ui.md
Web React UI: <AGENTPLAYBOOK_ROOT>/platforms/web/web-react-ui.md
Server API implementation: <AGENTPLAYBOOK_ROOT>/platforms/server/server-api-implementation.md
Application command/UI: <AGENTPLAYBOOK_ROOT>/platforms/application/application-command-ui.md
Auth/RBAC implementation: <AGENTPLAYBOOK_ROOT>/product-patterns/auth-rbac-implementation.md
Invitation implementation: <AGENTPLAYBOOK_ROOT>/product-patterns/invitation-implementation.md
Billing/entitlements implementation: <AGENTPLAYBOOK_ROOT>/product-patterns/billing-entitlements-implementation.md
Agent task lifecycle: <AGENTPLAYBOOK_ROOT>/workflows/agent-task-lifecycle.md
Request triage workflow: <AGENTPLAYBOOK_ROOT>/workflows/request-triage.md
Agent handoff/continuation: <AGENTPLAYBOOK_ROOT>/workflows/agent-handoff-continuation.md
Scripted agent workflow: <AGENTPLAYBOOK_ROOT>/workflows/scripted-agent-workflow.md
Ambiguity gate: <AGENTPLAYBOOK_ROOT>/workflows/ambiguity-gate.md
Product architecture delivery: <AGENTPLAYBOOK_ROOT>/workflows/product-architecture-delivery.md
Development cycle: <AGENTPLAYBOOK_ROOT>/workflows/development-cycle.md
Multi-agent collaboration: <AGENTPLAYBOOK_ROOT>/workflows/multi-agent-collaboration.md
Multi-perspective review: <AGENTPLAYBOOK_ROOT>/workflows/multi-perspective-review.md
Retrospective learning: <AGENTPLAYBOOK_ROOT>/workflows/retrospective-learning.md
Planning/research workflow: <AGENTPLAYBOOK_ROOT>/workflows/planning-research.md
Documentation workflow: <AGENTPLAYBOOK_ROOT>/workflows/documentation-update.md
Feature workflow: <AGENTPLAYBOOK_ROOT>/workflows/feature-implementation.md
Bugfix/debugging workflow: <AGENTPLAYBOOK_ROOT>/workflows/bugfix-debugging.md
Refactor workflow: <AGENTPLAYBOOK_ROOT>/workflows/refactor-cleanup.md
Release readiness workflow: <AGENTPLAYBOOK_ROOT>/workflows/release-readiness.md
Review/commit workflow: <AGENTPLAYBOOK_ROOT>/workflows/review-and-commit.md
```

Use `index.md` for platform, product-pattern, and task-specific common cards
instead of copying the full shared library into repo-local instructions.
