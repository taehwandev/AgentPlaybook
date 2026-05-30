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
4. Safety gate: current VibeGuard application flow using AgentPlaybook as the
   rule source.

Repo-local instructions remain the source of truth for commands, paths,
services, product policy, and domain language.

## Setup Modes

Select one mode before wiring a runtime:

- Existing local install: required by default when AgentPlaybook is already
  present on the machine. Reuse that root and do not clone another copy unless
  the user explicitly approves a new copy after seeing the found path.
- First-time local shared install: clone once to a stable path such as
  `~/.agent-playbook` when no usable root exists.
- Team-pinned install: use a submodule, vendored dependency, or workspace
  dependency when every teammate and agent must use the same reviewed version.

A usable root contains `AGENTS.md`, `index.md`, and `scripts/workflow.py`.
Validate the selected root with:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py validate
```

If a usable root is found, runtime setup must stop install selection there and
reuse it. Do not download, clone, vendor, copy, overwrite, or add a second root
unless the user approves this question:

```text
AgentPlaybook already exists locally at <path>. Do you want me to download or
pin a new copy anyway, or should I reuse the existing root?
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
- Personal or global runtime docs: treat these as optional Step 2 bridge work.
  Update them only when the user chooses the stronger future-behavior setup.
  Examples include `~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md`,
  `~/.antigravity`, `~/.antigravitycli`, and `~/.antigravity-ide`.

Prefer one canonical instruction file, usually `AGENTS.md`, when all active
runtimes read it. When `CLAUDE.md`, `CODEX.md`, `.agents/README.md`, or
Antigravity CLI docs already exist, update them in the same application pass so
they point to the selected AgentPlaybook root or back to `AGENTS.md`. Do not
create a separate runtime-specific file only to duplicate guidance that the
runtime already reads from `AGENTS.md`.

Every runtime bridge must explicitly tell the agent to read the current target
project's own instructions first. Do not rely on implicit discovery. State the
runtime-specific entrypoint directly: Codex-style agents should read the current
project's `AGENTS.md` / `AGENTS.override.md`, Claude should read the current
project's `CLAUDE.md` when present, Codex-specific setups should read `CODEX.md`
when present, and Antigravity should read the Antigravity/project instruction
surface it is configured to load. Then tell the agent to follow AgentPlaybook as
shared guidance only after those local instructions.

Use `templates/repo-agents-routing.md` as the source block. Keep the block
short and point to:

