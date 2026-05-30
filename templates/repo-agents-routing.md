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
<AGENTPLAYBOOK_ROOT>/scripts/workflow.py
<AGENTPLAYBOOK_ROOT>/scripts/agent-preflight.py
<AGENTPLAYBOOK_ROOT>/scripts/agent-finish-check.py

Use repo-local instructions first. Explicitly read the current target project's
instruction file for this runtime before using AgentPlaybook: Codex-style agents
read `AGENTS.md` / `AGENTS.override.md`, Claude reads `CLAUDE.md` when present,
Codex-specific setups read `CODEX.md` when present, and Antigravity or generic
agents read their configured project instruction document or `.agents/README.md`
when used. If this block is being installed into a personal or global runtime
instructions file, it must still tell the runtime to read the current project's
local instruction files first.
Use the shared index only to select the smallest relevant document set.
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
For multi-step tasks, run the workflow script first with `--request
"<USER_REQUEST>"` and use its output as the command manifest before selecting
task documents, editing, reviewing, committing, or reporting completion. If the
current user message is a direct question, answer it before routing or editing.
If the direct question asks how to start app, product, or feature work, answer
with the PRD -> ARD -> implementation path before lower-level coding steps. If
the work then proceeds into code, use the `product` route unless an existing
PRD/ARD or repo-local instruction makes the slice clearly trivial.
If the workflow router cannot run, stop and report the blocker before
continuing. Keep its gate execution ledger current; each required gate must
have evidence before completion. Show a short traffic-light gate signal after
each completed gate or task step. Completion requires every
required gate to be 🐱🟢 GREEN. Use the cat signal badges in human-visible
reports: 🐱🔵 PENDING means not reached, 🐱🟡 YELLOW means blocked or paused,
and 🐱🔴 RED means missed or missing evidence and triggers missed-gate recovery:
stop finalization, roll back only dependent agent-made changes after the missed
gate when safe, return to the first missed gate only, and run the retrospective
workflow. The missed gate gets up to two recovery retries; do not restart the
whole route.
When the wrapper scripts are available, run `agent-preflight.py` before editing,
reviewing, committing, or reporting completion, and run `agent-finish-check.py`
before final report, commit, release, or handoff. Pass evidence for every route
gate to the finish check. The wrappers write local evidence under
`.agentplaybook/`; this directory is runtime evidence and should usually be
gitignored. Missing wrapper evidence or missing route gate evidence is
non-compliant even when the final files look correct. VibeGuard 🐱🟡 YELLOW /
`Needs review` must be reported explicitly and can pass the finish check only
with an `--allow-vibeguard-review` reason. `--request-classified` must include
`--classification-evidence`; if a request asks for a question drill, missing
drill evidence is 🐱🔴 RED and requires missed-gate recovery.
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
Preflight evidence script: <AGENTPLAYBOOK_ROOT>/scripts/agent-preflight.py
Finish evidence script: <AGENTPLAYBOOK_ROOT>/scripts/agent-finish-check.py
Android Compose UI: <AGENTPLAYBOOK_ROOT>/platforms/android/android-compose-ui.md
Android ViewModel/state: <AGENTPLAYBOOK_ROOT>/platforms/android/android-viewmodel-state.md
KMP architecture: <AGENTPLAYBOOK_ROOT>/platforms/kmp/kmp-architecture.md
KMP Compose UI: <AGENTPLAYBOOK_ROOT>/platforms/kmp/kmp-compose-ui.md
Flutter architecture: <AGENTPLAYBOOK_ROOT>/platforms/flutter/flutter-architecture.md
Flutter widget UI: <AGENTPLAYBOOK_ROOT>/platforms/flutter/flutter-widget-ui.md
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
