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
AgentPlaybook. It handles deterministic setup, preflight audit, safe fixes, and
secret/cost/data-risk checks.

Website:

```text
https://agentplaybook.thdev.app/
```

## Quick Start

If AgentPlaybook already exists locally, use that copy. Point the target repo to
the existing root instead of cloning or copying another copy.

For a new local shared install, clone the playbook somewhere stable:

```bash
export AGENTPLAYBOOK_HOME="$HOME/.agent-playbook"
git clone https://github.com/taehwandev/AgentPlaybook.git "$AGENTPLAYBOOK_HOME"
```

Then add a short pointer to the target repo's `AGENTS.md`,
`AGENTS.override.md`, `CLAUDE.md`, `CODEX.md`, or equivalent local agent
instructions:

```text
Shared AgentPlaybook guidance:
${AGENTPLAYBOOK_HOME}/AGENTS.md
${AGENTPLAYBOOK_HOME}/index.md
${AGENTPLAYBOOK_HOME}/scripts/workflow.py

Use repo-local instructions first.
For multi-step tasks, use the workflow script first when it exists.
Use the shared index only to select the smallest relevant document set.
Do not load every shared document by default.
```

You can also vendor this repository as a submodule or workspace dependency if
your team wants a pinned version.

VibeGuard is required in every distribution mode:

```bash
vibe-guard setup . --rules "${AGENTPLAYBOOK_HOME}"
vibe-guard audit . --rules "${AGENTPLAYBOOK_HOME}"
```

Use an installed, repo-pinned, or team-approved VibeGuard source first. If a
local source is unavailable, use a reviewed GitHub tag or commit:

```bash
npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard#<VIBEGUARD_REF> -- vibe-guard setup . --rules "${AGENTPLAYBOOK_HOME}"
npm --no-update-notifier exec --yes --package github:taehwandev/VibeGuard#<VIBEGUARD_REF> -- vibe-guard audit . --rules "${AGENTPLAYBOOK_HOME}"
```

Run `--fix` only after audit output shows a low-risk safety fix and the target
repo allows that automatic change.

## Apply With Any AI Agent

Give an AI coding agent this request:

```text
Apply AgentPlaybook to this project:
https://github.com/taehwandev/AgentPlaybook

If AgentPlaybook already exists locally, link this repo to the existing copy.
Do not clone, vendor, or copy a second copy unless no usable local copy exists.
Run VibeGuard setup and audit with the selected AgentPlaybook root as --rules.
Use a local, repo-pinned, or reviewed VibeGuard source. Do not run an unpinned
GitHub package command in unattended automation.
Update the repo-local agent instructions with a short routing block. Keep
repo-specific commands, paths, services, product policy, and domain language in
this repo.
```

Full bootstrap instructions live in [docs/agent-bootstrap.md](docs/agent-bootstrap.md).
A shorter reusable prompt lives in
[templates/apply-agentplaybook-request.md](templates/apply-agentplaybook-request.md).

## Use With Codex, Claude, And Antigravity

AgentPlaybook is not tied to one runtime. Codex may discover `AGENTS.md`
directly, while Claude, Antigravity, or generic agents may need a repo-local
bridge file or a pasted prompt.

- For long-lived repo setup, add the routing block from
  [templates/repo-agents-routing.md](templates/repo-agents-routing.md) to the
  instruction file the runtime reads, such as `AGENTS.md`,
  `AGENTS.override.md`, `CLAUDE.md`, `CODEX.md`, or `.agents/README.md`.
- For one-shot use, paste
  [templates/use-agentplaybook-prompt.md](templates/use-agentplaybook-prompt.md)
  into the agent with the target repo, task, AgentPlaybook root, and VibeGuard
  source filled in.
- For runtime-specific setup rules, read
  [docs/agent-runtime-integration.md](docs/agent-runtime-integration.md).

## Distribution Modes

- Existing local install: preferred when the user already has AgentPlaybook.
  Link the target repo to that root and do not reinstall.
- Local shared install: clone once to `~/.agent-playbook` and reuse it across
  personal repos.
- Team-pinned install: add AgentPlaybook as a git submodule or vendored
  dependency when every teammate and agent must use the same reviewed version.

In every mode, VibeGuard is mandatory. Run VibeGuard setup/audit against the
target repo and pass the selected AgentPlaybook root as `--rules`. Prefer a
local, repo-pinned, or reviewed VibeGuard source. If VibeGuard cannot run,
report the blocker instead of bypassing the gate. The target repo keeps its own
commands, paths, services, product policy, and domain rules. AgentPlaybook
provides shared defaults only.

