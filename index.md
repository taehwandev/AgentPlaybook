---
keyflow_id: sys_a0cda107d0b0
status: draft
type: ai-generated
---

# Agent Index

Pick the smallest relevant document set. Repo-local guidance wins over this shared library.

## Common

- Agent operating baseline: `common/agent-operating-skill.md`
- All coding work: `common/llm-coding-discipline.md`
- Code conventions, naming, comments, formatting: `common/code-conventions.md`
- Change size and reviewable diff scope: `common/change-size-policy.md`
- Dependencies, SDKs, packages, build plugins: `common/dependency-policy.md`
- Generated files, lockfiles, snapshots, build artifacts: `common/generated-files-policy.md`
- Architecture choice/change: `common/architecture-selection.md`
- Architecture design: `common/architecture-design.md`
- New feature or product ambiguity: `common/product-spec-to-implementation.md`
- App boundary/state/data shape: `common/app-architecture.md`
- Refactor: `common/refactoring.md`
- Testing or bug regression: `common/testing.md`
- Verification evidence: `common/verification-policy.md`
- Local tools, AI CLIs, runtime, usage telemetry: `common/local-tools.md`
- File editing safety, secrets, external state: `common/agent-editing-safety.md`
- Design system or shared UI rules: `common/design-system.md`
- Secure development, secrets, client keys, open-source-safe setup: `common/secure-development-baseline.md`
- Security/privacy/secrets/tenant risk: `common/security-privacy-review.md`
- Persistence, cache, sync, migration: `common/data-persistence-sync.md`
- Errors, logs, audit, diagnostics: `common/observability-error-handling.md`
- Code review: `common/code-review.md`
- Commit review: `common/code-review.md` + `common/commit-review.md`
- Commit creation: `common/commit-workflow.md`

## Platform

- Android architecture: `platforms/android/android-architecture.md`
- Android state/data: `platforms/android/android-state-data.md`
- Android background work: `platforms/android/android-background-work.md`
- Android security: `platforms/android/android-security.md`
- Android review: `platforms/android/android-review.md`
- iOS architecture: `platforms/ios/ios-architecture.md`
- iOS state/concurrency: `platforms/ios/ios-state-concurrency.md`
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

- Feature implementation: `workflows/feature-implementation.md`
- Review and commit: `workflows/review-and-commit.md`

## Loading Rule

For coding, read `common/agent-operating-skill.md`,
`common/llm-coding-discipline.md`, and `common/code-conventions.md` first. Then
read one platform architecture card. Add platform detail, common, or
product-pattern cards only when the task touches that concern.

For broad diffs, refactors, PR review, or commit preparation, also read
`common/change-size-policy.md`. For dependency, SDK, package, build plugin, or
lockfile work, read `common/dependency-policy.md`. For codegen, generated
clients, lockfiles, snapshots, build artifacts, translations, or generated
assets, read `common/generated-files-policy.md`.

For Android work touching background execution, release builds, exported components, deep links, WebView, permissions, or secrets, load the Android background/security cards instead of relying only on the architecture card.

For desktop/application work touching menu bar/tray controls, shell/file/clipboard APIs, power assertions, IPC, signing, notarization, updates, or first launch, load the application system/security cards.

When the task touches keys, auth, permissions, user data, logs, analytics,
external integrations, local config, release config, or a public/open-source repo,
read `common/secure-development-baseline.md` before implementation.

For React/web feature work, usually read:

```text
common/llm-coding-discipline.md
common/code-conventions.md
platforms/web/web-architecture.md
platforms/web/web-state-data.md when state/data/storage is touched
platforms/web/web-accessibility-i18n.md when UI text, forms, menus, dialogs, or localization are touched
```

For review, read `common/code-review.md` first. Then read the matching platform review card. Add `common/security-privacy-review.md` and product-pattern cards only for affected auth, invite, billing, tenancy, or security concerns.

Stop reading when you can answer:

- What is the state owner?
- What are the UI, domain, data, and platform boundaries?
- What security, permission, persistence, or billing risks exist?
- What verification proves the goal?
- Which project-specific rules live in the repo?