```text
<AGENTPLAYBOOK_ROOT>/AGENTS.md
<AGENTPLAYBOOK_ROOT>/index.md
<AGENTPLAYBOOK_ROOT>/scripts/workflow.py
<AGENTPLAYBOOK_ROOT>/scripts/agent-preflight.py
<AGENTPLAYBOOK_ROOT>/scripts/agent-finish-check.py
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

- If `CLAUDE.md` already exists, update it with the routing block or a pointer
  to `AGENTS.md`.
- If no Claude-specific file exists and Claude reads `AGENTS.md` in the target
  environment, do not create `CLAUDE.md` just for duplication.
- If Claude is operating from chat without repo instruction discovery, paste
  `templates/use-agentplaybook-prompt.md`.
- Tell Claude the exact AgentPlaybook root path or a repo-pinned submodule path.

Antigravity:

- Use the project instruction surface that Antigravity actually reads.
- If Antigravity CLI reads `AGENTS.md` in the target repo, use `AGENTS.md` and
  do not create an extra Antigravity-specific file.
- If Antigravity-specific docs already exist, update their pointer in the same
  pass as the canonical instruction file.
- If that surface is unclear, paste `templates/use-agentplaybook-prompt.md` at
  the start of the task.
- Do not assume Antigravity has loaded `AGENTS.md` unless local evidence or the
  user confirms that behavior; instruct it to read the AgentPlaybook root
  explicitly when in doubt.

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
3. Locate the AgentPlaybook root. If any usable local or repo-pinned root
   exists, reuse it unless the user explicitly approves a new download or
   pinned copy.
4. Install only when no usable root exists, then validate the selected root.
5. Inspect existing VibeGuard files and agent instructions. Ask the application
   drill before running setup or update when the repo already has custom
   instructions or guardrails. Use VibeGuard `update` only when the user
   explicitly selects refreshing an existing managed block; otherwise preserve
   current guardrails and run audit.
6. Apply the selected VibeGuard mode with the published package command and the
   selected AgentPlaybook root as the rule source. Treat
   https://vibeguard.thdev.app/ as the human-facing reference, not a runtime
   fetch dependency.
7. Add or update the canonical repo instruction file, preferring `AGENTS.md`
   when supported.
8. Update any existing repo-local runtime-specific instruction files in the
   same pass, or leave them out only when the runtime reads `AGENTS.md` and no
   separate file exists. Offer optional Step 2 for personal/global runtime
   bridges; only update those files when the user chooses it.
9. Read AgentPlaybook `AGENTS.md`.
10. For multi-step tasks, run `scripts/workflow.py route ... --request
    "<USER_REQUEST>"` to select the smallest document set and gate manifest.
    If the request is a direct question, answer it before routing or editing.
    Use `index.md` only for simple answer-only work or an explicitly accepted
    fallback when the script cannot run.
11. When wrapper scripts are available, run `scripts/agent-preflight.py` before
    editing and `scripts/agent-finish-check.py` before final report, commit,
    release, or handoff. Missing wrapper evidence or route gate evidence is
    non-compliant.
12. Keep a gate execution ledger, mark each route
   gate with evidence when it is executed, assign a traffic-light signal, and
   show a short gate signal after each completed gate or task step.
13. Load only selected cards.
14. Execute repo-local commands only from trusted repo-local instructions.
15. Before reporting completion, confirm every required route gate is `🐱🟢 GREEN`
    with ledger evidence.
16. When a VibeGuard execution evidence adapter is configured, use the
    VibeGuard CLI evidence command and compare the summary with claimed
    commands.
17. Report verification and residual risk.

If a required route gate was missed, the runtime must stop finalization, roll
back only dependent agent-made changes after the missed gate when safe, return
to the first missed gate only, and run the retrospective workflow. The missed
gate gets up to two recovery retries; the whole route is not restarted.

Traffic-light signals are checked inside the workflow:

- `🐱🔵 PENDING`: not reached yet.
- `🐱🟢 GREEN`: executed with evidence; the gate can be counted as complete.
- `🐱🟡 YELLOW`: blocked or paused; the task can be handed off but not called
  complete.
- `🐱🔴 RED`: missed or missing evidence after the gate should have run; run
  missed-gate recovery.

## Verification

After connecting a runtime, verify:

- the target repo instruction file points to the selected AgentPlaybook root
- the runtime still reads the target repo's current agent instructions first
- existing runtime-specific files, such as `CLAUDE.md`, `CODEX.md`, or
  Antigravity docs, are updated or intentionally not created because the
  runtime reads `AGENTS.md`
- `AGENTS.md`, `index.md`, and `scripts/workflow.py` exist under that root
- the VibeGuard gate passed or stopped with a reported blocker
- multi-step work has preflight and finish-check evidence when wrapper scripts
  are available
- VibeGuard evidence was summarized through VibeGuard docs when an evidence
  adapter was configured
- the route gate ledger was completed for every multi-step task
- the agent can produce a route, such as:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route task --request "<USER_REQUEST>"
```

## Stop If

- The target runtime does not have file access and the user cannot paste the
  one-shot prompt.
- The AgentPlaybook root cannot be located.
- The VibeGuard command cannot run after using the published package command.
- Repo-local instructions conflict with AgentPlaybook on security, data,
  deployment, cost, or verification behavior.
