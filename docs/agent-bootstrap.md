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

If AgentPlaybook already exists locally, link this repo to the existing copy.
Do not clone, vendor, or copy a second copy unless no usable local copy exists.
Run VibeGuard setup and audit with the selected AgentPlaybook root as --rules.
Update the repo-local agent instructions with a short routing block. Keep
repo-specific commands, paths, services, product policy, and domain language in
this repo.
```

## Discovery Order

1. Identify the target project from the user's request and current working
   directory.
2. Check whether the user supplied an explicit AgentPlaybook path.
3. Check `AGENTPLAYBOOK_HOME`.
4. Check legacy `KEYFLOW_AGENT_ROOT` only when present.
5. Check common local installs such as `~/.agent-playbook`,
   `~/AgentPlaybook`, and `~/GitHub/AgentPlaybook`.
6. Check repo-pinned locations only when the target repo already contains one,
   such as `.agents/AgentPlaybook`, `tools/AgentPlaybook`, or a git submodule.

A usable AgentPlaybook root contains both:

```text
AGENTS.md
index.md
```

If a usable root is found, use it. Do not reinstall.

## Required VibeGuard Gate

VibeGuard is mandatory. After selecting the AgentPlaybook root, run VibeGuard
against the target repo before editing target repo instructions:

```bash
npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard -- vibe-guard setup . --rules <AGENTPLAYBOOK_ROOT>
npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard -- vibe-guard audit . --rules <AGENTPLAYBOOK_ROOT> --fix
npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard -- vibe-guard audit . --rules <AGENTPLAYBOOK_ROOT>
```

Use a local VibeGuard checkout or installed `vibe-guard` binary only when it is
already available and equivalent. If VibeGuard cannot run, stop and report the
blocker. Do not continue as if the safety gate were optional.

## Install If Missing

If no usable local or repo-pinned copy exists, choose one of these modes:

- Local shared install: clone once to `~/.agent-playbook`. This is best for
  individual users and multiple personal repos.
- Repo-pinned install: add AgentPlaybook as a git submodule or vendored
  dependency. This is best for teams that need a reviewed version.
Ask before using network access, adding a submodule, changing git remotes, or
writing outside the target repo.

## Connect The Target Repo

1. Find the repo-local instruction file: `AGENTS.md`, `CLAUDE.md`, `CODEX.md`,
   `.agents/README.md`, or an equivalent project guide.
2. Preserve existing repo-local instructions.
3. Confirm VibeGuard setup/audit passed or stopped with a reported blocker.
4. Add a short AgentPlaybook routing block with the selected root path.
5. Prefer `${AGENTPLAYBOOK_HOME}` when the environment variable is configured.
   Otherwise use the absolute path or repo-relative submodule path.
6. Link only `AGENTS.md`, `index.md`, and any direct route cards the repo wants.
7. Do not paste the full AgentPlaybook library into the repo-local file.

Use `templates/repo-agents-routing.md` as the routing block source.

## Verify

Before reporting success:

- The selected AgentPlaybook root exists.
- `AGENTS.md` and `index.md` exist under that root.
- VibeGuard setup/audit ran with the selected root as `--rules`.
- The target repo's local instruction file still contains its original
  repo-specific rules.
- The routing block points to the selected root.
- No secrets, local credentials, private prompts, or unrelated files were added.

## Stop If

- The target project is ambiguous.
- The user asked only for advice and did not ask to edit the repo.
- No usable local copy exists and network access is unavailable or not approved.
- VibeGuard cannot run locally or from the GitHub package URL.
- Existing repo-local instructions conflict with AgentPlaybook in a way that
  changes security, data handling, verification, deployment, or cost behavior.
