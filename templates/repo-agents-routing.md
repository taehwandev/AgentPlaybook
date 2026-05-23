---
keyflow_id: sys_850baab06765
status: stable
type: ai-generated
---

# Repo Agent Routing Template

Add this to repo-local agent instructions.

```text
Shared AgentPlaybook library:
<AGENTPLAYBOOK_ROOT>/AGENTS.md
<AGENTPLAYBOOK_ROOT>/index.md
<AGENTPLAYBOOK_ROOT>/scripts/workflow.py

Use repo-local instructions first.
Use the shared index only to select the smallest relevant document set.
VibeGuard is required before documentation, code, config, dependency, data,
deployment, or credential changes. Run
`vibe-guard audit . --rules <AGENTPLAYBOOK_ROOT>` before editing and again
before finishing.
For multi-step tasks, run the workflow script first when it exists and use its
output as the command manifest.
Do not load every shared document by default.
Replace `<AGENTPLAYBOOK_ROOT>` with an existing local install path,
`${AGENTPLAYBOOK_HOME}`, or a repo-pinned submodule path. Use legacy
`${KEYFLOW_AGENT_ROOT}` only when the environment already provides it.
Keep repo paths, commands, components, role matrices, and domain terms in this repo.
```

Core direct routes:

```text
Document index: <AGENTPLAYBOOK_ROOT>/index.md
Agent operating skill: <AGENTPLAYBOOK_ROOT>/common/agent-operating-skill.md
LLM discipline: <AGENTPLAYBOOK_ROOT>/common/llm-coding-discipline.md
Code conventions: <AGENTPLAYBOOK_ROOT>/common/code-conventions.md
LLM wiki documentation: <AGENTPLAYBOOK_ROOT>/common/llm-wiki-documentation.md
Editing safety: <AGENTPLAYBOOK_ROOT>/common/agent-editing-safety.md
Worktree hygiene: <AGENTPLAYBOOK_ROOT>/common/worktree-hygiene.md
Defensive boundaries: <AGENTPLAYBOOK_ROOT>/common/defensive-boundaries.md
UI visual verification: <AGENTPLAYBOOK_ROOT>/common/ui-visual-verification.md
Workflow script: <AGENTPLAYBOOK_ROOT>/scripts/workflow.py
Agent task lifecycle: <AGENTPLAYBOOK_ROOT>/workflows/agent-task-lifecycle.md
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
