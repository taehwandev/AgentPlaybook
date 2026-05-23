---
keyflow_id: sys_a0cda107d0b0
status: stable
type: ai-generated
---

# Agent Index

Pick the smallest relevant document set. Repo-local guidance wins over this shared library.

## Common

- Agent operating baseline: `common/agent-operating-skill.md`
- User questions, approvals, status updates, and handoff messages:
  `common/agent-interaction.md`
- All coding work: `common/llm-coding-discipline.md`
- Code conventions, naming, comments, formatting: `common/code-conventions.md`
- Stack, package manager, framework, runtime, and command discovery:
  `common/stack-discovery.md`
- Project, app, repo, package, module, CLI, and service naming: `common/project-naming.md`
- Change size and reviewable diff scope: `common/change-size-policy.md`
- Existing checkout and user-owned diff safety: `common/worktree-hygiene.md`
- Dependencies, SDKs, packages, build plugins: `common/dependency-policy.md`
- Generated files, lockfiles, snapshots, build artifacts: `common/generated-files-policy.md`
- API, DTO, route, event, webhook contract compatibility: `common/api-contract-compatibility.md`
- Defensive handling for external, persisted, generated, cached, or user-provided
  values: `common/defensive-boundaries.md`
- Release, deployment, packaging, rollback: `common/release-deployment.md`
- Release version, tag, artifact, build number, and deployment id scheme:
  `common/release-versioning.md`
- Accessibility, localization, dates, numbers, UI text: `common/accessibility-i18n.md`
- Architecture choice/change: `common/architecture-selection.md`
- Architecture design: `common/architecture-design.md`
- New feature or product ambiguity: `common/product-spec-to-implementation.md`
- LLM-readable wiki, knowledge-base, runbook, or durable documentation:
  `common/llm-wiki-documentation.md`
- App boundary/state/data shape: `common/app-architecture.md`
- Refactor: `common/refactoring.md`
- Testing or bug regression: `common/testing.md`
- Verification evidence: `common/verification-policy.md`
- Tool, compiler, lint, test, and command failure recovery:
  `common/tool-failure-recovery.md`
- Local tools, AI CLIs, runtime, usage telemetry: `common/local-tools.md`
- File editing safety, secrets, external state: `common/agent-editing-safety.md`
- Design system or shared UI rules: `common/design-system.md`
- UI visual and interaction verification: `common/ui-visual-verification.md`
- Secure development, secrets, client keys, open-source-safe setup: `common/secure-development-baseline.md`
- Security/privacy/secrets/tenant risk: `common/security-privacy-review.md`
- Persistence, cache, sync, migration: `common/data-persistence-sync.md`
- Server-rendered/API/edge/database caching and invalidation: `common/server-side-caching.md`
- Errors, logs, audit, diagnostics: `common/observability-error-handling.md`
- Code review: `common/code-review.md`
- Commit review: start with code review, then add `common/commit-review.md`
- Commit creation: `common/commit-workflow.md`

## Platform

- Android architecture: `platforms/android/android-architecture.md`
- Android state/data: `platforms/android/android-state-data.md`
- Android background work: `platforms/android/android-background-work.md`
- Android security: `platforms/android/android-security.md`
- Android review: `platforms/android/android-review.md`
- iOS architecture: `platforms/ios/ios-architecture.md`
- iOS state/concurrency: `platforms/ios/ios-state-concurrency.md`
- iOS security: `platforms/ios/ios-security.md`
- iOS review: `platforms/ios/ios-review.md`
- Web/React architecture: `platforms/web/web-architecture.md`
- Web/React state/data: `platforms/web/web-state-data.md`
- Web accessibility/i18n: `platforms/web/web-accessibility-i18n.md`
- Web review: `platforms/web/web-review.md`
- Server architecture: `platforms/server/server-architecture.md`
- Server data/jobs: `platforms/server/server-data-jobs.md`
- Server review: `platforms/server/server-review.md`
- Application architecture: `platforms/application/application-architecture.md`
- Application system integration: `platforms/application/application-system-integration.md`
- Application security: `platforms/application/application-security.md`
- Application review: `platforms/application/application-review.md`

## Product Pattern

- Auth/RBAC/permissions: `product-patterns/auth-rbac-permissions.md`
- Invitation flows: `product-patterns/invitation-workflows.md`
- Billing/entitlements/quota: `product-patterns/billing-entitlements.md`

## Workflow

- Workflow script command list:
  `python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py list`
- Agent task lifecycle: `workflows/agent-task-lifecycle.md`
- Agent handoff/continuation: `workflows/agent-handoff-continuation.md`
- Scripted workflow routing: `workflows/scripted-agent-workflow.md`
- Ambiguity gate: `workflows/ambiguity-gate.md`
- PRD creation: `workflows/prd-creation.md`
- Product architecture delivery: `workflows/product-architecture-delivery.md`
- Development cycle: `workflows/development-cycle.md`
- Multi-agent collaboration: `workflows/multi-agent-collaboration.md`
- Multi-perspective review: `workflows/multi-perspective-review.md`
- Retrospective learning: `workflows/retrospective-learning.md`
- Planning/research: `workflows/planning-research.md`
- Documentation update: `workflows/documentation-update.md`
- Feature implementation: `workflows/feature-implementation.md`
- Bugfix/debugging: `workflows/bugfix-debugging.md`
- Refactor cleanup: `workflows/refactor-cleanup.md`
- Release readiness: `workflows/release-readiness.md`
- Review and commit: `workflows/review-and-commit.md`

