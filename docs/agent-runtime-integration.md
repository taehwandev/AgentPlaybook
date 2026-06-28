---
keyflow_id: sys_agent_runtime_integration
status: review
type: human-reviewed-needed
---

# Agent Runtime Integration

Use this when connecting AgentPlaybook to Codex, Claude, Antigravity, or another
AI coding agent runtime.

## Model

AgentPlaybook should be consumed through a small bridge, not copied wholesale:

1. Reusable library: one AgentPlaybook root.
2. Runtime bridge: repo-local instructions or a pasted prompt.
3. Task route: `scripts/workflow.py` output for the current task.
4. Safety gate: current VibeGuard application flow using AgentPlaybook as the
   rule source.

Repo-local instructions remain the source of truth for commands, paths,
services, product policy, and domain language.

## Setup Modes

Select one mode before wiring a runtime:

- Existing local install: required by default when AgentPlaybook is already
  present on the machine. Reuse that root and do not clone another copy unless
  the user explicitly approves a new copy after seeing the found path.
- First-time local shared install: clone once to a stable path such as
  `~/.agent-playbook` when no usable root exists.
- Team-pinned install: use a submodule, vendored dependency, or workspace
  dependency when every teammate and agent must use the same reviewed version.

A usable root contains `AGENTS.md`, `index.md`, and `scripts/workflow.py`.
Validate the selected root with:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py validate
```

Check runtime hooks and permission allowlists with:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/setup-agent-hooks.py --check
```

