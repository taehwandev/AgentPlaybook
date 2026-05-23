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
AGENTS.md, AGENTS.override.md, CLAUDE.md, CODEX.md, .agents/README.md,
CONTRIBUTING.md, task docs, PRD/ARD docs, or equivalent project docs.

If AgentPlaybook already exists locally, link this repo to the existing copy.
Do not clone, vendor, or copy a second copy unless no usable local copy exists.
Apply the required VibeGuard safety gate by following
https://vibeguard.thdev.app/ and use the selected AgentPlaybook root as the
rule source.
Update the repo-local agent instructions with a short routing block. Keep
repo-specific commands, paths, services, product policy, and domain language in
this repo.
```

For one-shot task use without editing repo-local instructions, use
`templates/use-agentplaybook-prompt.md`.

For runtime-specific setup across Codex, Claude, Antigravity, and generic
agents, use `docs/agent-runtime-integration.md`.

## Setup Decision

Choose the setup mode before editing the target repo:

1. Existing local install: use this when the user already has AgentPlaybook on
   the machine. Link to that root and do not clone or vendor a second copy.
2. First-time local shared install: use this when no usable copy exists and the
   user wants one install reused across personal repos. Clone once to a stable
   path such as `~/.agent-playbook`.
3. Team-pinned install: use this when the repo needs a reviewed version shared
   by teammates and agents. Add a submodule, vendored dependency, or workspace
   dependency only after approval.

Always report which setup mode was selected before changing repo-local
instructions.

## Discovery Order

1. Identify the target project from the user's request and current working
   directory.
2. Read the target project's current agent instructions before changing files:
   `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`, `CODEX.md`,
   `.agents/README.md`, `CONTRIBUTING.md`, task docs, PRD/ARD docs, or
   equivalent project docs.
3. Check whether the user supplied an explicit AgentPlaybook path.
4. Check `AGENTPLAYBOOK_HOME`.
5. Check legacy `KEYFLOW_AGENT_ROOT` only when present.
6. Check common local installs such as `~/.agent-playbook`,
   `~/AgentPlaybook`, and `~/GitHub/AgentPlaybook`.
7. Check repo-pinned locations only when the target repo already contains one,
   such as `.agents/AgentPlaybook`, `tools/AgentPlaybook`, or a git submodule.

A usable AgentPlaybook root contains both:

```text
AGENTS.md
index.md
scripts/workflow.py
```

If a usable root is found, use it. Do not reinstall.

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
npx --yes @taehwandev/vibeguard audit . --rules <AGENTPLAYBOOK_ROOT>
```

Refresh an existing managed VibeGuard block only when requested:

```bash
npx --yes @taehwandev/vibeguard update . --rules <AGENTPLAYBOOK_ROOT>
npx --yes @taehwandev/vibeguard audit . --fix --rules <AGENTPLAYBOOK_ROOT>
npx --yes @taehwandev/vibeguard audit . --rules <AGENTPLAYBOOK_ROOT>
```

Use `setup` only for first-time target repos with no guardrails:

```bash
npx --yes @taehwandev/vibeguard setup . --rules <AGENTPLAYBOOK_ROOT>
npx --yes @taehwandev/vibeguard audit . --fix --rules <AGENTPLAYBOOK_ROOT>
npx --yes @taehwandev/vibeguard audit . --rules <AGENTPLAYBOOK_ROOT>
```

Full VibeGuard setup, audit, fix, package, and evidence flow lives in VibeGuard
docs:

```text
https://vibeguard.thdev.app/
```

If VibeGuard cannot run, stop and report the blocker. Do not continue as if the
safety gate were optional.

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

## Connect The Target Repo

1. Find the repo-local instruction file: `AGENTS.md`, `AGENTS.override.md`,
   `CLAUDE.md`, `CODEX.md`, `.agents/README.md`, or an equivalent project
   guide.
2. Preserve existing repo-local instructions.
3. Confirm the required VibeGuard gate passed or stopped with a reported
   blocker.
4. Add a short AgentPlaybook routing block with the selected root path.
5. Prefer `${AGENTPLAYBOOK_HOME}` when the environment variable is configured.
   Otherwise use the absolute path or repo-relative submodule path.
6. Link only `AGENTS.md`, `index.md`, and any direct route cards the repo wants.
7. Do not paste the full AgentPlaybook library into the repo-local file.
8. For multi-step setup or migration work, keep the workflow route gate ledger
   and verify every required gate is `GREEN` with evidence before reporting
   success.

Use `templates/repo-agents-routing.md` as the routing block source.

## Verify

Before reporting success:

- The selected AgentPlaybook root exists.
- `AGENTS.md` and `index.md` exist under that root.
- The VibeGuard gate ran with the selected AgentPlaybook root as the rule
  source.
- The target repo's local instruction file still contains its original
  repo-specific rules.
- The routing block points to the selected root.
- No secrets, local credentials, private prompts, or unrelated files were added.

## Stop If

- The target project is ambiguous.
- The user asked only for advice and did not ask to edit the repo.
- No usable local copy exists and network access is unavailable or not approved.
- VibeGuard cannot run after following https://vibeguard.thdev.app/.
- Existing repo-local instructions conflict with AgentPlaybook in a way that
  changes security, data handling, verification, deployment, or cost behavior.
