---
keyflow_id: sys_use_agentplaybook_prompt_template
status: review
type: human-reviewed-needed
---

# Use AgentPlaybook Prompt

Paste this into Claude, Antigravity, Codex, or another AI coding agent when the
target repo is not yet wired to AgentPlaybook or when you want a one-shot task
to follow AgentPlaybook explicitly.

Replace the placeholders before sending.

```text
Use AgentPlaybook for this task.

Target repo:
<TARGET_REPO_OR_CURRENT_DIRECTORY>

Task:
<TASK>

AgentPlaybook root:
<AGENTPLAYBOOK_ROOT>

VibeGuard source:
<LOCAL_OR_PINNED_VIBEGUARD_SOURCE>

Rules:
1. Identify the target repo and read repo-local instructions first, including
   AGENTS.md, AGENTS.override.md, CLAUDE.md, CODEX.md, .agents/README.md,
   CONTRIBUTING.md, task docs, PRD/ARD docs, or equivalent project docs.
2. Do not assume this runtime automatically loaded AgentPlaybook. Explicitly
   read <AGENTPLAYBOOK_ROOT>/AGENTS.md and <AGENTPLAYBOOK_ROOT>/index.md.
3. Do not copy the whole AgentPlaybook library into this repo. Link only the
   relevant root, index, workflow script, and selected cards.
4. VibeGuard is required. Before editing documentation, code, config,
   dependency, data, deployment, or credential surfaces, run:
   vibe-guard audit . --rules <AGENTPLAYBOOK_ROOT>
   If the local command is unavailable, use the local or pinned VibeGuard source
   I provided. Do not run an unpinned GitHub package command in unattended
   automation. If VibeGuard cannot run, stop and report the blocker.
5. For multi-step tasks, run:
   python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py list
   python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route <COMMAND> [--platform <PLATFORM>] [--concern <CONCERN>]
   Use the route output as the command manifest.
6. Keep a gate execution ledger from the route output. Mark each required gate
   when it is executed and include concrete evidence such as a command, file,
   diff, manual check, or decision note. Do not reconstruct the ledger from
   memory at the end.
7. After each completed gate or task step, show:
   Gate signal: <gate> / executed / evidence: <evidence> / next: <next gate>
8. If any required gate was not executed, stop before final report, commit,
   release, or handoff. Roll back only dependent agent-made changes after the
   missed gate when safe, preserve user-owned changes, return to the first
   missed gate only, and run the retrospective workflow. The missed gate gets
   one retry; do not restart the whole route.
9. When a gate is missed, the retrospective must include `AI mistake`,
   `Proposed fix`, and `Discussion result`. Write the discussion result in the
   user's language for the task.
10. Load only the listed documents and the smallest relevant platform, product,
   or common cards. Do not load every shared document by default.
11. Discover the repo stack before choosing package managers, framework APIs, or
   project commands. Preserve user-owned worktree changes.
12. When commands fail, read stdout/stderr and fix only the smallest relevant
   issue. Do not blindly retry, delete tests, or silence errors.
13. Ask only blocker questions. Prefer concrete options with tradeoffs and a
   recommended default.
14. Before finishing, confirm every required route gate has ledger evidence,
    rerun the relevant verification and VibeGuard audit, then
    report changed files, checks run, skipped checks, and residual risk.
```

## Choosing The Route

Use these common command profiles:

- General task: `task`
- Product PRD/ARD to implementation: `product`
- Feature: `feature`
- Bug or failing command: `bugfix --concern failure`
- PRD/product requirements note only: `prd`
- Documentation update: `docs --concern wiki`
- Documentation review: `docs-review --concern wiki`
- Code review or commit readiness: `review`
- Release or versioning: `release`

Add `--platform web`, `--platform ios`, `--platform android`,
`--platform server`, or `--platform application` when a platform is touched.
Repeat `--concern` for each touched risk area.
