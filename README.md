---
keyflow_id: sys_e2d59ab64adc
status: stable
type: ai-generated
---

# Agent Playbook

AgentPlaybook is a reusable guidance library for AI coding agents. It gives
agents a compact set of operating rules, workflow paths, review criteria,
platform guidance, and product-pattern checks that can be linked from any
software project.

Use it when you want repo-local instructions to stay small while still giving an
agent enough shared engineering discipline to plan, edit, review, test, and
handoff work reliably.

Repository:

```text
https://github.com/taehwandev/AgentPlaybook
```

## Who It Is For

- Teams that use AI coding agents across multiple repositories.
- Solo builders who want consistent agent behavior from project to project.
- Maintainers who want reusable review, safety, architecture, and workflow
  guidance without copying long prompt files into every repo.
- Tooling authors who need a source library of agent-readable engineering
  practices.

## What This Is

- A document library, not a framework or runtime.
- A source of shared agent instructions, not a replacement for repo-local rules.
- A selective-loading system: agents should read only the cards relevant to the
  current task.
- A public, reusable project. No local machine path, private workspace, product
  name, or personal environment is required.

## What This Is Not

- It is not a beginner product UI.
- It is not a secret scanner, package manager, or safety CLI.
- It is not a place for repo-specific commands, internal paths, credentials,
  private architecture, role matrices, product policy, or domain language.
- It is not meant to be copied wholesale into every project.

VibeGuard is the required safety gate for applying and maintaining
AgentPlaybook. Agents should apply VibeGuard with the published package command
and pass the selected AgentPlaybook root as the rule source. The VibeGuard site
is the human-facing reference, not a runtime dependency; do not block only
because an agent browsing/fetch tool cannot read the site.

Website:

```text
https://agentplaybook.thdev.app/
```

Korean update guide: [docs/ko/update-agentplaybook.md](docs/ko/update-agentplaybook.md)

## Quick Start

Choose one setup path first. Existing local or repo-pinned roots are the
default. If any usable AgentPlaybook root already exists, do not download,
clone, vendor, or copy another one unless the user explicitly approves a new
copy after being told which root was found.

### Path A: Existing Local Install

Use this when AgentPlaybook is already on the machine.

1. Locate the existing root. Prefer an explicit path from the user, then
   `AGENTPLAYBOOK_HOME`, then common local locations such as
   `~/.agent-playbook`, `~/AgentPlaybook`, or `~/GitHub/AgentPlaybook`.
2. Verify that the root contains `AGENTS.md`, `index.md`, and
   `scripts/workflow.py`.
3. Point the target repo to that root. Do not clone, vendor, or copy another
   AgentPlaybook checkout.

If a usable root is found but the agent believes a fresh download is needed,
it must ask first:

```text
AgentPlaybook already exists locally at <path>. Do you want me to download or
pin a new copy anyway, or should I reuse the existing root?
```

```bash
export AGENTPLAYBOOK_HOME="/path/to/existing/AgentPlaybook"
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" validate
```

### Path B: First-Time Local Shared Install

Use this when no usable local or repo-pinned copy exists and the user wants one
shared install for multiple personal repos.

```bash
export AGENTPLAYBOOK_HOME="$HOME/.agent-playbook"
git clone https://github.com/taehwandev/AgentPlaybook.git "$AGENTPLAYBOOK_HOME"
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" validate
```

### Path C: Team-Pinned Install

Use this when every teammate and agent must use the same reviewed version. Add
AgentPlaybook as a submodule, vendored dependency, or workspace dependency only
after the repo owner approves the pinned location and update policy.

```bash
git submodule add https://github.com/taehwandev/AgentPlaybook.git .agents/AgentPlaybook
python3 .agents/AgentPlaybook/scripts/workflow.py validate
```

### Updating An Existing Install

Use Git as the update mechanism. For a personal or shared local checkout, update
the selected AgentPlaybook root between tasks:

```bash
cd "${AGENTPLAYBOOK_HOME}"
git pull --ff-only
python3 scripts/workflow.py validate
npx --yes @taehwandev/vibeguard audit . --rules .
```

Target repos that link to this root do not need their own copied update. The
next agent task should read the current files from the selected
AgentPlaybook root. Do not auto-pull during an active task; update intentionally
between tasks so the workflow rules do not change mid-run.

For a team-pinned submodule, update the pinned commit through the target repo's
normal review flow:

```bash
cd <target-repo>
git submodule update --remote .agents/AgentPlaybook
python3 .agents/AgentPlaybook/scripts/workflow.py validate
git add .agents/AgentPlaybook
```

Public site: `https://agentplaybook.thdev.app/#update`

### Connect The Target Repo

