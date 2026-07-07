---
keyflow_id: sys_agentplaybook_agent_bootstrap
status: review
type: human-reviewed-needed
---

# AgentPlaybook Agent Bootstrap

Use when an AI coding agent receives the AgentPlaybook repository link or a
request to apply AgentPlaybook to a target project.

The goal is to connect the target repo to one reusable AgentPlaybook install. Do
not copy the full playbook into the target repo.

## Pasteable User Request

```text
Apply AgentPlaybook to this project:
https://github.com/taehwandev/AgentPlaybook

Before changing anything, read this project's current agent instructions first:
AGENTS.md, CLAUDE.md, CODEX.md, .agents/README.md, CONTRIBUTING.md, task docs,
PRD/ARD docs, equivalent project docs, or explicitly documented local override
files.

If AgentPlaybook already exists locally, link this repo to the existing copy.
Do not clone, vendor, or copy a second copy unless no usable local copy exists.
If a usable local copy exists but you think a fresh copy is needed, ask me
first: "AgentPlaybook already exists locally at <path>. Do you want me to
download or pin a new copy anyway, or should I reuse the existing root?"
Apply the required VibeGuard safety gate with the selected AgentPlaybook root
as the rule source. Use an installed `vibeguard` binary when available; use the
published package command only when no trusted binary exists or an explicit
latest-package check is needed. The VibeGuard site is a human reference and
does not need to be fetched by the agent.
Update the repo-local agent instructions with a short routing block. Keep
repo-specific commands, paths, services, product policy, and domain language in
this repo. If existing Claude, Codex, Antigravity, or other runtime instruction
files are present, update the necessary AgentPlaybook pointer there in the same
pass. If the runtime reads AGENTS.md, do not create a duplicate runtime-specific
file.
```

For one-shot task use without editing repo-local instructions, use
`templates/use-agentplaybook-prompt.md`.

For runtime-specific setup across Codex, Claude, Antigravity, and generic
agents, use `docs/agent-runtime-integration.md`.

## Setup Decision

Choose the setup mode before editing the target repo:

1. Existing local install: use this when the user already has AgentPlaybook on
   the machine. Link to that root and do not clone or vendor a second copy
   unless the user explicitly approves a new copy after seeing the found path.
2. First-time local shared install: use this when no usable copy exists and the
   user wants one install reused across personal repos. Clone once to a stable
   path such as `~/.agent-playbook`.
3. Team-pinned install: use this when the repo needs a reviewed version shared
   by teammates and agents. Add a submodule, vendored dependency, or workspace
   dependency only after approval.

Always report which setup mode was selected before changing repo-local
instructions.

## Local Reuse Guard

Local reuse is the default and a hard stop for install work:

- If discovery finds a usable local or repo-pinned root, select `Existing local
  install`.
- Do not download, clone, vendor, copy, overwrite, or add a second
  AgentPlaybook root while a usable root exists.
- If there is a concrete reason to use a fresh copy anyway, ask before any
  network, git, submodule, or filesystem action:

  ```text
  AgentPlaybook already exists locally at <path>. Do you want me to download or
  pin a new copy anyway, or should I reuse the existing root?
  ```

- Continue with a new download or pinned copy only after explicit approval.

## Discovery Order

1. Identify the target project from the user's request and current working
   directory.
2. If the runtime started from `~`, another non-project directory, or a
   directory that may not be the requested target, use the selected
   AgentPlaybook root's entry helper before project work:

   ```text
   python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-entry.py --request "<USER_REQUEST>" --cwd "<CURRENT_DIRECTORY>" --runtime <RUNTIME>
   ```

   Continue only when it returns `selected`. If it returns `ambiguous` or
   `not_found`, ask the user for the target project instead of guessing. Do not
   scan broad home directories by default; use an explicit path, registry alias,
   or known `--search-root` first.
3. Read the target project's current agent instructions before changing files:
   `AGENTS.md`, `CLAUDE.md`, `CODEX.md`, `.agents/README.md`,
   `CONTRIBUTING.md`, task docs, PRD/ARD docs, equivalent project docs, or an
   explicitly documented local override file.
4. Check whether the user supplied an explicit AgentPlaybook path.
5. Check `AGENTPLAYBOOK_HOME`.
6. Check legacy `KEYFLOW_AGENT_ROOT` only when present.
7. Check common local installs such as `~/.agent-playbook`,
   `~/AgentPlaybook`, and `~/GitHub/AgentPlaybook`.
