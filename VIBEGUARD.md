---
keyflow_id: sys_a3d290ee7b45
status: draft
type: ai-generated
---

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

## Recommended Commands

Run VibeGuard from the public GitHub package:

```bash
npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard -- vibe-guard audit . --rules .
```

Run the local checkout during development:

```bash
node ~/GitHub/vibe-guard/src/cli.js audit . --rules .
```

Use `--fix` only for low-risk safety fixes such as env ignore rules,
value-free `.env.example` updates, or simple secret quarantine:

```bash
npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard -- vibe-guard audit . --rules . --fix
```

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
npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard -- vibe-guard audit . --rules .
```

If npm cache permissions block the GitHub package command locally, use a
temporary cache:

```bash
npm_config_cache=/private/tmp/agentplaybook-npm-cache npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard -- vibe-guard audit . --rules .
```