After choosing the root, add a short pointer to the target repo's canonical
agent instruction file. Prefer `AGENTS.md` when the active runtimes read it.
If existing runtime-specific files such as `CLAUDE.md`, `CODEX.md`,
`.agents/README.md`, Antigravity CLI docs, or explicitly documented local
override files are present, update their AgentPlaybook pointer in the same pass
or point them back to `AGENTS.md`.
Do not create extra runtime-specific files only to duplicate the same routing
block.

Keep committed repo-local instructions portable. Do not write a personal
absolute path such as `/Users/.../AgentPlaybook` into files that will be shared
through Git. Use `${AGENTPLAYBOOK_HOME}` for a shared local install, or a
repo-relative path such as `.agents/AgentPlaybook` for a repo-pinned install.
Personal full paths belong only in shell environment setup, one-shot prompts,
or uncommitted user-level runtime bridges.

When starting an agent from `~`, a workspace parent, or another repo, resolve
the target first:

```bash
python3 "${AGENTPLAYBOOK_HOME}/scripts/agent-entry.py" --runtime codex --request "<USER_REQUEST>" --cwd "$PWD"
```

If discovery returns `selected`, use the reported `runtime_launch` guidance for
the next session. For Codex, the normal shape is:

```bash
codex -C <TARGET_REPO>
codex -C <TARGET_REPO> --add-dir "${AGENTPLAYBOOK_HOME}"
```

Use the second form only when the task needs the AgentPlaybook root in the
session workspace, such as maintaining shared playbook docs, scripts, or runtime
bridges. Repo instruction files decide behavior; `-C` and `--add-dir` decide
which filesystem roots the runtime can use without repeated prompts.

For products that span several repos, add a local workspace group to
`~/.agentplaybook/projects.json` instead of relying on prompt guessing:

```json
{
  "workspace_groups": [
    {
      "name": "product-x",
      "aliases": ["product-x"],
      "members": [
        {"role": "app", "root": "~/GitHub/product-x-app", "aliases": ["app", "desktop"]},
        {"role": "web", "root": "~/GitHub/product-x-web", "aliases": ["web"]}
      ]
    }
  ]
}
```

When an agent starts in one repo and discovers that another repo must be written,
it should stop for a workspace scope checkpoint before that write. The checkpoint
names the starting primary repo, secondary/source-of-truth repo, selected mode,
write scope, session model, and cross-repo verification.

```text
Shared AgentPlaybook guidance:
${AGENTPLAYBOOK_HOME}/AGENTS.md
${AGENTPLAYBOOK_HOME}/index.md
${AGENTPLAYBOOK_HOME}/scripts/workflow.py
${AGENTPLAYBOOK_HOME}/scripts/setup-agent-hooks.py
${AGENTPLAYBOOK_HOME}/scripts/agent-preflight.py
${AGENTPLAYBOOK_HOME}/scripts/agent-finish-check.py

Use repo-local instructions first.
For multi-step tasks, use the workflow script first when it exists.
When the preflight and finish-check wrappers exist, use them to create local
evidence before editing and before final report, commit, release, or handoff.
Use the shared index only to select the smallest relevant document set.
Do not load every shared document by default.
```

You can also vendor this repository as a submodule or workspace dependency if
your team wants a pinned version.

### Safety Gate

VibeGuard is required in every distribution mode, but its commands and
operating details live in VibeGuard docs. The AgentPlaybook-side contract is to
pass the selected AgentPlaybook root as the rule source.

Do not run `setup` or `update` blindly. First inspect the target repo for
existing agent instructions, `.vibeguard.json`, `VIBEGUARD.md`, or a managed
VibeGuard block. When any of those exist, ask a short application drill before
changing files:

```text
Application drill:
1. AgentPlaybook link style: add a short pointer (recommended), merge into the
   current instruction file, or pin a repo-local copy?
2. VibeGuard handling: audit only with current guardrails (recommended for
   existing custom docs), refresh the managed block with update, or first-time
   setup?
3. Scope: apply now and continue the original task, or prepare instructions
   only?
```

After the user answers, use the matching command shape.

Audit only, preserving existing guardrails:

```bash
export AGENTPLAYBOOK_HOME="/path/to/existing/AgentPlaybook"
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" validate
npx --yes @taehwandev/vibeguard audit . --rules "${AGENTPLAYBOOK_HOME}"
```

Refresh an existing managed VibeGuard block only when explicitly requested:

```bash
export AGENTPLAYBOOK_HOME="/path/to/existing/AgentPlaybook"
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" validate
npx --yes @taehwandev/vibeguard update . --rules "${AGENTPLAYBOOK_HOME}"
npx --yes @taehwandev/vibeguard audit . --fix --rules "${AGENTPLAYBOOK_HOME}"
npx --yes @taehwandev/vibeguard audit . --rules "${AGENTPLAYBOOK_HOME}"
```

