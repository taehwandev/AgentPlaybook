---
keyflow_id: sys_agent_operating_skill
status: review
type: human-reviewed-needed
---

# Agent Operating Skill

Use this before implementation, review, refactoring, debugging, documentation,
or verification work. This is the baseline skill for reducing repeated agent
mistakes.

## Core Loop

1. Identify the target project and task type.
2. Read repo-local instructions before changing files.
3. For multi-step tasks, use `scripts/workflow.py` when available to generate
   the workflow route.
4. Use `index.md` to load only relevant AgentPlaybook cards.
5. Inspect existing code, docs, tests, and local conventions.
6. Make the smallest change that genuinely addresses the request.
7. Verify with the narrowest reliable command first.
8. Report what changed, what was verified, and what risk remains.

## Mistake Prevention Checklist

Before editing:

- Confirm target path and project.
- Check repo-local `AGENTS.md`, `CLAUDE.md`, `CODEX.md`,
  `.agents/README.md`, `CONTRIBUTING.md`, or equivalent docs.
- Check whether the task touches data, auth, permissions, billing,
  persistence, filesystem, network, release, or external state.
- Check whether the task touches secrets, client keys, local config, logs,
  analytics, crash reporting, or open-source-safe setup.
- Check for existing user changes in files you may touch.

While editing:

- Follow existing architecture and naming before inventing a new pattern.
- Keep unrelated refactors out of feature or bug-fix work.
- Preserve user-owned changes.
- Do not expose secrets, tokens, private prompts, or credential contents.
- Do not claim mocked, placeholder, or TODO behavior is complete.

Before finishing:

- Run the most relevant test, build, typecheck, lint, or smoke check.
- If verification cannot run, state why and what risk remains.
- Include file references when explaining non-trivial changes.

## Task Routing

- Scripted workflow route: `workflows/scripted-agent-workflow.md` and
  `scripts/workflow.py` when the task has multiple steps.
- Any multi-step agent task: `workflows/agent-task-lifecycle.md`.
- Interrupted or transferred work: `workflows/agent-handoff-continuation.md`.
- Ambiguous requests or blocker unknowns before PRD, ARD, task breakdown, or
  implementation: `workflows/ambiguity-gate.md`.
- Multi-step development: `workflows/development-cycle.md`.
- Delegated or parallel agent work: `workflows/multi-agent-collaboration.md`.
- Non-trivial review or release candidate review:
  `workflows/multi-perspective-review.md`.
- Planning or research: `workflows/planning-research.md`.
- Documentation update: `workflows/documentation-update.md`.
- Feature work: `workflows/feature-implementation.md`.
- Bug or regression: `workflows/bugfix-debugging.md`.
- Refactor or cleanup: `workflows/refactor-cleanup.md`.
- Release-sensitive work: `workflows/release-readiness.md`.
- Final review or commit: `workflows/review-and-commit.md`.
- Architecture: `common/architecture-selection.md`,
  `common/architecture-design.md`, or `common/app-architecture.md`.
- LLM-readable wiki, knowledge-base, runbook, or durable documentation:
  `common/llm-wiki-documentation.md`.
- Code conventions: `common/code-conventions.md`.
- Project, app, repo, package, module, CLI, or service naming:
  `common/project-naming.md`.
- Change size or broad diffs: `common/change-size-policy.md`.
- Existing checkout, user-owned changes, or commit preparation:
  `common/worktree-hygiene.md`.
- Dependencies, SDKs, or build plugins: `common/dependency-policy.md`.
- Generated files, lockfiles, or snapshots: `common/generated-files-policy.md`.
- API, DTO, route, event, webhook, or shared fixture contracts:
  `common/api-contract-compatibility.md`.
- External, persisted, generated, cached, platform, or user-provided values:
  `common/defensive-boundaries.md`.
- Release, deployment, packaging, signing, rollout, or rollback:
  `common/release-deployment.md`.
- User-facing text, forms, controls, dates, numbers, or localization:
  `common/accessibility-i18n.md`.
- UI layout, interaction, text overflow, responsive behavior, or
  accessibility-visible state: `common/ui-visual-verification.md`.
- Refactoring: `common/refactoring.md`.
- Tests and evidence: `common/testing.md` and
  `common/verification-policy.md`.
- Code review: `common/code-review.md`.
- Local programs, agent CLIs, or usage telemetry: `common/local-tools.md`.
- Secrets, external state, or user-owned changes:
  `common/agent-editing-safety.md`, `common/secure-development-baseline.md`,
  and `common/security-privacy-review.md`.
- React, iOS, Android, server, desktop, or application work: load the matching
  platform card from `index.md`.

## Output Contract

Use short evidence-based reporting:

```text
Changed:
- ...

Verified:
- ...

Remaining risk:
- ...
```

For small tasks, a concise paragraph is enough, but verification status still
matters.
