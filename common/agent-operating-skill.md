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
2. Classify request clarity and effort before loading broad context. If the user
   asks a direct question, answer it before starting workflow routing, editing,
   or project-specific commands.
3. Read repo-local instructions before changing files.
4. Discover the project stack before choosing commands or libraries.
5. For multi-step tasks, run `scripts/workflow.py route ... --request
   "<USER_REQUEST>"` before selecting task documents, editing, reviewing,
   committing, or reporting completion.
6. Keep a gate execution ledger for the route and mark each gate with evidence
   when it is executed. Show a short gate signal after each completed gate or
   task step.
7. Use `index.md` to load only relevant AgentPlaybook cards.
8. Inspect existing code, docs, tests, and local conventions.
9. Make the smallest change that genuinely addresses the request.
10. Verify with the narrowest reliable command first.
11. Confirm the route gate ledger before reporting completion.
12. Report what changed, what was verified, and what risk remains.

## Mistake Prevention Checklist

Before editing:

- Confirm target path and project.
- Classify the request as clear-exact, clear-scoped, vague-action,
  broad-product, risky-unclear, or direct-question before choosing effort.
- If classified as direct-question, answer first and do not start work unless a
  separate actionable request remains.
- If the direct question asks how to start app, product, or feature work, answer
  with the PRD -> ARD -> implementation sequence first. Do not give an
  implementation-only workflow for product delivery.
- Check repo-local `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`,
  `CODEX.md`, `.agents/README.md`, `CONTRIBUTING.md`, or equivalent docs.
- Check stack manifests, lockfiles, and config before running commands, adding
  dependencies, or using framework-specific APIs.
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

- Confirm every required workflow route gate has ledger evidence when a scripted
  route was used.
- Run the most relevant test, build, typecheck, lint, or smoke check.
- If verification cannot run, state why and what risk remains.
- Include file references when explaining non-trivial changes.

## Task Routing

- Request clarity, question drill, model/effort routing, or token reduction:
  `common/task-intake-effort-routing.md` and `workflows/request-triage.md`.
- Scripted workflow route: `workflows/scripted-agent-workflow.md` and
  `scripts/workflow.py` are mandatory for multi-step tasks when the script is
  available. Pass `--request "<USER_REQUEST>"` so the script can block direct
  questions and unclear work before implementation. If the script cannot run,
  report the blocker before using `index.md` as a fallback.
- Stack, package manager, framework, runtime, or command discovery:
  `common/stack-discovery.md`.
- Failed commands, compiler errors, lint errors, or broken verification:
  `common/tool-failure-recovery.md`.
- User questions, approval requests, and ambiguity communication:
  `common/agent-interaction.md`.
- Any multi-step agent task: `workflows/agent-task-lifecycle.md`.
- Interrupted or transferred work: `workflows/agent-handoff-continuation.md`.
- Ambiguous requests or blocker unknowns before PRD, ARD, task breakdown, or
  implementation: `workflows/ambiguity-gate.md`.
- PRD or product requirements note: `workflows/prd-creation.md`.
- App, product, or feature delivery that may continue into code:
  `workflows/product-architecture-delivery.md`. Use this before the lower-level
  feature workflow unless the request is already a trivial, scoped change.
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
- File/module layout, ownership, public contracts, or `api`/`impl` splits:
  `common/code-structure-ownership.md`.
- Reusable code extraction or shared module/package contracts:
  `common/reusable-code-design.md`.
- Reusable component, hook, widget, control, or caller-facing API design:
  `common/component-api-design.md`.
- UI, async, reducer, store, ViewModel, hook, cache, or state-machine state
  design: `common/state-modeling.md`.
- Error handling, typed failures, retry classification, or failure UX:
  `common/error-modeling.md`.
- Project, app, repo, package, module, CLI, or service naming:
  `common/project-naming.md`.
- Change size or broad diffs: `common/change-size-policy.md`.
- Existing checkout, user-owned changes, or commit preparation:
  `common/worktree-hygiene.md`.
- Dependencies, SDKs, or build plugins: `common/dependency-policy.md`.
- Generated files, lockfiles, or snapshots: `common/generated-files-policy.md`.
- API, DTO, route, event, webhook, or shared fixture contracts:
  `common/api-contract-compatibility.md`.
- Upload, download, media, attachment, signed URL, public/private asset
  movement, cleanup, or embedded asset references:
  `common/asset-lifecycle.md`.
- External, persisted, generated, cached, platform, or user-provided values:
  `common/defensive-boundaries.md`.
- Release, deployment, packaging, signing, rollout, rollback, versioning, or
  tags: `common/release-deployment.md` and `common/release-versioning.md`.
- User-facing text, forms, controls, dates, numbers, or localization:
  `common/accessibility-i18n.md`.
- User-facing prose, documentation tone, release notes, marketing copy, emails,
  voice fidelity, or AI-writing signal cleanup:
  `common/human-authored-writing.md`.
- SEO, AI search visibility, AEO/GEO claims, sitemap, robots, metadata, Open
  Graph, short links, canonical URLs, or public discovery feeds:
  `common/public-discovery.md`.
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