First-time VibeGuard setup only when the target has no guardrails yet:

```bash
export AGENTPLAYBOOK_HOME="/path/to/existing/AgentPlaybook"
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" validate
npx --yes @taehwandev/vibeguard setup . --rules "${AGENTPLAYBOOK_HOME}"
npx --yes @taehwandev/vibeguard audit . --fix --rules "${AGENTPLAYBOOK_HOME}"
npx --yes @taehwandev/vibeguard audit . --rules "${AGENTPLAYBOOK_HOME}"
```

Full VibeGuard usage for humans: `https://vibeguard.thdev.app/`

If an agent cannot fetch that site, continue with the package command shape
above. To confirm the current CLI surface, run:

```bash
npx --yes @taehwandev/vibeguard --help
```

When applying AgentPlaybook, use the selected AgentPlaybook root as the
VibeGuard rule source. If VibeGuard cannot run, report the blocker instead of
bypassing the gate. Do not copy full VibeGuard onboarding or command reference
material into public AgentPlaybook docs; link to VibeGuard's current
instructions.

## Apply With Any AI Agent

Give an AI coding agent this request:

```text
Apply AgentPlaybook to this project:
https://github.com/taehwandev/AgentPlaybook

If AgentPlaybook already exists locally, link this repo to the existing copy.
Do not clone, vendor, or copy a second copy unless no usable local copy exists.
If a usable local copy exists but you think a fresh copy is needed, ask me
first: "AgentPlaybook already exists locally at <path>. Do you want me to
download or pin a new copy anyway, or should I reuse the existing root?"
Inspect the current repo instructions and VibeGuard files first. If either
already exists, ask me a short application drill before running setup or update.
Use the selected AgentPlaybook root as the VibeGuard rule source.
Update the repo-local agent instructions with a short routing block. Keep
repo-specific commands, paths, services, product policy, and domain language in
this repo. In committed repo-local instruction files, use a portable
AgentPlaybook root reference: `${AGENTPLAYBOOK_HOME}` for shared local installs
or a repo-relative pinned path such as `.agents/AgentPlaybook`; do not commit my
personal absolute path. If existing repo-local Claude, Codex, Antigravity, or
other runtime instruction files are present, update the necessary AgentPlaybook
pointer there in the same pass. If the runtime reads AGENTS.md, do not create a
duplicate runtime-specific file. Treat user-level runtime bridges as optional
Step 2 work, not part of the required application prompt.
```

### Actual Application Flow

When an agent applies AgentPlaybook to a target repo, it should execute this
flow instead of copying the whole library:

1. Identify the target repo and read its existing local instructions first.
2. Choose one setup mode: existing local install, first-time local shared
   install, or team-pinned install.
3. If any usable local or repo-pinned root exists, stop install selection there
   and reuse it unless the user explicitly approves a new download or pinned
   copy.
4. Validate the selected AgentPlaybook root with
   `python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py validate`.
5. Inspect existing VibeGuard and repo-local instruction files. Ask the
   application drill when the repo already has custom instructions or guardrails.
6. Apply the selected VibeGuard mode with the selected AgentPlaybook root as the
   rule source: audit-only, refresh with `update`, or first-time `setup`.
7. Add a short routing block to the repo instruction file the agent runtime
   actually reads, preferring `AGENTS.md` when supported.
8. Use a portable AgentPlaybook root reference in committed repo-local files:
   `${AGENTPLAYBOOK_HOME}` for shared local installs or a repo-relative pinned
   path such as `.agents/AgentPlaybook`. Personal absolute paths are allowed
   only in shell env setup, one-shot prompts, or uncommitted user-level runtime
   bridges. Replace existing committed personal paths before reporting success.
9. Keep repo-specific commands, paths, services, product policy, and domain
   language in the target repo.
10. Update any existing runtime-specific instruction files, such as
   `CLAUDE.md`, `CODEX.md`, `.agents/README.md`, or Antigravity CLI docs, so
   they point to the same AgentPlaybook root or back to `AGENTS.md`.
11. Do not create new runtime-specific instruction files when the active
    runtime already reads `AGENTS.md`.
12. Offer optional Step 2 for user-level runtime bridges. Only update personal
   or global runtime instruction files when the user chooses that option. The
   bridge must explicitly tell the runtime to read the current target project's
   local instructions first: Codex-style agents read `AGENTS.md`, Claude reads
   `CLAUDE.md`, and Antigravity reads `AGENTS.md`.
13. For follow-up work, run `workflow.py classify` when request clarity is
   uncertain, then `workflow.py route ... --request "<USER_REQUEST>"` and
   follow the gate ledger. Answer direct questions before routing.
