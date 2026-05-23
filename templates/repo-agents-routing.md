---
keyflow_id: sys_850baab06765
status: stable
type: ai-generated
---

# Repo Agent Routing Template

Add this to repo-local agent instructions for Codex, Claude, Antigravity, or
another coding agent runtime. Use the file the runtime actually reads, such as
`AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`, `CODEX.md`, or
`.agents/README.md`.

```text
Shared AgentPlaybook library:
<AGENTPLAYBOOK_ROOT>/AGENTS.md
<AGENTPLAYBOOK_ROOT>/index.md
<AGENTPLAYBOOK_ROOT>/scripts/workflow.py

Use repo-local instructions first.
Use the shared index only to select the smallest relevant document set.
VibeGuard is required before documentation, code, config, dependency, data,
deployment, or credential changes. Follow https://vibeguard.thdev.app/ and use
<AGENTPLAYBOOK_ROOT> as the rule source before editing and again before
finishing.
For multi-step tasks, run the workflow script first when it exists and use its
output as the command manifest. Keep its gate execution ledger current; each
required gate must have evidence before completion. Show a short traffic-light
gate signal after each completed gate or task step. Completion requires every
required gate to be GREEN. YELLOW means blocked or paused. RED means missed or
missing evidence and triggers missed-gate recovery: stop finalization, roll back
only dependent agent-made changes after the missed gate when safe, return to the
first missed gate only, and run the retrospective workflow. The missed gate gets
one retry; do not restart the whole route.
Do not load every shared document by default.
Replace `<AGENTPLAYBOOK_ROOT>` with an existing local install path,
`${AGENTPLAYBOOK_HOME}`, or a repo-pinned submodule path. Use legacy
`${KEYFLOW_AGENT_ROOT}` only when the environment already provides it.
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