If hooks or permissions are missing, ask for approval to write user-level
runtime config, then run:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/setup-agent-hooks.py
```

This permission setup is global because the AgentPlaybook Python wrappers are
shared by every target repo. Keep it narrow: allow only the current
`<AGENTPLAYBOOK_ROOT>/scripts/*.py` files by exact path and suffix-aware
runtime matcher. Do not broadly allow `python3`.
When executing AgentPlaybook wrapper commands from an agent runtime, replace
`<AGENTPLAYBOOK_ROOT>` with the resolved absolute path. Do not leave `$HOME`,
`${HOME}`, `~`, or a relative path in the executable command.

Spill token metering is an optional local bridge, not an AgentPlaybook
dependency. AgentPlaybook setup does not install token-usage event hooks; those
belong to the Spill installer. If the local Spill setup helper exists,
`setup-agent-hooks.py` may add AgentPlaybook-managed safe workflow label hooks
and runtime env for that bridge. If the helper is absent, the setup removes
only those AgentPlaybook-managed Spill label hooks/env and keeps the Python
wrapper permissions installed.

For Antigravity/AGY, the runtime bridge is fail-closed. `setup-agent-hooks.py`
manages a short block in `~/.antigravity/AGENTS.md`; `--check` reports it as
missing when the block is absent or stale. The block must tell AGY to stop before
routing, editing, testing, committing, or reporting completion when it cannot
confirm the bridge or project-root `AGENTS.md`. It must also keep setup, hook,
permission, helper, label, and background metering details out of normal
conversation unless the user explicitly asks about that subsystem.

If a usable root is found, runtime setup must stop install selection there and
reuse it. Do not download, clone, vendor, copy, overwrite, or add a second root
unless the user approves this question:

```text
AgentPlaybook already exists locally at <path>. Do you want me to download or
pin a new copy anyway, or should I reuse the existing root?
```

## Project Discovery Entry

When a runtime starts from a personal directory such as `~`, or when the target
repo is not explicit in the current request, resolve the project before reading
project docs or running task commands. Use the local entry helpers:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/project-discover.py --request "<USER_REQUEST>" --cwd "<CURRENT_DIRECTORY>"
python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-entry.py --runtime <codex|claude|antigravity|generic> --request "<USER_REQUEST>" --cwd "<CURRENT_DIRECTORY>"
```

`project-discover.py` returns one of three states:

- `selected`: a single target project is safe to use; open its instruction
  files before project work.
- `ambiguous`: multiple candidates have comparable evidence; ask the user to
  choose one before reading project docs, editing, testing, committing, or
  reporting completion.
- `not_found`: no usable project was found; ask for the target path before
  project work.

`agent-entry.py` wraps the same discovery result with the AgentPlaybook root,
workflow script, preflight script, finish-check script, selected project
instruction files, workspace scope guidance, runtime launch guidance, and
next-step checklist. User-level runtime bridges should call it when the current
working directory might not be the target project.

Project discovery uses safe local evidence only: explicit paths in the request,
the current working directory, common project markers, repo-local instruction
files, configured search roots, and an optional local registry. It does not
scan broad home directories by default; pass `--search-root` for a known parent
or `--include-default-search-roots` only when the user accepts that broader
search cost and ambiguity risk. It must not use prompt guessing as a substitute
for a selected project. If the result is ambiguous or missing, stop and ask.

Optional local project registry:

```json
{
  "projects": [
    {
      "root": "~/Downloads/nunu-os-main",
      "aliases": ["nunu", "nunu-os"]
    }
  ],
  "workspace_groups": [
    {
      "name": "product-x",
      "aliases": ["product-x"],
      "members": [
        {
          "role": "app",
          "root": "~/GitHub/product-x-app",
          "aliases": ["app", "desktop"]
        },
        {
          "role": "web",
          "root": "~/GitHub/product-x-web",
          "aliases": ["web"]
        }
      ]
    }
  ],
  "search_roots": ["~/Documents", "~/Downloads"]
}
```

Store that file at `~/.agentplaybook/projects.json`, or pass a specific path
with `--registry`. The registry is local machine state and may contain personal
paths; do not commit it to target repos. This is separate from global
retrospective lessons, which must remain reusable and path-free.

Use `workspace_groups` when a product alias can mean several repos, such as an
app shell, web surface, shared API, or docs repo. If only the group alias
matches the request, discovery should not guess a single repo. It should return
the primary candidates and require a target decision. If a member alias also
matches, such as `web` or `desktop`, that member can become the selected
primary repo.

## Runtime Launch Root Discipline

Project instructions and runtime launch roots solve different problems.
`AGENTS.md`, `CLAUDE.md`, `CODEX.md`, and `.agents/README.md` tell the agent
what behavior to follow. They do not grant filesystem write scope. When a
runtime starts from `~`, a workspace parent, or a different repo, first run
`agent-entry.py`; when it returns `selected`, start or relaunch the runtime with
the selected target project as the primary workspace.

For Codex, use the selected repo as `-C`:

```text
codex -C <TARGET_REPO>
```

When the current task may also edit or run shared AgentPlaybook files, add the
selected AgentPlaybook root explicitly:

```text
codex -C <TARGET_REPO> --add-dir <AGENTPLAYBOOK_ROOT>
```

Use `--add-dir` only for additional roots that belong in the current session's
workspace. Prefer one selected target repo over broad parent folders such as
`~/GitHub` when the target is known. Do not use unrestricted filesystem modes
as the default fix for missing workspace roots.

`agent-entry.py --runtime codex` includes these launch commands in its
`runtime_launch` section after project discovery succeeds. User-level runtime
bridges may show this section to the operator or use it as a relaunch hint, but
they must still stop on `ambiguous` or `not_found`.

## Cross-Repo Scope Checkpoint

For multi-repo products, distinguish the primary repo from secondary repos:

- Primary repo: the repo whose user path or acceptance result defines success
  for the current task.
- Secondary repo: a repo that may need to be read or changed because it owns a
  web route, app bridge, shared contract, API schema, configuration, docs, or
  other source of truth.

Start with the primary repo when the request is clear. During orientation, stop
for a workspace scope checkpoint before writing to a secondary repo. The
checkpoint must state:

```text
starting primary:
new source of truth:
secondary repo:
mode: single-repo | primary-led secondary read | primary-led secondary write | multi-session
write scope:
verification:
session model:
```

Use these modes:

- `single-repo`: only the primary repo is changed and verified.
- `primary-led secondary read`: the primary repo remains the only write target;
  the secondary repo is inspected to confirm contracts or behavior.
- `primary-led secondary write`: the primary repo owns acceptance, but a small
  secondary repo change is needed. Use one session with the primary as `-C` and
  the secondary as an added workspace only when the write scope is small and
  clearly bounded.
- `multi-session`: both repos need meaningful implementation, verification, or
  commits. Use separate sessions and a lead agent or lead checklist for the
  shared contract, ordering, verification, and commit split.

Do not silently broaden from one repo to another because investigation found a
related file. If the secondary change is more than a small bounded contract,
route, bridge, config, or docs update, prefer `multi-session`.

When wrapper finish evidence is available and a secondary repo was written, add
one of these gates to the finish check:

```text
--gate "workspace scope checkpoint=<checkpoint evidence>"
--gate "scope expansion checkpoint=<checkpoint evidence>"
--gate "cross-repo scope checkpoint=<checkpoint evidence>"
```

The finish-check policy validates that the evidence names the starting primary
repo, secondary/source-of-truth repo, chosen mode, and cross-repo verification.

## Long-Lived Repo Setup

For repos that will keep using AgentPlaybook, add a short routing block to the
instruction file each agent runtime reads:

- Codex-style runtimes: `AGENTS.md`.
- Claude-style runtimes: `CLAUDE.md`.
- Codex-specific local docs: `CODEX.md` when the repo already uses it.
- Antigravity: `AGENTS.md`.
- Generic agents: the project instruction file the runtime actually reads, or
  `.agents/README.md` when the repo uses a shared agent folder.
- Personal or global runtime docs: treat these as optional Step 2 bridge work.
  Update them only when the user chooses the stronger future-behavior setup.
  Examples include `~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md`,
  `~/.antigravity`, `~/.antigravitycli`, and `~/.antigravity-ide`.

Prefer one canonical instruction file, usually `AGENTS.md`, when all active
runtimes read it. When `CLAUDE.md`, `CODEX.md`, `.agents/README.md`, or
Antigravity CLI docs already exist, update them in the same application pass so
they point to the selected AgentPlaybook root or back to `AGENTS.md`. Do not
create a separate runtime-specific file only to duplicate guidance that the
runtime already reads from `AGENTS.md`.

Every runtime bridge must explicitly tell the agent to read the current target
project's own instructions first. Do not rely on implicit discovery. State the
runtime-specific entrypoint directly: Codex-style agents should read the current
project's `AGENTS.md`, Claude should read the current project's `CLAUDE.md`
when present, Codex-specific setups should read `CODEX.md` when present, and
Antigravity should read the current project's `AGENTS.md`.
Then tell the agent to follow AgentPlaybook as shared guidance only after those
local instructions.

Use `templates/repo-agents-routing.md` as the source block. Keep the block
short and point to:

```text
<AGENTPLAYBOOK_ROOT>/AGENTS.md
<AGENTPLAYBOOK_ROOT>/index.md
<AGENTPLAYBOOK_ROOT>/scripts/agent-entry.py
<AGENTPLAYBOOK_ROOT>/scripts/project-discover.py
<AGENTPLAYBOOK_ROOT>/scripts/workflow.py
<AGENTPLAYBOOK_ROOT>/scripts/setup-agent-hooks.py
<AGENTPLAYBOOK_ROOT>/scripts/agent-preflight.py
<AGENTPLAYBOOK_ROOT>/scripts/agent-finish-check.py
```

For committed repo-local instruction files, keep the root reference portable.
Use `${AGENTPLAYBOOK_HOME}` when each machine can set the variable, or a
repo-relative pinned path such as `.agents/AgentPlaybook` when the playbook is
kept with the target repo. Do not commit personal absolute paths such as
`/Users/.../AgentPlaybook`; keep them in shell environment setup, one-shot
prompts, or uncommitted user-level runtime bridges only.

Do not paste the full playbook into runtime-specific files.

## One-Shot Prompt Setup

Use one-shot prompting when:

- the target repo is not wired yet
- the agent runtime does not automatically load repo instruction files
- you are using a web chat or temporary session
- you want Claude, Antigravity, or another agent to follow AgentPlaybook for one
  task without changing repo files

Paste `templates/use-agentplaybook-prompt.md` into the agent, replacing the
target repo, task, AgentPlaybook root, and VibeGuard docs placeholders.

The prompt explicitly tells the runtime to read `AGENTS.md` and `index.md`,
because not every agent automatically discovers Codex-style `AGENTS.md` files.

## Runtime Notes

Codex:

- Prefer repo-local `AGENTS.md` plus the routing block.
- Start Codex with the selected target repo as the primary workspace:
  `codex -C <TARGET_REPO>`.
- Add `--add-dir <AGENTPLAYBOOK_ROOT>` only when the task must include the
  shared playbook root in the session workspace, such as maintaining
  AgentPlaybook itself or editing shared runtime bridge files.
- Do not expect `AGENTS.md` or `.codex/rules` to change sandbox roots; they
  control behavior and permission matching, not the runtime's workspace root.
- Use the workflow router for multi-step work.
- AgentPlaybook command permissions belong in user-level
  `~/.codex/rules/default.rules` as narrow `prefix_rule` entries for the
  current `<AGENTPLAYBOOK_ROOT>/scripts/*.py` files.
- Generate direct `python3 <script>` argv prefixes for those same scripts using
  resolved absolute paths only. Agents should invoke these wrappers as direct
  argv commands, not through `$HOME`, `${HOME}`, `~`, relative paths, or shell
  `-lc` strings; once the absolute script path is a separate argv item, long
  trailing workflow arguments such as repeated `--gate` values are
  suffix-matched by the runtime policy and should not prompt again.
- When a Codex tool call needs escalation, request the persistent permission
  with `prefix_rule=["python3", "/absolute/path/to/AgentPlaybook/scripts/<name>.py"]`.
  Do not include changing arguments such as `--project`, `--request`, `--gate`,
  `$(pwd)`, or user-provided text in the saved prefix.
- `setup-agent-hooks.py` should leave only absolute, parameter-free
  AgentPlaybook script prefix rules in the managed Codex block and remove stale
  AgentPlaybook rules that were saved with `$HOME`, `${HOME}`, `~`, relative
  script paths, shell `-lc`, or command-specific arguments.
- Keep Codex-specific commands or sandbox notes in the target repo, not in the
  shared playbook.

Claude:

- If `CLAUDE.md` already exists, update it with the routing block or a pointer
  to `AGENTS.md`.
- If no Claude-specific file exists and Claude reads `AGENTS.md` in the target
  environment, do not create `CLAUDE.md` just for duplication.
- If Claude is operating from chat without repo instruction discovery, paste
  `templates/use-agentplaybook-prompt.md`.
- Tell Claude the exact AgentPlaybook root path or a repo-pinned submodule path.
- AgentPlaybook command permissions belong in the user-level
  `~/.claude/settings.json`, not repo-local `.claude/settings.json`, because
  the AgentPlaybook `scripts/*.py` entrypoints are shared across projects.
- Claude AgentPlaybook permissions should be absolute wrapper command prefixes
  with the runtime's trailing wildcard form for arguments, for example
  `Bash(python3 /absolute/path/to/AgentPlaybook/scripts/agent-hook.py *)`.
  Do not approve or document `$HOME`, `${HOME}`, `~`, relative
  `scripts/<name>.py`, or argument-specific variants for shared wrappers.

Antigravity:

- Use `AGENTS.md` as the project instruction surface that Antigravity reads.
- The managed user-level bridge installed by `setup-agent-hooks.py` must tell
  AGY to run `agent-entry.py` or `project-discover.py` before project work when
  it starts outside the target repo or cannot identify one clear target.
- Do not create an extra Antigravity-specific file only to duplicate guidance
  already available from `AGENTS.md`.
- If Antigravity-specific docs already exist, update their pointer in the same
  pass as the canonical instruction file.
- If local evidence shows a different active instruction surface, stop and ask
  before adding duplicate guidance.
- Do not assume Antigravity has loaded `AGENTS.md` unless local evidence or the
  user confirms that behavior; instruct it to read the AgentPlaybook root
  explicitly when in doubt.
- AgentPlaybook command permissions may live in
  `~/.gemini/config/config.json` or the legacy
  `~/.gemini/antigravity-cli/settings.json`, depending on the active AGY
  runtime. Runtime hooks remain in `~/.gemini/config/hooks.json`.
- AGY AgentPlaybook permissions follow the same absolute-wrapper rule as
  Claude, using the AGY permission key shape, for example
  `command(python3 /absolute/path/to/AgentPlaybook/scripts/agent-hook.py *)`.
  Avoid `$HOME`, `${HOME}`, `~`, relative script paths, and saved prefixes that
  include task-specific arguments.

Generic agents:

- Use `.agents/README.md` or the runtime's documented project instruction file.
- If file discovery is unavailable, use the one-shot prompt.

## Required Flow

For every runtime:

1. Identify the target repo. If the runtime started outside the repo, the
   target is not explicit, or multiple repos match the request, run
   `scripts/agent-entry.py` or `scripts/project-discover.py` first. Continue
   only when discovery returns `selected`; ask the user when it returns
   `ambiguous` or `not_found`.
2. Read the current repo-local instructions:
   `AGENTS.md`, `CLAUDE.md`, `CODEX.md`, `.agents/README.md`,
   `CONTRIBUTING.md`, task docs, PRD/ARD docs, equivalent project guidance, or
   explicitly documented local override files.
3. Select the setup mode: existing local install, first-time local shared
   install, or team-pinned install.
4. Locate the AgentPlaybook root. If any usable local or repo-pinned root
   exists, reuse it unless the user explicitly approves a new download or
   pinned copy.
5. Install only when no usable root exists, then validate the selected root.
6. Run `scripts/setup-agent-hooks.py --check`. If hooks or permissions are
   missing, ask for approval to update user-level runtime config, then run
   `scripts/setup-agent-hooks.py`.
7. Inspect existing VibeGuard files and agent instructions. Ask the application
   drill before running setup or update when the repo already has custom
   instructions or guardrails. Use VibeGuard `update` only when the user
   explicitly selects refreshing an existing managed block; otherwise preserve
   current guardrails and run audit.
8. Apply the selected VibeGuard mode with an installed `vibeguard` binary when
   available, using the selected AgentPlaybook root as the rule source. Use the
   published package command only when no trusted binary exists or an explicit
   latest-package check is needed. Treat https://vibeguard.thdev.app/ as the
   human-facing reference, not a runtime fetch dependency.
9. Add or update the canonical repo instruction file, preferring `AGENTS.md`
   when supported.
10. Update any existing repo-local runtime-specific instruction files in the
   same pass, or leave them out only when the runtime reads `AGENTS.md` and no
   separate file exists. Offer optional Step 2 for personal/global runtime
   bridges; only update those files when the user chooses it.
11. Read AgentPlaybook `AGENTS.md`.
12. For multi-step tasks, run `scripts/workflow.py route ... --request
    "<USER_REQUEST>"` to select the smallest document set and gate manifest.
    If the request is a direct question, answer it before routing or editing.
    Use `index.md` only for simple answer-only work or an explicitly accepted
    fallback when the script cannot run.
13. When wrapper scripts are available, run `scripts/agent-preflight.py` before
    editing and `scripts/agent-finish-check.py` before final report, commit,
    release, or handoff. Missing wrapper evidence or route gate evidence is
    non-compliant.
14. Keep a gate execution ledger, mark each route gate with evidence when it is
   executed or fails, assign only `🐱🟢 SUCCESS` or `🐱🔴 FAIL`, and show a
   short gate signal after each completed or failed gate or task step.
15. Load only selected cards.
16. Execute repo-local commands only from trusted repo-local instructions.
17. Before reporting completion, confirm every required route gate is
    `🐱🟢 SUCCESS` with ledger evidence.
18. When a VibeGuard execution evidence adapter is configured, use the
    VibeGuard CLI evidence command and compare the summary with claimed
    commands.
19. Report verification and residual risk.

## Lifecycle Aliases

Runtimes may expose short lifecycle commands for convenience, but they should
call AgentPlaybook routing instead of creating a second active workflow router.

| Alias | Route Command | Primary Use |
| --- | --- | --- |
| `/spec` | `spec` | requirements note, PRD, acceptance criteria, open decisions |
| `/plan` | `plan` | research, options, recommendation before implementation |
| `/build` | `build` | scoped feature or implementation slice |
| `/test` | `test` | verification-only work or test evidence collection |
| `/review` | `review` | code, diff, risk, and verification review |
| `/webperf` | `webperf` | browser/web performance measurement and review |
| `/code-simplify` | `code-simplify` | behavior-preserving simplification and refactor cleanup |
| `/ship` | `ship` | release, packaging, rollout, rollback, and launch checks |

The alias should run:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route <route-command> --request "<USER_REQUEST>"
```

Do not let aliases bypass request intake, preflight, route docs, VibeGuard,
review hook, finish-check, or repo-local instructions.

## Controlled Auto Mode

Do not add an unrestricted "auto build" or "auto ship" mode to a runtime bridge.
Automation may proceed without another question only when all of these are true:

- the user approved the goal or the repo has an explicit auto-run policy;
- project discovery selected exactly one target repo;
- the route command, docs, gates, and verification surface are known;
- destructive work, external writes, deploys, migrations, publishing,
  credential changes, and paid-usage increases are out of scope or separately
  approved;
- each slice still runs preflight, route docs, review hook when required,
  finish-check, and the nearest verification.

If any condition fails, the runtime should stop at a decision point instead of
continuing under an "auto" label.

If a required route gate was missed, the runtime must stop finalization, roll
back only dependent agent-made changes after the missed gate when safe, return
to the first missed gate only, and run the retrospective workflow. The missed
gate gets one recovery retry; the whole route is not restarted.

Human-visible signals are checked inside the workflow:

- `🐱🟢 SUCCESS`: executed with evidence; the gate can be counted as complete.
- `🐱🔴 FAIL`: blocked, failed, missed, or missing evidence after the gate should
  have run; run missed-gate recovery.

Do not report any third gate state. Gates that have not been reached are simply
absent from progress reports.

## Verification

After connecting a runtime, verify:

- the target repo instruction file points to the selected AgentPlaybook root
- `agent-entry.py` or `project-discover.py` selects the target repo when the
  runtime starts outside it, or stops with `ambiguous` / `not_found`
- workspace group aliases either select a clear member repo or return primary
  candidates with workspace scope guidance instead of guessing
- the runtime still reads the target repo's current agent instructions first
- existing runtime-specific files, such as `CLAUDE.md`, `CODEX.md`, or
  Antigravity docs, are updated or intentionally not created because the
  runtime reads `AGENTS.md`
- `AGENTS.md`, `index.md`, and `scripts/workflow.py` exist under that root
- `setup-agent-hooks.py --check` passed or missing user-level hooks or
  permissions were installed after approval
- the VibeGuard gate passed or stopped with a reported blocker
- multi-step work has preflight and finish-check evidence when wrapper scripts
  are available
- VibeGuard evidence was summarized through VibeGuard docs when an evidence
  adapter was configured
- the route gate ledger was completed for every multi-step task
- the agent can produce a route, such as:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route task --request "<USER_REQUEST>"
```

## Stop If

- The target runtime does not have file access and the user cannot paste the
  one-shot prompt.
- Project discovery is ambiguous or missing and the user has not chosen a
  target project.
- The AgentPlaybook root cannot be located.
- The VibeGuard command cannot run after using the installed binary or the
  published package fallback.
- Repo-local instructions conflict with AgentPlaybook on security, data,
  deployment, cost, or verification behavior.