14. When wrapper scripts are available, run `agent-preflight.py` before edits and
   `agent-finish-check.py` before final report, commit, release, or handoff.
15. Before reporting success, verify the routing block, VibeGuard gate result,
   and any route gates that were required.

## Prompt A Local Agent

When prompting Codex, Claude, Antigravity, or another local agent inside a
project, tell it to read the current project's own agent instructions first.
That keeps project commands, paths, product policy, and local constraints in the
target repo while AgentPlaybook supplies shared workflow discipline.

Use this shape for one task:

```text
Use this project's current agent instructions first.
Read whichever exist in the target repo:
AGENTS.md, CLAUDE.md, CODEX.md, .agents/README.md, CONTRIBUTING.md, task docs,
PRD/ARD docs, equivalent project docs, or explicitly documented local override
files.
Do not rely on implicit runtime discovery. Codex-style agents should explicitly
read the current project's AGENTS.md, Claude should read CLAUDE.md when
present, and Antigravity should read the current project's AGENTS.md before
AgentPlaybook.

Then use AgentPlaybook:
<AGENTPLAYBOOK_ROOT>/AGENTS.md
<AGENTPLAYBOOK_ROOT>/index.md
<AGENTPLAYBOOK_ROOT>/scripts/workflow.py
<AGENTPLAYBOOK_ROOT>/scripts/agent-preflight.py
<AGENTPLAYBOOK_ROOT>/scripts/agent-finish-check.py

Apply the required VibeGuard safety gate with <AGENTPLAYBOOK_ROOT> as the rule
source before editing. Use the published VibeGuard package command; the
VibeGuard site is a human reference and does not need to be fetched by the
agent.
For multi-step work, run the workflow route with `--request "<USER_REQUEST>"`
and follow its gate ledger. If the user asks a direct question, answer it before
starting project work.
When the wrapper scripts exist, run `agent-preflight.py` before editing and
`agent-finish-check.py` before final report, commit, release, or handoff. Missing
wrapper evidence or missing route gate evidence is non-compliant.
After each completed or failed gate or task step, show:
Gate signal: 🐱🟢 SUCCESS | gate: <gate> | evidence: <evidence> | next: <next gate>

Completion requires every required gate to be 🐱🟢 SUCCESS. 🐱🔴 FAIL means the
gate was blocked, failed, missed, or lacks evidence and must use missed-gate
recovery. Do not report any third gate state.

For PRD-only work:
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route prd --request "<USER_REQUEST>" --platform <platform> --concern <concern>

For PRD -> ARD -> implementation:
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route product --request "<USER_REQUEST>" --platform <platform> --concern <concern>
```

Full bootstrap instructions live in [docs/agent-bootstrap.md](docs/agent-bootstrap.md).
A shorter reusable prompt lives in
[templates/apply-agentplaybook-request.md](templates/apply-agentplaybook-request.md).

## Use With Codex, Claude, And Antigravity

AgentPlaybook is not tied to one runtime. Codex and Antigravity may discover
`AGENTS.md` directly, while Claude or generic agents may need a repo-local bridge
file or a pasted prompt.

- For long-lived repo setup, add the routing block from
  [templates/repo-agents-routing.md](templates/repo-agents-routing.md) to the
  instruction file the runtime reads, preferring `AGENTS.md` when supported.
  If `CLAUDE.md`, `CODEX.md`, `.agents/README.md`, or Antigravity CLI docs
  already exist, update their pointer in the same pass instead of leaving stale
  runtime guidance.
- For one-shot use, paste
  [templates/use-agentplaybook-prompt.md](templates/use-agentplaybook-prompt.md)
  into the agent with the target repo, task, AgentPlaybook root, and VibeGuard
  docs link filled in.
- For stronger future behavior, use the optional Step 2 prompt in
  [templates/apply-agentplaybook-request.md](templates/apply-agentplaybook-request.md)
  to update user-level runtime bridges such as `~/.codex/AGENTS.md`,
  `~/.claude/CLAUDE.md`, `~/.antigravity`, `~/.antigravitycli`, or
  `~/.antigravity-ide`.
- When a runtime starts from `~` or another non-project directory, resolve the
  target first with
  `python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-entry.py --request "<USER_REQUEST>" --cwd "<CURRENT_DIRECTORY>" --runtime <RUNTIME>`.
  Continue only when it returns `selected`; ask the user when it returns
  `ambiguous` or `not_found`. Optional local aliases can live in
  `~/.agentplaybook/projects.json`.
