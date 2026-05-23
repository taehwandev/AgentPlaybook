---
keyflow_id: sys_agent_entrypoint
status: stable
type: human-reviewed
---

# AgentPlaybook Shared Agent Instructions

This file is the entrypoint for agents that consult the shared AgentPlaybook library.

## Purpose

Use this library to prevent repeated mistakes across repositories. It provides
shared operating habits, review criteria, architecture principles, and platform
guidance. Repo-local instructions remain the source of truth for project paths,
commands, naming, domain rules, and product-specific policy.

## Language Policy

Write shared agent library documents in English. This includes `AGENTS.md`,
`index.md`, `common/`, `platforms/`, `product-patterns/`, `workflows/`, and
`templates/`. Public-facing site copy under `docs/` may be localized, but it
must not become the source of truth for agent guidance.

## Metadata Policy

Use frontmatter `status` as the readiness signal and `type` as provenance or
review state. Do not ignore a document only because `type` is `ai-generated`
when `status` is `review` or `stable`; instead, treat `draft` as provisional,
`review` as active, and `stable` as broad-use guidance. The `keyflow_id` field
is retained for metadata compatibility and should not be renamed casually.

## Priority

When instructions conflict, follow this order:

1. System and developer instructions from the active agent runtime.
2. The user's current request.
3. The target repo's local instructions, such as `AGENTS.md`,
   `AGENTS.override.md`, `CLAUDE.md`, `CODEX.md`, `.agents/README.md`, or
   `CONTRIBUTING.md`.
4. More specific shared AgentPlaybook documents, such as platform or product-pattern docs.
5. Shared AgentPlaybook common cards.
6. General guidance in `README.md`.

If the conflict changes behavior, verification, security, or data handling, call
it out before or after the work.

## Always Read For Agent Work

For implementation, review, refactoring, debugging, documentation, or planning tasks, first consult:

```text
<AGENTPLAYBOOK_ROOT>/common/agent-operating-skill.md
```

Then load only the supporting documents relevant to the task.

## Required VibeGuard Gate

VibeGuard is mandatory for AgentPlaybook maintenance and for repos that apply
AgentPlaybook. Before documentation, code, configuration, dependency, data,
deployment, or credential changes, run the VibeGuard audit for the target repo.
When applying AgentPlaybook to another repo, do not run VibeGuard `setup` or
`update` blindly; use the application drill in `docs/agent-bootstrap.md` when
the target already has agent instructions or guardrails. Use `update` only when
the user explicitly chooses to refresh an existing managed VibeGuard block;
otherwise run audit with the current guardrails.
For this repo, use the current VibeGuard package flow documented in
`VIBEGUARD.md`. During local maintenance, prefer the official package command:

```text
npx --yes @taehwandev/vibeguard audit . --rules .
```

An installed binary is equivalent when the environment provides one:

```text
vibeguard audit . --rules .
```

When actively developing or validating a local VibeGuard checkout, this fallback
is acceptable:

```text
node <VIBEGUARD_ROOT>/src/cli.js audit . --rules .
```

Run it again before finishing. Use `--fix` only for low-risk safety fixes, and
never print detected secret values. If VibeGuard cannot run, stop and report
the blocker instead of treating it as optional.

## Required Workflow Script

For every multi-step task, run the shared workflow router before selecting
documents manually, editing, reviewing, committing, or reporting completion:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route <command> --request "<USER_REQUEST>" [--platform <platform>] [--concern <concern>]
```

Use the script output as a document and gate manifest, then execute the task with
the target repo's local commands. The route command must receive the current
user request or `--request-classified` after the request was already classified
or answered. If the request is a direct question, answer it before editing,
routing, or running project-specific work. If the script is unavailable, cannot
run, or the route is missing a clearly relevant concern, stop and report the gap
before continuing. Use `index.md` as a fallback only for simple answer-only work
or after the user explicitly accepts the fallback.
Discover valid commands, platforms, and concerns with:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py list
```