8. Check repo-pinned locations only when the target repo already contains one,
   such as `.agents/AgentPlaybook`, `tools/AgentPlaybook`, or a git submodule.

A usable AgentPlaybook root contains all of:

```text
AGENTS.md
index.md
scripts/workflow.py
```

If a usable root is found, use it. Do not reinstall.
When `scripts/agent-preflight.py` and `scripts/agent-finish-check.py` exist in
that root, they are the required evidence wrappers for multi-step work.

## Required VibeGuard Gate

VibeGuard is mandatory. After selecting the AgentPlaybook root, apply
VibeGuard to the target repo before editing target repo instructions. Use the
selected AgentPlaybook root as the VibeGuard rule source.

Do not choose `setup` or `update` by file existence alone. First inspect:

- current repo-local agent instructions
- `.vibeguard.json`
- `VIBEGUARD.md`
- any managed VibeGuard block

When the target already has instructions or guardrails, ask this application
drill before changing files:

```text
Application drill:
1. AgentPlaybook link style: add a short pointer, merge into the current
   instruction file, or pin a repo-local copy?
2. VibeGuard handling: audit only with current guardrails, refresh the managed
   block with update, or first-time setup?
3. Scope: apply now and continue the original task, or prepare instructions
   only?
```

Audit only, preserving existing guardrails:

```bash
vibeguard audit . --rules <AGENTPLAYBOOK_ROOT>
```

Refresh an existing managed VibeGuard block only when the user explicitly
selects that option:

```bash
vibeguard update . --rules <AGENTPLAYBOOK_ROOT>
vibeguard audit . --fix --rules <AGENTPLAYBOOK_ROOT>
vibeguard audit . --rules <AGENTPLAYBOOK_ROOT>
```

Use `setup` only for first-time target repos with no guardrails:

```bash
vibeguard setup . --rules <AGENTPLAYBOOK_ROOT>
vibeguard audit . --fix --rules <AGENTPLAYBOOK_ROOT>
vibeguard audit . --rules <AGENTPLAYBOOK_ROOT>
```

If `vibeguard` is not installed, use the same command shapes with
`npx --yes @taehwandev/vibeguard` in place of `vibeguard`. Do not choose `npx`
first in repeated hooks or routine local maintenance; npm may contact the
registry and wait through network retry timeouts before VibeGuard itself starts.

Full VibeGuard setup, audit, fix, package, and evidence flow lives in VibeGuard
docs for humans:

```text
https://vibeguard.thdev.app/
```

Do not block only because an agent browsing/fetch tool cannot read the
VibeGuard site. Continue with the VibeGuard command shape above, and use
`vibeguard --help` when an installed binary is available. Use
`npx --yes @taehwandev/vibeguard --help` only as the missing-binary or
latest-package fallback. If the VibeGuard command itself cannot run, stop and
report the blocker. Do not continue as if the safety gate were optional.

## Install If Missing

If no usable local or repo-pinned copy exists, choose one of these modes:

- Local shared install: clone once to `~/.agent-playbook`. This is best for
  individual users and multiple personal repos.
- Repo-pinned install: add AgentPlaybook as a git submodule or vendored
  dependency. This is best for teams that need a reviewed version.
Ask before using network access, adding a submodule, changing git remotes, or
writing outside the target repo.

After installing or selecting a root, run:

```bash
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py validate
```

Then check runtime bridges, hooks, and permission allowlists:

```bash
python3 <AGENTPLAYBOOK_ROOT>/scripts/setup-agent-hooks.py --check
```

If the check reports missing bridges, hooks, or permissions, ask for approval
before writing user-level runtime config, then run:

```bash
python3 <AGENTPLAYBOOK_ROOT>/scripts/setup-agent-hooks.py
```

The setup is global because the workflow router, graph-backed document routing,
and evidence wrappers are shared across target repos. It must install or repair
only AgentPlaybook-managed bridge blocks and allow only the current
AgentPlaybook Python entrypoints by exact path, not broad `python3` execution:

```text
<AGENTPLAYBOOK_ROOT>/scripts/*.py
```

Claude Code permissions belong in `~/.claude/settings.json`. AGY/Antigravity
permissions may live in `~/.gemini/config/config.json` or the legacy
`~/.gemini/antigravity-cli/settings.json`; AGY hooks stay in
`~/.gemini/config/hooks.json`.