- To avoid repeated prompts for AgentPlaybook's required Python wrappers, run
  `python3 <AGENTPLAYBOOK_ROOT>/scripts/setup-agent-hooks.py --check`, then run
  `python3 <AGENTPLAYBOOK_ROOT>/scripts/setup-agent-hooks.py` after approval if
  user-level hooks or permissions are missing. This writes global runtime
  config only for AgentPlaybook-managed entrypoints; it does not broadly allow
  `python3`. Codex and AGY direct wrapper permissions use the resolved absolute
  AgentPlaybook path, not `$HOME`, `~`, relative paths, or shell `-lc` strings.
  Claude managed hooks use `~/.agentplaybook/bin/agentplaybook-hook` plus a
  refreshed `~/.agentplaybook/agentplaybook-root` pointer so moving or
  migrating the checkout does not leave `~/.claude/settings.json` pointing at
  a stale `scripts/workflow.py` path. Rerun setup after moving AgentPlaybook to
  refresh that pointer and repair stale managed hooks.
- Spill token metering is optional and separate. AgentPlaybook does not install
  token-usage event hooks. If the local Spill setup helper is present,
  `setup-agent-hooks.py` may wire a safe workflow label bridge; if the helper is
  absent, it removes only AgentPlaybook-managed Spill label hooks/env and leaves
  AgentPlaybook routing and evidence wrappers working normally.
- For Antigravity/AGY, `setup-agent-hooks.py --check` also verifies the managed
  user bridge in `~/.antigravity/AGENTS.md`. A missing or stale bridge is treated
  as missing setup so AGY cannot proceed as if the fail-closed and silence rules
  were installed.
- For runtime-specific setup rules, read
  [docs/agent-runtime-integration.md](docs/agent-runtime-integration.md).

## Distribution Modes

- Existing local install: required by default when the user already has
  AgentPlaybook. Link the target repo to that root and do not reinstall unless
  the user explicitly approves a new copy after seeing the found path.
- Local shared install: clone once to `~/.agent-playbook` and reuse it across
  personal repos.
- Team-pinned install: add AgentPlaybook as a git submodule or vendored
  dependency when every teammate and agent must use the same reviewed version.

In every mode, VibeGuard is mandatory. AgentPlaybook names that requirement and
the selected rule source; VibeGuard owns the operating flow. Use the published
VibeGuard package command, with https://vibeguard.thdev.app/ as the
human-facing reference. If an agent browsing/fetch tool cannot read the site,
do not treat that alone as a blocker. If the VibeGuard command itself cannot
run, report the blocker instead of bypassing the gate. The target repo keeps
its own commands, paths, services, product policy, and domain rules.
AgentPlaybook provides shared defaults only.

## Workflow Router

For multi-step work, agents must generate a route manifest before selecting
documents manually, editing, reviewing, committing, or reporting completion:

```bash
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" list
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" classify "Change the button on home"
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route triage --request "Change the button on home"
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route product --request "<USER_REQUEST>" --platform web --concern security --concern ui
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route feature --request "<USER_REQUEST>" --platform kmp --concern compose --concern state
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route feature --request "<USER_REQUEST>" --platform flutter --concern widget --concern state
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route docs-review --request "<USER_REQUEST>" --concern wiki
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" validate
```

Supported commands are `ambiguity`, `bugfix`, `docs`, `docs-review`, `feature`,
`multi-agent`, `planning`, `prd`, `product`, `refactor`, `release`,
`retrospective`, `review`, `task`, and `triage`.

Supported platforms are `android`, `application`, `flutter`, `ios`, `kmp`,
`server`, and `web`. Supported concerns are `accessibility`, `aeo`, `ai-mode`,
`ai-overviews`, `ai-search`, `ai-search-optimization`, `answer-engine`,
`answer-engine-optimization`, `api`, `asset`, `assets`, `auth`, `background`,
`billing`, `cache`, `canonical`, `channel`, `component`, `component-api`,
`compose`, `config`, `copy`, `defensive`, `dependency`, `desktop`, `discovery`,
`effort`, `error`, `errors`, `failure`, `generated`, `generative-ai`,
`generative-ai-search`, `geo`, `intake`, `interaction`, `invite`, `llms`,
`llms-txt`, `module`, `observability`, `open-graph`, `persistence`, `platform`,
`prose`, `react`, `release`, `reusability`, `robots`, `runtime-url`,
`security`, `seo`,
`sitemap`, `stack`, `state`, `structure`, `structured-data`, `swiftui`, `ui`,
`uikit`, `url`, `voice`, `widget`, `wiki`, `worktree`, and `writing`.

Use `classify` before route selection when the request may be vague or when the
agent runtime can choose model/reasoning effort. The classifier is intentionally
cheap: it suggests `clear-exact`, `clear-scoped`, `vague-action`,
`broad-product`, or `risky-unclear`, then recommends quick, standard, deep, or
specialist effort. It is a first pass, not a replacement for repo-local
inspection.

