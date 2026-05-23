---
keyflow_id: sys_agent_runtime_integration
status: review
type: human-reviewed-needed
---

# Agent Runtime Integration

Use this when connecting AgentPlaybook to Codex, Claude, Antigravity, or another
AI coding agent runtime.

## Model

AgentPlaybook should be consumed through a small bridge, not copied wholesale:

1. Reusable library: one AgentPlaybook root.
2. Runtime bridge: repo-local instructions or a pasted prompt.
3. Task route: `scripts/workflow.py` output for the current task.
4. Safety gate: required VibeGuard gate using AgentPlaybook as the rule source.

Repo-local instructions remain the source of truth for commands, paths,
services, product policy, and domain language.

## Setup Modes

Select one mode before wiring a runtime:

- Existing local install: preferred when AgentPlaybook is already present on the
  machine. Reuse that root and do not clone another copy.
- First-time local shared install: clone once to a stable path such as
  `~/.agent-playbook` when no usable root exists.
- Team-pinned install: use a submodule, vendored dependency, or workspace
  dependency when every teammate and agent must use the same reviewed version.

A usable root contains `AGENTS.md`, `index.md`, and `scripts/workflow.py`.
Validate the selected root with:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py validate
```

## Long-Lived Repo Setup

For repos that will keep using AgentPlaybook, add a short routing block to the
instruction file each agent runtime reads:

- Codex-style runtimes: `AGENTS.md` or `AGENTS.override.md`.
- Claude-style runtimes: `CLAUDE.md`.
- Codex-specific local docs: `CODEX.md` when the repo already uses it.
- Antigravity or generic agents: the project instruction file the runtime
  actually reads, or `.agents/README.md` when the repo uses a shared agent
  folder.

Use `templates/repo-agents-routing.md` as the source block. Keep the block
short and point to:

```text
<AGENTPLAYBOOK_ROOT>/AGENTS.md
<AGENTPLAYBOOK_ROOT>/index.md
<AGENTPLAYBOOK_ROOT>/scripts/workflow.py
```

Do not paste the full playbook into runtime-specific files.

## One-Shot Prompt Setup

Use one-shot prompting when:

- the target repo is not wired yet
- the agent runtime does not automatically load repo instruction files
- you are using a web chat or temporary session
- you want Claude, Antigravity, or another agent to follow AgentPlaybook for one
  task without changing repo files

Paste `templates/use-agentplaybook-prompt.md` into the agent, replacing the
target repo, task, AgentPlaybook root, and VibeGuard docs placeholders.

The prompt explicitly tells the runtime to read `AGENTS.md` and `index.md`,
because not every agent automatically discovers Codex-style `AGENTS.md` files.

## Runtime Notes

Codex:

- Prefer repo-local `AGENTS.md` / `AGENTS.override.md` plus the routing block.
- Use the workflow router for multi-step work.
- Keep Codex-specific commands or sandbox notes in the target repo, not in the
  shared playbook.

Claude:

- Prefer `CLAUDE.md` with the routing block.
- If Claude is operating from chat without repo instruction discovery, paste
  `templates/use-agentplaybook-prompt.md`.
- Tell Claude the exact AgentPlaybook root path or a repo-pinned submodule path.

Antigravity:

- Use the project instruction surface that Antigravity actually reads.
- If that surface is unclear, paste `templates/use-agentplaybook-prompt.md` at
  the start of the task.
- Do not assume Antigravity has loaded Codex-specific `AGENTS.md`; instruct it
  to read the AgentPlaybook root explicitly.

Generic agents:

- Use `.agents/README.md` or the runtime's documented project instruction file.
- If file discovery is unavailable, use the one-shot prompt.

## Required Flow

For every runtime:

1. Identify the target repo and read the current repo-local instructions:
   `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`, `CODEX.md`,
   `.agents/README.md`, `CONTRIBUTING.md`, task docs, PRD/ARD docs, or
   equivalent project guidance.
2. Select the setup mode: existing local install, first-time local shared
   install, or team-pinned install.
3. Locate or install the AgentPlaybook root and validate it.
4. Run the required VibeGuard safety gate from
   https://vibeguard.thdev.app/ with the selected AgentPlaybook root as the
   rule source.
5. Read AgentPlaybook `AGENTS.md`.
6. Use `index.md` or `scripts/workflow.py` to select the smallest document set.
7. When a scripted route is used, keep a gate execution ledger, mark each route
   gate with evidence when it is executed, assign a traffic-light signal, and
   show a short gate signal after each completed gate or task step.
8. Load only selected cards.
9. Execute repo-local commands only from trusted repo-local instructions.
10. Before reporting completion, confirm every required route gate is `GREEN`
    with ledger evidence.
11. When a VibeGuard execution evidence adapter is configured, follow
    https://vibeguard.thdev.app/ and compare the summary with claimed commands.
12. Report verification and residual risk.

If a required route gate was missed, the runtime must stop finalization, roll
back only dependent agent-made changes after the missed gate when safe, return
to the first missed gate only, and run the retrospective workflow. The missed
gate gets one retry; the whole route is not restarted.

Traffic-light signals are checked inside the workflow:

- `GREEN`: executed with evidence; the gate can be counted as complete.
- `YELLOW`: blocked or paused; the task can be handed off but not called
  complete.
- `RED`: missed or missing evidence after the gate should have run; run
  missed-gate recovery.

## Verification

After connecting a runtime, verify:

- the target repo instruction file points to the selected AgentPlaybook root
- the runtime still reads the target repo's current agent instructions first
- `AGENTS.md`, `index.md`, and `scripts/workflow.py` exist under that root
- the VibeGuard gate passed or stopped with a reported blocker
- VibeGuard evidence was summarized through VibeGuard docs when an evidence
  adapter was configured
- the route gate ledger was completed when a scripted route was used
- the agent can produce a route, such as:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route task
```

## Stop If

- The target runtime does not have file access and the user cannot paste the
  one-shot prompt.
- The AgentPlaybook root cannot be located.
- VibeGuard cannot run after following https://vibeguard.thdev.app/.
- Repo-local instructions conflict with AgentPlaybook on security, data,
  deployment, cost, or verification behavior.
