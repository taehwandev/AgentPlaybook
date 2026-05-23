---
keyflow_id: sys_apply_agentplaybook_request_template
status: review
type: human-reviewed-needed
---

# Apply AgentPlaybook Request

Paste this into an AI coding agent when you want it to connect a project to
AgentPlaybook.

```text
Apply AgentPlaybook to this project:
https://github.com/taehwandev/AgentPlaybook

Use an existing local AgentPlaybook install if one is available. Check an
explicit path from me first, then AGENTPLAYBOOK_HOME, then common local clones
such as ~/.agent-playbook or ~/GitHub/AgentPlaybook.

If a usable install exists, link this repo to that copy. Do not clone, vendor,
or copy a second copy.

If no usable install exists, ask before cloning to ~/.agent-playbook or adding
AgentPlaybook as a repo-pinned submodule.

VibeGuard is required. After selecting the AgentPlaybook root, run VibeGuard
setup and audit with that root as --rules. Use the local vibe-guard command if
available, otherwise use:

npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard -- vibe-guard setup . --rules <AGENTPLAYBOOK_ROOT>
npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard -- vibe-guard audit . --rules <AGENTPLAYBOOK_ROOT> --fix
npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard -- vibe-guard audit . --rules <AGENTPLAYBOOK_ROOT>

If VibeGuard cannot run, stop and tell me the blocker.

Update the repo-local agent instructions, such as AGENTS.md, CLAUDE.md, CODEX.md,
or .agents/README.md, with a short routing block. Preserve existing project
rules. Keep repo-specific commands, paths, services, product policy, and domain
language in this repo.

After connecting it, verify that the referenced AgentPlaybook AGENTS.md and
index.md files exist, confirm VibeGuard is passing, then continue with my
original task.
```

For a team-pinned install, add this sentence:

```text
Prefer a repo-pinned submodule or vendored dependency so every teammate and
agent uses the same reviewed AgentPlaybook version.
```