The router infers the canonical `seo` concern from explicit public-discovery
keywords in the request, including SEO, AI search, AEO, GEO, AI Overviews, AI
Mode, `llms.txt`, sitemap, robots, canonical, Open Graph, and structured data.
Agents should still pass exact concerns when local context shows a specific
risk.
It also infers `runtime-url` from requests about environment-specific runtime
URLs, API/base URLs, API origins, callback URLs, `redirect_uri`, webhook
endpoints, CORS origins, asset hosts, and CDN origins.

If the workflow router cannot run, the agent must stop and report the blocker or
ask whether to continue with an `index.md` fallback. The route output contains
`docs`, `gates`, `gate_ledger`, `attempt_limit`, `retry_limit`,
`retry_scope`, `notes`, and `missing`. Agents should read the listed docs in
order, use gates as the task checklist, mark each completed or failed gate with
evidence while working, and show a short gate signal after each completed or
failed gate or task step. Stop if any document is listed under `missing`.
Completion requires every required gate to be `🐱🟢 SUCCESS`. `🐱🔴 FAIL` means
blocked, failed, missed, or missing evidence and triggers missed-gate recovery:
stop finalization, return to the first missed gate only, roll back dependent
agent-made changes when safe, and run the retrospective workflow. The missed
gate gets one recovery retry; the whole route is not restarted. Do not report
any third gate state.

## Executable Evidence Gate

For stronger enforcement, agents should use the wrapper scripts that turn the
route, VibeGuard checks, git status, validation, and gate ledger into local JSON
evidence.

When an agent runtime executes these wrapper commands, resolve
`${AGENTPLAYBOOK_HOME}` to the absolute path first. Do not leave `$HOME`,
`${HOME}`, `~`, or a relative path in approval-sensitive executable commands.

Before multi-step edits:

```bash
python3 "${AGENTPLAYBOOK_HOME}/scripts/agent-preflight.py" \
  --project . \
  --rules "${AGENTPLAYBOOK_HOME}" \
  --command task \
  --request "<USER_REQUEST>" \
  --concern wiki
```

Before final report, commit, release, or handoff:

```bash
python3 "${AGENTPLAYBOOK_HOME}/scripts/agent-finish-check.py" \
  --project . \
  --rules "${AGENTPLAYBOOK_HOME}" \
  --gate "request intake=<route/classification evidence>" \
  --gate "orient=<instructions and route docs read>" \
  --gate "scope=<scope decision evidence>" \
  --gate "act=<diff or changed files evidence>" \
  --gate "verify=<commands and results>" \
  --gate "report=<final report prepared>"
```

The scripts write to `.agentplaybook/preflight.json` and
`.agentplaybook/finish.json`. That directory is local runtime evidence and
should usually be gitignored. Missing wrapper evidence or missing route gate
evidence is non-compliant even if the resulting code or docs look correct.
Human-visible gate reports use only two cat signal badges so failures are hard
to miss: `🐱🟢 SUCCESS` and `🐱🔴 FAIL`. The JSON evidence keeps the plain signal
values for automation.
When `--request-classified` is used, pass `--classification-evidence`; otherwise
request intake is treated as skipped. If route classification or stored request
text asks for Grill-Me, the finish check must receive Grill-Me protocol evidence
such as `grill-me if needed=</grilling session/output evidence>`.
Work routes require resolved-scope classification evidence such as
`clear-exact`, `clear-scoped`, `answered ... separate actionable`, or
`blockers resolved`; weak evidence such as `classified`, `done`, `clarified`,
or `no blockers` does not open work routes by itself.

If final VibeGuard is `Needs review`, the agent must report that state and pass
`--allow-vibeguard-review "<reason>"` only when the review state is acceptable.
A failed VibeGuard command, `🐱🔴 FAIL`, missing route evidence, or missing
VibeGuard output remains a blocker.

## Structure

```text
AGENTS.md         Shared entrypoint for agent runtimes
index.md          Routing map for selecting the smallest useful document set
common/           Platform-neutral engineering guidance
platforms/        Android, KMP, Flutter, iOS, web, server, and application tracks
product-patterns/ Reusable product mechanics such as auth, invite, and billing
workflows/        Repeatable agent work paths
scripts/          Executable workflow routers, preflight checks, and validators
templates/        Repo-local routing snippets
docs/             Static public site source
```

## Concrete Implementation Guides

AgentPlaybook cards should not stop at "write clean code." Platform routes now
include implementation-detail cards that tell an agent which boundary to create,
where state should live, and what evidence proves the work.

- Android Compose: `platforms/android/android-compose-ui.md` covers
  route/screen/component splits, `UiState`, architecture tracks, previews,
  package layout, and verification.
- Android module/package structure:
  `platforms/android/android-module-structure.md` covers feature modules,
  API/implementation splits, repository boundaries, build-logic conventions,
  shared core/design-system ownership, and migration strategy.
