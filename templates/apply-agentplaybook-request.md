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

If any usable local or repo-pinned AgentPlaybook root exists, stop install
selection there and reuse it. Do not download, clone, vendor, copy, overwrite,
or add a second AgentPlaybook root unless I explicitly approve after you ask:
"AgentPlaybook already exists locally at <path>. Do you want me to download or
pin a new copy anyway, or should I reuse the existing root?"

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
with the selected AgentPlaybook root as the rule source.

Before changing files, inspect this repo's current agent instructions,
.vibeguard.json, VIBEGUARD.md, and any managed VibeGuard block.

If this repo already has instructions or guardrails, ask me this application
drill before running setup or update:

1. AgentPlaybook link style: add a short pointer, merge into the current
   instruction file, or pin a repo-local copy?
2. VibeGuard handling: audit only with current guardrails, refresh the managed
   block with update, or first-time setup?
3. Scope: apply now and continue my original task, or prepare instructions only?

If I choose audit-only:

npx --yes @taehwandev/vibeguard audit . --rules <AGENTPLAYBOOK_ROOT>

If I choose to refresh the managed VibeGuard block:

npx --yes @taehwandev/vibeguard update . --rules <AGENTPLAYBOOK_ROOT>
npx --yes @taehwandev/vibeguard audit . --fix --rules <AGENTPLAYBOOK_ROOT>
npx --yes @taehwandev/vibeguard audit . --rules <AGENTPLAYBOOK_ROOT>

If this repo has never used VibeGuard and I choose first-time setup:

npx --yes @taehwandev/vibeguard setup . --rules <AGENTPLAYBOOK_ROOT>
npx --yes @taehwandev/vibeguard audit . --fix --rules <AGENTPLAYBOOK_ROOT>
npx --yes @taehwandev/vibeguard audit . --rules <AGENTPLAYBOOK_ROOT>

For full VibeGuard usage, use https://vibeguard.thdev.app/ as a human
reference. Do not block only because your browsing/fetch tool cannot read that
site. Continue with the package command shape above, and use
`npx --yes @taehwandev/vibeguard --help` if you need to confirm the CLI.

If VibeGuard cannot run, stop and tell me the blocker.

Update the repo-local agent instructions, such as AGENTS.md,
AGENTS.override.md, CLAUDE.md, CODEX.md, or .agents/README.md, with a short
routing block. Preserve existing project rules. Keep repo-specific commands,
paths, services, product policy, and domain language in this repo.

Prefer AGENTS.md as the canonical instruction file when the active runtimes read
it. If existing Claude, Codex, Antigravity CLI, or other runtime instruction
files are present, update their AgentPlaybook pointer in the same pass or point
them back to AGENTS.md. Do not create a separate runtime-specific file only to
duplicate guidance when the runtime already reads AGENTS.md.

For any multi-step setup or follow-up task, run the workflow route before
selecting task documents, editing, reviewing, committing, or reporting
completion. If the workflow router cannot run, stop and report the blocker
before continuing. Show a gate signal after each completed gate or task step:

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