The route output contains `request_classification`, `docs`, `gates`,
`gate_ledger`, `attempt_limit`, `retry_scope`, `notes`, and `missing`. Read
listed documents in order, follow the gates as the task checklist, keep the gate
ledger current while working, show a short traffic-light gate signal after each
completed gate or task step, and stop if `missing` is not empty. Completion
requires every required gate to be `GREEN`. If a required gate is missed, follow
the missed gate recovery rule instead of finalizing. See
`workflows/scripted-agent-workflow.md` for the full consumption rules.

## Supporting Documents

Use `index.md` as the full document map. Do not duplicate the full index in
repo-local instructions. Start with these direct routes, then load only the
specific cards selected by `index.md`.

Release, versioning, platform, product-pattern, and other task-specific cards
are intentionally selected through `index.md` or `scripts/workflow.py` instead
of being listed as baseline direct routes here.

```text
<AGENTPLAYBOOK_ROOT>/index.md
<AGENTPLAYBOOK_ROOT>/common/stack-discovery.md
<AGENTPLAYBOOK_ROOT>/common/llm-coding-discipline.md
<AGENTPLAYBOOK_ROOT>/common/code-conventions.md
<AGENTPLAYBOOK_ROOT>/common/tool-failure-recovery.md
<AGENTPLAYBOOK_ROOT>/common/agent-interaction.md
<AGENTPLAYBOOK_ROOT>/common/agent-editing-safety.md
```

## Workflow Documents

```text
<AGENTPLAYBOOK_ROOT>/workflows/agent-task-lifecycle.md
<AGENTPLAYBOOK_ROOT>/workflows/agent-handoff-continuation.md
<AGENTPLAYBOOK_ROOT>/workflows/scripted-agent-workflow.md
<AGENTPLAYBOOK_ROOT>/workflows/ambiguity-gate.md
<AGENTPLAYBOOK_ROOT>/workflows/product-architecture-delivery.md
<AGENTPLAYBOOK_ROOT>/workflows/development-cycle.md
<AGENTPLAYBOOK_ROOT>/workflows/multi-agent-collaboration.md
<AGENTPLAYBOOK_ROOT>/workflows/multi-perspective-review.md
<AGENTPLAYBOOK_ROOT>/workflows/retrospective-learning.md
<AGENTPLAYBOOK_ROOT>/workflows/planning-research.md
<AGENTPLAYBOOK_ROOT>/workflows/documentation-update.md
<AGENTPLAYBOOK_ROOT>/workflows/feature-implementation.md
<AGENTPLAYBOOK_ROOT>/workflows/bugfix-debugging.md
<AGENTPLAYBOOK_ROOT>/workflows/refactor-cleanup.md
<AGENTPLAYBOOK_ROOT>/workflows/release-readiness.md
<AGENTPLAYBOOK_ROOT>/workflows/review-and-commit.md
```

## Operating Rule

Do not copy this whole library into a repo. Link only the documents relevant to
that repo. Keep repo-specific paths, commands, role matrices, API names, and
domain language in the repo-local instructions.

When applying AgentPlaybook to another repo, reuse an existing usable local or
repo-pinned AgentPlaybook root by default. Do not download, clone, vendor, copy,
overwrite, or add a second root while one exists unless the user explicitly
approves after being told the found path.

When adding AgentPlaybook routing to a target repo, keep `AGENTS.md` as the
canonical instruction file when that runtime reads it. If existing
runtime-specific files such as `CLAUDE.md`, `CODEX.md`, `.agents/README.md`, or
Antigravity CLI docs are present, update their AgentPlaybook pointer in the same
pass or point them back to `AGENTS.md`; do not create extra runtime-specific
files only for duplication.

`<AGENTPLAYBOOK_ROOT>` means the directory containing this shared library. In a
repo-local template, replace it with an existing local install path,
`${AGENTPLAYBOOK_HOME}`, or a repo-pinned submodule path. `${KEYFLOW_AGENT_ROOT}`
is accepted only as a legacy local alias when already configured.