## Loading Rule

For any multi-step agent task, start with `workflows/agent-task-lifecycle.md`.
When `scripts/workflow.py` is available, use it to generate the command route
before manually selecting workflow documents. Treat the route's gate ledger as a
required execution record, not a summary to reconstruct after the work. Show a
short gate signal after each completed gate or task step.

Before running project commands, adding dependencies, or using framework-specific
APIs, use `common/stack-discovery.md`. When a command fails, use
`common/tool-failure-recovery.md` before retrying or changing code. When the
agent needs to ask a blocker question or approval, use
`common/agent-interaction.md`.

For PRD-only work, use `workflows/prd-creation.md` and prefer this scripted
route:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route prd --platform <platform> --concern <concern>
```

For product or feature work that needs PRD -> ARD -> implementation ->
verification gates, use `workflows/product-architecture-delivery.md` and prefer
this scripted route:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route product --platform <platform> --concern <concern>
```

For lower-level multi-step development work, continue with
`workflows/development-cycle.md`. For vague or risky requests, use
`workflows/ambiguity-gate.md` before PRD, ARD, task breakdown, or
implementation. After a task, incident, handoff, repeated mistake, or missed
signal, use `workflows/retrospective-learning.md` only when there is a reusable
lesson. For coding, read
`common/agent-operating-skill.md`, `common/llm-coding-discipline.md`, and
`common/code-conventions.md` first. Then read one platform architecture card.
Add platform detail, common, or product-pattern cards only when the task touches
that concern.

For documentation-only work, use `workflows/documentation-update.md`. For wiki,
knowledge-base, runbook, onboarding, durable architecture, or operational docs
that humans and agents will read, also use `common/llm-wiki-documentation.md`.
For documentation review, use
`python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route docs-review --concern wiki`
or manually combine `workflows/review-and-commit.md`,
`workflows/documentation-update.md`, and `common/llm-wiki-documentation.md`.
For planning, research, comparison, or recommendations before implementation,
use `workflows/planning-research.md`. For interrupted, long-running, or
transferred work, use `workflows/agent-handoff-continuation.md`.

For delegated or parallel agent work, use
`workflows/multi-agent-collaboration.md`. For non-trivial reviews, release
candidates, or changes that need product, UX, architecture, reliability,
security, and QA lenses, use `workflows/multi-perspective-review.md`.

For new project scaffolds, app names, repo names, package ids, modules, CLIs,
services, slugs, bundle ids, or renames, read `common/project-naming.md`.

For broad diffs, refactors, PR review, or commit preparation, also read
`common/change-size-policy.md`. When the worktree already contains changes or
the task includes commit preparation, also read `common/worktree-hygiene.md`.
For dependency, SDK, package, build plugin, or lockfile work, read
`common/dependency-policy.md`. For codegen, generated clients, lockfiles,
snapshots, build artifacts, translations, or generated assets, read
`common/generated-files-policy.md`.

For API, DTO, route, event, webhook, shared fixture, or generated client
changes, read `common/api-contract-compatibility.md`. For packaging,
deployment, publishing, signing, migration rollout, or rollback-sensitive work,
read `common/release-deployment.md`. For release version, package version, app
version, build number, tag, artifact name, or deployment id changes, also read
`common/release-versioning.md`. For user-facing text, forms, controls, dates,
numbers, media, or localization, read `common/accessibility-i18n.md`.

For code that consumes external, persisted, generated, cached, platform, or
user-provided values, read `common/defensive-boundaries.md`.

For UI layout, visible state, interaction, text overflow, responsive behavior,
or accessibility-visible changes, read `common/ui-visual-verification.md`.

For server-rendered data, API response caching, framework data cache,
request-level memoization, edge/CDN cache, database query cache, materialized
read models, or cache invalidation, read `common/server-side-caching.md`.

For Android work touching background execution, release builds, exported
components, deep links, WebView, permissions, or secrets, load the Android
background/security cards instead of relying only on the architecture card.

For iOS work touching Keychain, Universal Links, URL schemes, app extensions,
WebViews, permissions, entitlements, signing, release builds, or secrets, load
the iOS security card instead of relying only on the architecture card.

For desktop/application work touching menu bar/tray controls, shell, file,
clipboard APIs, power assertions, IPC, signing, notarization, updates, or first
launch, load the application system/security cards.

When the task touches keys, auth, permissions, user data, logs, analytics,
external integrations, local config, release config, or a public/open-source
repo, read `common/secure-development-baseline.md` before implementation.

For React/web feature work, usually read:

```text
common/llm-coding-discipline.md
common/code-conventions.md
platforms/web/web-architecture.md
platforms/web/web-state-data.md when state/data/storage is touched
platforms/web/web-accessibility-i18n.md when UI text, forms, menus, dialogs,
or localization are touched
```

For review, read `common/code-review.md` first. Then read the matching platform
review card. Add `common/security-privacy-review.md` and product-pattern cards
only for affected auth, invite, billing, tenancy, or security concerns.

Stop reading when you can answer:

- What is the state owner?
- What are the UI, domain, data, and platform boundaries?
- What security, permission, persistence, or billing risks exist?
- What verification proves the goal?
- Which project-specific rules live in the repo?
