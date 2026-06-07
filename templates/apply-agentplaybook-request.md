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

## Step 1: Required Application Prompt

```text
Step 1 - Apply AgentPlaybook to this project:
https://github.com/taehwandev/AgentPlaybook

Before changing anything, open and read this project's current agent instructions first:
AGENTS.md, AGENTS.override.md, CLAUDE.md, CODEX.md, .agents/README.md,
CONTRIBUTING.md, task docs, PRD/ARD docs, or equivalent project docs.
Do not rely on implicit runtime discovery: Codex-style agents must explicitly
read the current project's AGENTS.md or AGENTS.override.md, Claude must
explicitly read CLAUDE.md when present, Antigravity agents must explicitly read
the current project's AGENTS.md, and generic agents must explicitly read the
project instruction document they are configured to load.
Do not claim the file was read unless you actually opened it.

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

Check user-level runtime hooks and permission allowlists:

python3 <AGENTPLAYBOOK_ROOT>/scripts/setup-agent-hooks.py --check

If the check reports missing hooks or permissions, ask for approval to update
user-level runtime config, then run:

python3 <AGENTPLAYBOOK_ROOT>/scripts/setup-agent-hooks.py

This setup is global by design. It allows only the current AgentPlaybook Python
entrypoints under `<AGENTPLAYBOOK_ROOT>/scripts/*.py` by exact path and
suffix-aware runtime matcher. It must not broadly allow `python3`.
For Codex, update `~/.codex/rules/default.rules` with direct `python3 <script>`
argv prefixes for the same scripts using resolved absolute paths only. Do not
use `$HOME`, `${HOME}`, `~`, relative paths, or shell `-lc` wrappers for
AgentPlaybook Python wrappers: those forms can be treated as shell expansion or
a single shell string before the runtime permission matcher sees the trusted
script path. For Claude Code, update `~/.claude/settings.json`. For
AGY/Antigravity, support both
`~/.gemini/config/config.json` and
`~/.gemini/antigravity-cli/settings.json`; hooks remain in
`~/.gemini/config/hooks.json`.

Do not install token-usage event hooks from AgentPlaybook. Spill token metering
is optional and belongs to the separate Spill installer. If the local Spill
setup helper exists, AgentPlaybook setup may add a safe workflow label bridge.
If the helper is absent, remove only AgentPlaybook-managed Spill label hooks/env
and keep the normal AgentPlaybook Python wrapper permissions.

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

If I explicitly choose to refresh the managed VibeGuard block:

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

When writing committed repo-local instruction files, do not commit my personal
absolute path such as /Users/.../AgentPlaybook. Use ${AGENTPLAYBOOK_HOME} for a
shared local install, or a repo-relative pinned path such as
.agents/AgentPlaybook for a team-pinned install. Full local paths are allowed
only in shell environment setup, one-shot prompts, or uncommitted user-level
runtime bridges. If an existing committed instruction file contains a personal
absolute path, replace it with a portable reference before reporting success.

Prefer AGENTS.md as the canonical instruction file when the active runtimes read
it. If repo-local Claude, Codex, Antigravity CLI, or other runtime instruction
files are present, update their AgentPlaybook pointer in the same pass or point
them back to AGENTS.md. Do not create a separate runtime-specific file only to
duplicate guidance when the active runtime already reads AGENTS.md.

For any multi-step setup or follow-up task, run the workflow route with
`--request "<USER_REQUEST>"` before selecting task documents, editing,
reviewing, committing, or reporting completion. If the request is a direct
question, answer it before routing or editing. If the direct question asks how
to start app, product, or feature work, answer with PRD -> ARD ->
implementation gates before lower-level coding steps. If the task proceeds into
code, use the `product` route unless an existing PRD/ARD or repo-local
instruction makes the slice clearly trivial. If the workflow router cannot run,
stop and report the blocker before continuing. Show a gate signal after each
completed gate or task step:

Gate signal: 🐱🟢 GREEN | gate: <gate> | evidence: <evidence> | next: <next gate>

Completion requires every required gate to be 🐱🟢 GREEN. 🐱🔵 PENDING means not
reached, 🐱🟡 YELLOW means blocked or paused, and 🐱🔴 RED means the gate was
missed or lacks evidence and must use missed-gate recovery.

When the wrapper scripts are available, run preflight before editing, reviewing,
committing, or reporting completion:

Before executing wrapper commands, replace `<AGENTPLAYBOOK_ROOT>` with the
resolved absolute path; do not leave `$HOME`, `${HOME}`, `~`, or a relative path
in the executable command.

python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-preflight.py --project . --rules <AGENTPLAYBOOK_ROOT> --command <COMMAND> --request "<USER_REQUEST>" [--platform <PLATFORM>] [--concern <CONCERN>]

Before final report, commit, release, or handoff, run finish check with evidence
for every required route gate:

python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-finish-check.py --project . --rules <AGENTPLAYBOOK_ROOT> --gate "request intake=<evidence>" --gate "orient=<evidence>" --gate "scope=<evidence>" --gate "act=<evidence>" --gate "verify=<evidence>" --gate "report=<evidence>"

The wrappers write local evidence under .agentplaybook/. Missing wrapper
evidence or missing gate evidence is non-compliant even if the final files look
correct. If final VibeGuard is 🐱🟡 YELLOW / Needs review, report it explicitly
and pass --allow-vibeguard-review with a reason only when that review state is
acceptable. If --request-classified is used, include classification evidence. If
the request asks for a question drill, missing drill evidence is 🐱🔴 RED.

After connecting it, verify that the referenced AgentPlaybook AGENTS.md and
index.md files exist, confirm the VibeGuard gate is passing, then continue with
my original task.
```

## Step 2: Optional User-Level Bridge Prompt

```text
Optional Step 2 - Register a user-level runtime bridge on this machine.

Use this only if I choose the optional setup for better future agent behavior.
Preserve existing personal instructions. Add or update a short managed block; do
not replace unrelated user content.

Also run the AgentPlaybook runtime setup check:

python3 <AGENTPLAYBOOK_ROOT>/scripts/setup-agent-hooks.py --check

If hooks or permissions are missing, ask for approval to update user-level
runtime config and then run:

python3 <AGENTPLAYBOOK_ROOT>/scripts/setup-agent-hooks.py

Keep the permission allowlist narrow: allow only the current AgentPlaybook
`scripts/*.py` files by exact path and suffix-aware runtime matcher, not broad
`python3`.

Update the active user-level file for the runtime I choose:
Codex -> ~/.codex/AGENTS.md
Claude -> ~/.claude/CLAUDE.md
Antigravity -> ~/.antigravity/AGENTS.md
Antigravity SDK/IDE variants -> check ~/.antigravity-ide for the instruction
file the active runtime loads.

The bridge must force this behavior:
- Start every task by identifying the current project root.
- Before project work, open the project-root instruction file for the active runtime.
- Codex reads AGENTS.md / AGENTS.override.md.
- Claude reads CLAUDE.md.
- Antigravity reads AGENTS.md.
- Do not claim an instruction file was read unless you actually opened it.
- If the active runtime is Antigravity and this bridge or the project-root
  AGENTS.md cannot be confirmed, stop before routing, editing, testing,
  committing, or reporting completion and ask for bridge repair.
- Do not mention setup, hook, permission, helper, label, or background metering
  details in normal conversation unless I explicitly ask about that subsystem.
- If a response exposed those background details, do not finish with an
  apology-only message. Repair the action path or stop with the specific
  blocker.
- If I ask a direct question, answer it before routing, editing, or running commands.
- If I ask how to start app, product, or feature work, include PRD -> ARD ->
  implementation before lower-level coding steps.
- If my request is ambiguous and the answer changes behavior, scope, safety, or
  external state, ask before working.
- For multi-step tasks, require AgentPlaybook preflight and finish-check
  evidence when those wrapper scripts are available; missing wrapper or gate
  evidence is non-compliant.
```

For a team-pinned install, add this sentence:

```text
Prefer a repo-pinned submodule or vendored dependency so every teammate and
agent uses the same reviewed AgentPlaybook version.
```