AgentPlaybook must not install token-usage event hooks. Spill token metering is
optional and owned by the separate Spill installer. When the local Spill setup
helper is present, AgentPlaybook may wire safe workflow label hooks; when it is
absent, setup should remove only AgentPlaybook-managed Spill label hooks/env and
leave normal AgentPlaybook routing intact.

For AGY/Antigravity, setup must also manage the user-level bridge in
`~/.antigravity/AGENTS.md`. The bridge is fail-closed: if AGY cannot confirm the
bridge or the project-root `AGENTS.md`, it must stop before routing, editing,
testing, committing, or reporting completion and ask for bridge repair. The
bridge must not mention setup, hook, permission, helper, label, or background
metering details in normal conversation unless the user explicitly asks about
that subsystem.

## Connect The Target Repo

1. Find the canonical repo-local instruction file. Prefer `AGENTS.md` when the
   active runtimes read it.
2. Also inspect existing runtime-specific instruction files, such as
   `CLAUDE.md`, `CODEX.md`, `.agents/README.md`, Antigravity CLI docs,
   equivalent project guides, or explicitly documented local override files.
3. Preserve existing repo-local instructions.
4. Confirm the required VibeGuard gate passed or stopped with a reported
   blocker.
5. Add a short AgentPlaybook routing block with the selected root path to the
   canonical instruction file. Do not create repo-local skill documents only to
   mirror shared AgentPlaybook guidance; keep repo-local skill or workflow docs
   only when they encode product-specific facts, commands, domain policy, or
   verification that cannot live in the shared library.
6. Update existing runtime-specific files in the same pass by adding the same
   short pointer or by pointing them back to `AGENTS.md`.
7. Do not create new runtime-specific instruction files when the runtime already
   reads `AGENTS.md`.
8. Keep committed repo-local paths portable. Prefer `${AGENTPLAYBOOK_HOME}` for
   a shared local install, or use a repo-relative pinned path such as
   `.agents/AgentPlaybook`. Do not commit personal absolute paths such as
   `/Users/.../AgentPlaybook`; use those only in shell env setup, one-shot
   prompts, or uncommitted user-level runtime bridges.
9. Link only `AGENTS.md`, `index.md`, and any direct route cards the repo wants.
   Prefer shared route cards over per-repo skill copies unless the repo has a
   genuine local skill surface.
10. Do not paste the full AgentPlaybook library into repo-local files.
11. For multi-step setup or migration work, run
   `python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route ... --request
   "<USER_REQUEST>"` before editing, keep the workflow route gate ledger,
   and verify every required gate is `🐱🟢 SUCCESS` with evidence before
   reporting success.
12. When wrapper scripts are available, run
   `python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-preflight.py ...` before edits
   and `python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-finish-check.py ...` before
   final report, commit, release, or handoff. Missing wrapper evidence or gate
   evidence is non-compliant. Human-visible status should use only
   `🐱🟢 SUCCESS` and `🐱🔴 FAIL` badges. Do not report any third gate state.

Use `templates/repo-agents-routing.md` as the routing block source.

## Verify

Before reporting success:

- The selected AgentPlaybook root exists.
- `AGENTS.md` and `index.md` exist under that root.
- `setup-agent-hooks.py --check` either passed or missing user-level bridges,
  hooks, or permissions were installed after approval.
- `agent-entry.py` or `project-discover.py` selects the target repo when the
  runtime starts outside it, or stops with `ambiguous` / `not_found`.
- The VibeGuard gate ran with the selected AgentPlaybook root as the rule
  source.
- Multi-step work has preflight and finish-check evidence when the wrapper
  scripts are available.
- The target repo's local instruction file still contains its original
  repo-specific rules.
- The routing block points to the selected root.
- Existing Claude, Codex, Antigravity, or other runtime instruction files are
  either updated with the same pointer or intentionally left unchanged with a
  reason.
- No duplicate runtime-specific instruction file was created when `AGENTS.md`
  is the runtime-read file.
- No secrets, local credentials, private prompts, or unrelated files were added.

## Stop If

- The target project is ambiguous.
- Project discovery returns `ambiguous` or `not_found` and the user has not
  chosen a target project.
- The user asked only for advice and did not ask to edit the repo.
- No usable local copy exists and network access is unavailable or not approved.
- The VibeGuard command cannot run after using the installed binary or the
  published package fallback.
- Existing repo-local instructions conflict with AgentPlaybook in a way that
  changes security, data handling, verification, deployment, or cost behavior.