## Workflow Router

For multi-step work, agents can generate a route manifest before selecting
documents manually:

```bash
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" list
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route product --platform web --concern security --concern ui
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" route docs-review --concern wiki
python3 "${AGENTPLAYBOOK_HOME}/scripts/workflow.py" validate
```

Supported commands are `ambiguity`, `bugfix`, `docs`, `docs-review`, `feature`,
`multi-agent`, `planning`, `product`, `refactor`, `release`, `retrospective`,
`review`, and `task`.

Supported platforms are `android`, `application`, `ios`, `server`, and `web`.
Supported concerns are `accessibility`, `api`, `auth`, `background`, `billing`,
`cache`, `defensive`, `dependency`, `failure`, `generated`, `interaction`,
`invite`, `observability`, `persistence`, `release`, `security`, `stack`, `ui`,
`wiki`, and `worktree`.

The route output contains `docs`, `gates`, `gate_ledger`, `attempt_limit`,
`notes`, and `missing`. Agents should read the listed docs in order, use gates
as the task checklist, mark each gate with evidence while working, and stop if
any document is listed under `missing`. If a required gate is missed, the agent
must stop finalization, roll back only agent-made changes from the failed
attempt when safe, restart from the first gate, and run the retrospective
workflow. The attempt limit is two.

## Structure

```text
AGENTS.md         Shared entrypoint for agent runtimes
index.md          Routing map for selecting the smallest useful document set
common/           Platform-neutral engineering guidance
platforms/        Android, iOS, web, server, and application tracks
product-patterns/ Reusable product mechanics such as auth, invite, and billing
workflows/        Repeatable agent work paths
scripts/          Executable workflow routers and validators
templates/        Repo-local routing snippets
docs/             Static public site source
```

## Loading Model

1. Start from the target repo's local instructions.
2. Open this repository's `AGENTS.md`.
3. For multi-step work, run `scripts/workflow.py` when available to generate the
   command route.
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
- Use `scripts/workflow.py` to turn repeated multi-step workflows into command
  manifests before selecting documents manually.
- Discover the repo stack before choosing package managers, framework APIs, or
  project commands.
- Diagnose command failures from stdout/stderr before retrying or changing code.
- Start most coding work from `common/agent-operating-skill.md`.
- Use `workflows/agent-task-lifecycle.md` for multi-step agent work of any kind.
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

AgentPlaybook and VibeGuard should stay separate, but they are integrated by
policy. VibeGuard is not optional when applying AgentPlaybook.

AgentPlaybook is the reusable rule library. It answers:

- What should an AI coding agent read before editing?
- How should it route planning, implementation, review, testing, and handoff?
- Which platform or product-pattern risks should be considered?
- What guidance can be reused across many repositories?

VibeGuard is the required safety layer and CLI. It answers:

- How can a non-developer apply safety guardrails by giving an agent one link?
- What deterministic preflight checks should run before code is changed?
- Which safe fixes can be applied automatically?
- When should the agent stop before secrets, cost, data, or destructive risk?

Keeping them separate has practical benefits:

- Users can install or update the safety CLI without changing the playbook.
- Teams can pin the playbook version while still running the required
  VibeGuard gate on every target repo.
- VibeGuard can consume or summarize selected AgentPlaybook cards without
  copying the full library.
- AgentPlaybook remains general-purpose, while VibeGuard can optimize its UX for
  beginners and non-developers.

The integration model is link-based and mandatory:

- VibeGuard must reference AgentPlaybook as the configured rule source when
  applying this playbook to a repo.
- AgentPlaybook must point users to VibeGuard for installation, preflight checks,
  and safe auto-fixes.
- VibeGuard execution should use an installed, repo-pinned, team-approved, or
  reviewed package ref; unpinned package execution is not the default.
- Shared rules should live in AgentPlaybook when they are broadly reusable.
- VibeGuard-specific CLI behavior, audit output, setup flow, and beginner UX
  should live in VibeGuard.
- Do not duplicate long guidance between the two projects. Link it or promote it
  into the more general project.

Do not merge the projects while VibeGuard remains a CLI with setup, audit, fix,
localization, and beginner onboarding behavior. Separate repos keep ownership
clear while making the safety gate required.

## Language And Localization

Shared agent-facing documents in this repository are written in English. That
keeps the guidance easier for different agent runtimes and teams to parse.

Public-facing site copy under `docs/` can be localized. The site currently
supports English and Korean copy. Localized marketing or onboarding text should
not become the source of truth for agent behavior.

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
