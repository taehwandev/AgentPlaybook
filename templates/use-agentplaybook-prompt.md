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

VibeGuard human docs:
https://vibeguard.thdev.app/

Rules:
1. Identify the target repo and read repo-local instructions first, including
   AGENTS.md, AGENTS.override.md, CLAUDE.md, CODEX.md, .agents/README.md,
   CONTRIBUTING.md, task docs, PRD/ARD docs, or equivalent project docs.
   Do not rely on implicit runtime discovery. If you are Codex-style, explicitly
   read the current project's AGENTS.md or AGENTS.override.md; if you are
   Claude, explicitly read CLAUDE.md when present; if you are Antigravity,
   explicitly read the current project's AGENTS.md; if you are another runtime,
   explicitly read the project instruction document that runtime is configured
   to load.
2. Do not assume this runtime automatically loaded AgentPlaybook. Explicitly
   read <AGENTPLAYBOOK_ROOT>/AGENTS.md and <AGENTPLAYBOOK_ROOT>/index.md.
3. Do not copy the whole AgentPlaybook library into this repo. Link only the
   relevant root, index, workflow script, and selected cards. If you edit
   committed repo-local instruction files, use a portable root reference such
   as ${AGENTPLAYBOOK_HOME} or a repo-relative pinned path like
   .agents/AgentPlaybook; do not commit a personal absolute path. Full local
   paths are acceptable only in this one-shot prompt, shell env setup, or
   uncommitted user-level runtime bridges.
4. VibeGuard is required. Before editing documentation, code, config,
   dependency, data, deployment, or credential surfaces, inspect existing
   VibeGuard files and agent instructions. If they already exist, ask the
   application drill before running setup or update. Then apply the selected
   VibeGuard mode with the published package command and <AGENTPLAYBOOK_ROOT>
   as the rule source. The VibeGuard site is a human reference and does not
   need to be fetched by the agent. If the VibeGuard command cannot run, stop
   and report the blocker. Use VibeGuard update only when I explicitly choose
   to refresh an existing managed block.
5. For multi-step tasks, run this before selecting task documents, editing,
   reviewing, committing, or reporting completion:
   python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py list
   python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py classify "<USER_REQUEST>"
   python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route <COMMAND> --request "<USER_REQUEST>" [--platform <PLATFORM>] [--concern <CONCERN>]
   Use the route output as the command manifest.
   If the request is a direct question, answer it before routing or editing.
   If the direct question asks how to start app, product, or feature work,
   answer with PRD -> ARD -> implementation gates before lower-level coding
   steps. If the task then proceeds into code, use the product route unless an
   existing PRD/ARD or repo-local instruction makes the slice clearly trivial.
   If the workflow router cannot run, stop and report the blocker before
   continuing.
   Use the lowest capable effort level. Do not use deep reasoning or a
   specialist agent for clear, low-risk requests unless local evidence expands
   the scope.
6. When available, run this wrapper before editing, reviewing, committing, or
   reporting completion:
   python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-preflight.py --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> --command <COMMAND> --request "<USER_REQUEST>" [--platform <PLATFORM>] [--concern <CONCERN>]
   It records the route, git status, and VibeGuard result in
   <TARGET_REPO>/.agentplaybook/preflight.json.
7. Keep a gate execution ledger from the route output. Mark each required gate
   when it is executed, include concrete evidence such as a command, file, diff,
   manual check, or decision note, and assign a traffic-light signal:
   `🐱🔵 PENDING` for not reached, `🐱🟢 GREEN` for executed with evidence,
   `🐱🟡 YELLOW` for blocked or paused, and `🐱🔴 RED` for missed or missing
   evidence. Do not reconstruct the ledger from memory at the end.
8. After each completed gate or task step, show:
   Gate signal: 🐱🟢 GREEN | gate: <gate> | evidence: <evidence> | next: <next gate>
9. If any required gate was not executed, stop before final report, commit,
   release, or handoff. Roll back only dependent agent-made changes after the
   missed gate when safe, preserve user-owned changes, return to the first
   missed gate only, and run the retrospective workflow. The missed gate gets
   up to two recovery retries; do not restart the whole route.
10. When a gate is missed, the retrospective must include `AI mistake`,
   `Proposed fix`, and `Discussion result`. Write the discussion result in the
   user's language for the task.
11. Load only the listed documents and the smallest relevant platform, product,
   or common cards. Do not load every shared document by default.
12. Discover the repo stack before choosing package managers, framework APIs, or
   project commands. Preserve user-owned worktree changes.
13. When commands fail, read stdout/stderr and fix only the smallest relevant
   issue. Do not blindly retry, delete tests, or silence errors.
14. Ask only blocker questions. Prefer concrete options with tradeoffs and a
   recommended default.
15. Before finishing, confirm every required route gate is `🐱🟢 GREEN` with ledger
    evidence. Before executing wrapper commands, replace
    `<AGENTPLAYBOOK_ROOT>` with the resolved absolute path; do not leave
    `$HOME`, `${HOME}`, `~`, or a relative path in the executable command. When
    available, run:
    python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-finish-check.py --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> --gate "request intake=<evidence>" --gate "orient=<evidence>" --gate "scope=<evidence>" --gate "act=<evidence>" --gate "verify=<evidence>" --gate "report=<evidence>"
    Missing wrapper evidence or missing route gate evidence is non-compliant.
    If `--request-classified` is used, include `--classification-evidence`.
    If the request asks for a question drill, missing drill evidence is `🐱🔴 RED`.
    If final VibeGuard is `🐱🟡 YELLOW` / `Needs review`, report that state and pass
    `--allow-vibeguard-review "<reason>"` only when the review state is
    acceptable. Then report changed files, checks run, skipped checks, and
    residual risk.
```

## Choosing The Route

Use these common command profiles:

- General task: `task`
- Product PRD/ARD to implementation: `product`
- Feature: `feature` only after PRD/ARD is satisfied or unnecessary for a
  scoped trivial slice
- Bug or failing command: `bugfix --concern failure`
- PRD/product requirements note only: `prd`
- Documentation update: `docs --concern wiki`
- Documentation review: `docs-review --concern wiki`
- Code review or commit readiness: `review`
- Release or versioning: `release`

Add `--platform web`, `--platform ios`, `--platform android`,
`--platform server`, or `--platform application` when a platform is touched.
Repeat `--concern` for each touched risk area.
