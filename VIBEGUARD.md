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
required setup, update, audit, prompt, evidence, and safe-fix CLI.

## Execution Policy

VibeGuard is required. The default application source is the published package:

```bash
npx --yes @taehwandev/vibeguard <command> [project]
```

An installed local `vibeguard` binary is equivalent. A local checkout command is
allowed only when validating VibeGuard itself or when the package command cannot
run and the checkout is trusted. If VibeGuard cannot run from any approved
source, stop and report the blocker instead of continuing without the safety
gate.

## Audit Commands

Run the official package command during normal AgentPlaybook maintenance:

```bash
npx --yes @taehwandev/vibeguard audit . --rules .
```

Run an installed binary when the environment provides one:

```bash
vibeguard audit . --rules .
```

Use `vibeguard` as the canonical command name. Do not document deprecated
hyphenated command spellings for new setup.

Use a local checkout only when validating local VibeGuard changes:

```bash
node <VIBEGUARD_ROOT>/src/cli.js audit . --rules .
```

## Auxiliary Commands

Use the prompt command only when a user or runtime wants a generated safety
prompt for a concrete request:

```bash
vibeguard prompt . --request "<request>" --rules .
```

Use evidence only when the target runtime has an execution evidence adapter or
session evidence available:

```bash
vibeguard evidence .
vibeguard evidence install-claude-hook .
```

## Setup And Fix Policy

- Before running `setup` or `update` in a target repo, inspect existing
  repo-local instructions, `.vibeguard.json`, `VIBEGUARD.md`, and managed
  VibeGuard blocks.
- If the target already has instructions or guardrails, ask an application drill
  before changing files: add pointer vs merge vs pin; audit-only vs refresh
  with update vs first-time setup; apply now vs prepare instructions only.
- Existing custom guardrails should default to audit-only unless the user
  chooses to refresh the managed block.
- Initial AgentPlaybook application in a repo with no guardrails should use the
  current VibeGuard package flow with the selected AgentPlaybook root as
  `--rules`:

  ```bash
  npx --yes @taehwandev/vibeguard setup . --rules <AGENTPLAYBOOK_ROOT>
  npx --yes @taehwandev/vibeguard audit . --fix --rules <AGENTPLAYBOOK_ROOT>
  npx --yes @taehwandev/vibeguard audit . --rules <AGENTPLAYBOOK_ROOT>
  ```

- Existing managed VibeGuard guardrails should be refreshed with
  `npx --yes @taehwandev/vibeguard update . --rules <AGENTPLAYBOOK_ROOT>` only
  when that mode is selected, then checked with the package audit command.
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
- For target repos that apply AgentPlaybook, apply VibeGuard with the selected
  AgentPlaybook root as `--rules`.
- For normal AgentPlaybook repository maintenance, run `audit . --rules .`
  before editing and before finishing.
- When an execution evidence adapter is configured, run `vibeguard evidence .`
  before final reporting and do not claim checks that are not supported by
  command output or evidence.

## Verification

Before finishing AgentPlaybook changes, run:

```bash
python3 scripts/workflow.py validate
npx --yes @taehwandev/vibeguard audit . --rules .
```
