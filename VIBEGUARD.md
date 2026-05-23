---
keyflow_id: sys_vibeguard_policy
status: review
type: human-reviewed-needed
---

# VIBEGUARD.md

This repository requires VibeGuard as the preflight safety gate for maintaining
AgentPlaybook itself.

## Scope

This file applies to edits in the AgentPlaybook repository. It should not be
treated as downstream policy for every repository that links to AgentPlaybook.

AgentPlaybook remains a reusable guidance library. VibeGuard remains the
required setup, audit, and safe-fix CLI.

## Execution Policy

VibeGuard is required, but the execution source should be explicit.

Prefer these sources in order:

1. A repo-pinned or team-approved VibeGuard checkout.
2. An already installed local `vibe-guard` binary.
3. A reviewed GitHub package ref, pinned to a tag or commit.

Do not run an unpinned GitHub package command in unattended automation. If no
trusted VibeGuard source is available, stop and report the blocker instead of
continuing without the safety gate.

## Audit Commands

Run the local checkout during development when it is available:

```bash
node <VIBEGUARD_ROOT>/src/cli.js audit . --rules .
```

Run an installed binary when the repo or environment provides one:

```bash
vibe-guard audit . --rules .
```

When a local source is unavailable, use a maintainer-reviewed ref:

```bash
npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard#<VIBEGUARD_REF> -- vibe-guard audit . --rules .
```

Replace `<VIBEGUARD_REF>` with a reviewed tag or commit. The approved ref should
come from one of these sources:

- the target repo's local agent instructions
- a pinned submodule, lockfile, or tool manifest
- a release note, issue, PR, or commit reviewed by the repo maintainer
- an explicit user-provided ref in the current task

If no approved ref is available, ask for one or stop with the blocker. Do not
invent a ref from the latest branch head.

## Setup And Fix Policy

- Initial AgentPlaybook application should run `vibe-guard setup` first, then
  `vibe-guard audit`.
- Normal AgentPlaybook maintenance should run audit-only before editing and
  before finishing.
- Use `--fix` only after audit output shows low-risk safety fixes such as env
  ignore rules, value-free `.env.example` updates, or simple secret quarantine.
- Do not use `--fix` for code rewrites, dependency changes, data changes,
  credential rotation, deletion, deployment, or release work without explicit
  approval.

## Rules

- Do not print detected secret values.
- Keep real secrets only in ignored local env files or deployment secret stores.
- Keep `.env.example` value-free.
- Ask before deleting data, running migrations, deploying, changing credentials,
  or increasing paid API/model usage.
- For target repos that apply AgentPlaybook, run VibeGuard setup/audit with the
  selected AgentPlaybook root as `--rules`.
- For normal AgentPlaybook repository maintenance, run `audit . --rules .`
  before editing and before finishing.

## Verification

Before finishing AgentPlaybook changes, run:

```bash
python3 scripts/workflow.py validate
node <VIBEGUARD_ROOT>/src/cli.js audit . --rules .
```

If the local checkout is unavailable and a reviewed GitHub package ref is
approved, use a temporary npm cache when local npm permissions require it:

```bash
npm_config_cache=/private/tmp/agentplaybook-npm-cache npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard#<VIBEGUARD_REF> -- vibe-guard audit . --rules .
```
