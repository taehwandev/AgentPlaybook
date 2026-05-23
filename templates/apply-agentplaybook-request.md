---
keyflow_id: sys_apply_agentplaybook_request_template
status: review
type: human-reviewed-needed
---

# Apply AgentPlaybook Request

Paste this into an AI coding agent when you want it to connect a project to
AgentPlaybook.

Use `templates/use-agentplaybook-prompt.md` instead when you only want one task
to follow AgentPlaybook without changing repo-local instruction files.

```text
Apply AgentPlaybook to this project:
https://github.com/taehwandev/AgentPlaybook

Before changing anything, read this project's current agent instructions first:
AGENTS.md, AGENTS.override.md, CLAUDE.md, CODEX.md, .agents/README.md,
CONTRIBUTING.md, task docs, PRD/ARD docs, or equivalent project docs.

Use an existing local AgentPlaybook install if one is available. Check an
explicit path from me first, then AGENTPLAYBOOK_HOME, then common local clones
such as ~/.agent-playbook or ~/GitHub/AgentPlaybook.

Select one setup mode and tell me which one you selected before editing:

- Existing local install: if a usable install exists, link this repo to that
  copy. Do not clone, vendor, or copy a second copy.
- First-time local shared install: if no usable install exists, ask before
  cloning once to ~/.agent-playbook.
- Team-pinned install: ask before adding AgentPlaybook as a repo-pinned
  submodule, vendored dependency, or workspace dependency.

A usable AgentPlaybook root must contain AGENTS.md, index.md, and
scripts/workflow.py. Validate it with:

python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py validate

VibeGuard is required. After selecting the AgentPlaybook root, apply VibeGuard
with the selected AgentPlaybook root as the rule source. Follow the current
VibeGuard docs for exact setup, audit, fix, package, and evidence flow:

https://vibeguard.thdev.app/

If VibeGuard cannot run, stop and tell me the blocker.

Update the repo-local agent instructions, such as AGENTS.md,
AGENTS.override.md, CLAUDE.md, CODEX.md, or .agents/README.md, with a short
routing block. Preserve existing project rules. Keep repo-specific commands,
paths, services, product policy, and domain language in this repo.

For any multi-step setup or follow-up task, run the workflow route and show a
gate signal after each completed gate or task step:

Gate signal: GREEN | gate: <gate> | evidence: <evidence> | next: <next gate>

Completion requires every required gate to be GREEN. YELLOW means blocked or
paused. RED means the gate was missed or lacks evidence and must use missed-gate
recovery.

After connecting it, verify that the referenced AgentPlaybook AGENTS.md and
index.md files exist, confirm the VibeGuard gate is passing, then continue with
my original task.
```

For a team-pinned install, add this sentence:

```text
Prefer a repo-pinned submodule or vendored dependency so every teammate and
agent uses the same reviewed AgentPlaybook version.
```