- Android ViewModel/state: `platforms/android/android-viewmodel-state.md`
  covers ViewModel contracts, `StateFlow`, one-off events, use cases,
  repositories, persistence, and coroutine tests.
- KMP/Compose Multiplatform: `platforms/kmp/kmp-architecture.md`,
  `platforms/kmp/kmp-module-structure.md`,
  `platforms/kmp/kmp-compose-ui.md`, `platforms/kmp/kmp-state-data.md`, and
  `platforms/kmp/kmp-platform-integration.md` cover shared modules, source sets,
  umbrella frameworks, `expect`/`actual`, shared Compose UI, state/data
  boundaries, adapters, target capabilities, and verification across affected
  targets.
- Flutter: `platforms/flutter/flutter-architecture.md`,
  `platforms/flutter/flutter-project-structure.md`,
  `platforms/flutter/flutter-widget-ui.md`,
  `platforms/flutter/flutter-state-data.md`, and
  `platforms/flutter/flutter-platform-integration.md` cover feature folders,
  package boundaries, widget layers, state management, repositories, platform
  channels, plugins, federated plugin splits, target capabilities, lifecycle,
  and verification across affected targets.
- iOS module/package structure: `platforms/ios/ios-module-structure.md` covers
  targets, local Swift packages, access control, feature contracts, app
  extensions, package layout, and migration strategy.
- iOS SwiftUI: `platforms/ios/ios-swiftui-ui.md` covers route/coordinator,
  screen/section/view splits, ViewModel contracts, `UiState`, clean
  architecture, previews, navigation effects, and tests.
- iOS UIKit: `platforms/ios/ios-uikit-ui.md` covers coordinators, view
  controllers, ViewModels/presenters, typed UI state, lists, forms, navigation,
  and XCUITest/snapshot boundaries.
- Web React: `platforms/web/web-react-ui.md` covers route/page,
  container/screen splits, hooks, typed `UiState`, query/mutation boundaries,
  clean architecture, reusable components, and tests.
- Server API: `platforms/server/server-api-implementation.md` covers handlers,
  validators, use cases, repositories, response/error shapes, tenant filters,
  idempotency, and API tests.
- Desktop/application: `platforms/application/application-command-ui.md` covers
  command routing, windows/panels, shortcuts, menu bar/tray entry points, IPC,
  background work, and OS resource cleanup.
- Shared reuse: `common/reusable-code-design.md` covers when code should stay
  local, move into feature common, become a design-system primitive, or become a
  shared package/API.
- Shared structure/state/errors: `common/code-structure-ownership.md`,
  `common/component-api-design.md`, `common/state-modeling.md`, and
  `common/error-modeling.md` cover module ownership, component contracts, typed
  state, effects, retries, and user-visible failure states.
- Product implementation: product-pattern implementation cards cover concrete
  auth/RBAC, invitation, and billing/entitlement models, state machines,
  enforcement layers, side effects, and tests.
- Human-authored writing: `common/human-authored-writing.md` covers preserving
  meaning and voice while reducing generic AI-writing signals in prose,
  documentation, release notes, marketing copy, and email.

For implementation work, route with the platform and concern instead of relying
on only a broad architecture card:

```bash
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route feature --request "<USER_REQUEST>" --platform ios --concern swiftui
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route feature --request "<USER_REQUEST>" --platform ios --concern uikit
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route feature --request "<USER_REQUEST>" --platform web --concern react --concern ui
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route feature --request "<USER_REQUEST>" --platform android --concern compose
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route feature --request "<USER_REQUEST>" --platform kmp --concern compose --concern platform
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route feature --request "<USER_REQUEST>" --platform flutter --concern widget --concern channel
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route feature --request "<USER_REQUEST>" --platform server --concern api --concern auth
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route feature --request "<USER_REQUEST>" --platform application --concern desktop
```

## Loading Model

1. Start from the target repo's local instructions.
2. Open this repository's `AGENTS.md`.
3. For multi-step work, run `scripts/workflow.py route ... --request
   "<USER_REQUEST>"` to generate the command route before selecting task
   documents.
4. Use `index.md` to choose the smallest relevant document set.
5. Read the common baseline cards required for the task.
6. Add exactly the platform, product-pattern, or workflow cards that match the
   touched surface.
7. Stop loading once the agent can identify ownership boundaries, risk, and
   verification.

This is the core design: small cards, loaded only when relevant.

## Core Rules

- Repo-local instructions always win.
- `AGENTS.md` is the shared entrypoint for agent runtimes.
- Use `index.md` to choose only the needed documents.
- Answer direct user questions before starting workflow routing, editing, or
  project-specific commands.
- Run `scripts/workflow.py route ... --request "<USER_REQUEST>"` for multi-step
  workflows before selecting documents manually.
- Use `scripts/agent-preflight.py` and `scripts/agent-finish-check.py` when
  available; missing executable evidence is non-compliant.
- Classify unclear requests before loading broad context or using deep model
  effort.
- Discover the repo stack before choosing package managers, framework APIs, or
  project commands.
- Diagnose command failures from stdout/stderr before retrying or changing code.
- Start most coding work from `common/agent-operating-skill.md`.
- Use `workflows/agent-task-lifecycle.md` for multi-step agent work of any kind.
- Use `workflows/request-triage.md` and
  `common/task-intake-effort-routing.md` when deciding whether to ask
  blocker questions, run the Grill-Me protocol, or lower/raise effort.
- Use `workflows/product-architecture-delivery.md` for product work that needs
  PRD, architecture, implementation, verification, UI tests, and commit gates.
- Use `workflows/development-cycle.md` for lower-level multi-step implementation
  work.
- Use `workflows/ambiguity-gate.md` before PRD, ARD, task breakdown, or
  implementation when unknowns could change behavior, risk, or verification.
- Use `workflows/multi-agent-collaboration.md` when delegating or parallelizing
  agent work.
- Use `workflows/multi-perspective-review.md` for non-trivial reviews and
  release candidates that need multiple risk lenses.
- A typical coding task should load `common/llm-coding-discipline.md`,
  `common/code-conventions.md`, one platform architecture card, and only
  relevant detail or concern cards.
- Naming is surface-specific: app display names can use product capitalization,
  while repos, slugs, services, and CLIs usually use lowercase `kebab-case`.
- Security, background work, release, permission, and OS integration concerns should load their detail cards explicitly.
- Keep repo paths, commands, components, role matrices, domain terms, and product-specific policy out of this library.
- Keep shared documents short, action-oriented, and reusable.
- Write shared agent guidance in English so multiple agent runtimes and repos
  can reuse it consistently.
- Public-facing site copy under `docs/` may be localized, but source guidance
  cards remain English.
- Move repeated platform-neutral rules into `common/`.
- Promote a local lesson only when project names, local paths, commands,
  service names, and platform-specific API names can be removed without losing
  the rule.
- Move reusable SaaS or product mechanics into `product-patterns/`.
- Use `workflows/` to compose common and platform cards into repeatable work paths.
- Use `scripts/` for small dependency-free Python routers that turn repeated
  workflows into command manifests for agents.

## VibeGuard Relationship

AgentPlaybook and VibeGuard stay separate.

- AgentPlaybook owns reusable agent guidance: routing, workflow gates,
  engineering cards, and platform/product patterns.
- VibeGuard owns the required safety gate and its operational UX.
- AgentPlaybook links to VibeGuard instead of documenting VibeGuard operational
  details here.
- VibeGuard should use AgentPlaybook as a rule source when applying this
  playbook to a target repo.

VibeGuard documentation:

```text
https://vibeguard.thdev.app/
```

## Language And Localization

Shared agent-facing documents in this repository are written in English. That
keeps the guidance easier for different agent runtimes and teams to parse.

Public-facing site copy under `docs/` can be localized. The site currently
supports English and Korean copy. Localized marketing or onboarding text should
not become the source of truth for agent behavior.

For a Korean quick guide to updating an existing checkout, use
`docs/ko/update-agentplaybook.md`. The canonical policy remains in this README
and the shared agent guidance.

## Metadata

Most documents use frontmatter:

```yaml
keyflow_id: sys_example
status: review
type: ai-generated
```

- Frontmatter `status` values mean `draft`, `review`, `stable`, or
  `deprecated`. Prefer `review` for active guidance and `stable` only for
  entrypoints or cards that are ready for broad reuse.
- Frontmatter `type` values describe provenance and review state:
  `ai-generated`, `human-reviewed-needed`, or `human-reviewed`. Use `status`
  for operational readiness and `type` for audit or human review queues.
- The `keyflow_id` key is retained for compatibility with older local tooling
  and document indexes. New documents should continue using it until a separate
  metadata migration is planned.

## Contributing Guidance

- Keep cards short and action-oriented.
- Prefer links over duplicated guidance.
- Add platform-neutral lessons to `common/`.
- Add LLM-readable wiki, runbook, and durable knowledge-base rules to
  `common/llm-wiki-documentation.md`.
- Add reusable product mechanics to `product-patterns/`.
- Add repeatable task paths to `workflows/`.
- Add or update `scripts/workflow.py` when a repeated workflow should be
  resolved as a command route.
- Keep repo-specific paths, commands, services, product names, and policies in
  the target repo, not in this shared library.
- When adding a public-facing page, keep agent source guidance in English and
  localize only the distribution copy.
