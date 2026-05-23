---
keyflow_id: sys_agent_entrypoint
status: draft
type: human-reviewed-needed
---

# KeyFlow Shared Agent Instructions

This file is the entrypoint for agents that consult the shared KeyFlow agent
library.

## Purpose

Use this library to prevent repeated mistakes across repositories. It provides
shared operating habits, review criteria, architecture principles, and platform
guidance. Repo-local instructions remain the source of truth for project paths,
commands, naming, domain rules, and product-specific policy.

## Priority

When instructions conflict, follow this order:

1. System and developer instructions from the active agent runtime.
2. The user's current request.
3. The target repo's local instructions, such as `AGENTS.md`, `CLAUDE.md`,
   `CODEX.md`, `.agents/README.md`, or `CONTRIBUTING.md`.
4. More specific shared KeyFlow documents, such as platform or product-pattern
   docs.
5. Shared KeyFlow common cards.
6. General guidance in `README.md`.

If the conflict changes behavior, verification, security, or data handling,
call it out before or after the work.

## Always Read For Agent Work

For implementation, review, refactoring, debugging, documentation, or planning
tasks, first consult:

```text
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/agent-operating-skill.md
```

Then load only the supporting documents relevant to the task.

## Supporting Documents

Use `index.md` as the full document map. Common direct routes:

```text
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/llm-coding-discipline.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/code-conventions.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/change-size-policy.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/dependency-policy.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/generated-files-policy.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/architecture-selection.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/architecture-design.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/product-spec-to-implementation.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/app-architecture.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/refactoring.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/testing.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/verification-policy.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/local-tools.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/agent-editing-safety.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/design-system.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/secure-development-baseline.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/security-privacy-review.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/data-persistence-sync.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/observability-error-handling.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/code-review.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/commit-review.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/common/commit-workflow.md
```

## Platform Documents

```text
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/web/web-architecture.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/web/web-state-data.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/web/web-accessibility-i18n.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/web/web-review.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/ios/ios-architecture.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/ios/ios-state-concurrency.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/ios/ios-review.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/android/android-architecture.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/android/android-state-data.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/android/android-background-work.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/android/android-security.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/android/android-review.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/server/server-architecture.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/server/server-data-jobs.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/server/server-review.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/application/application-architecture.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/application/application-system-integration.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/application/application-security.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/platforms/application/application-review.md
```

## Product Pattern Documents

```text
/Users/taehwankwon/Documents/KeyFlowVault/agent/product-patterns/auth-rbac-permissions.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/product-patterns/invitation-workflows.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/product-patterns/billing-entitlements.md
```

## Workflow Documents

```text
/Users/taehwankwon/Documents/KeyFlowVault/agent/workflows/feature-implementation.md
/Users/taehwankwon/Documents/KeyFlowVault/agent/workflows/review-and-commit.md
```

## Operating Rule

Do not copy this whole library into a repo. Link only the documents relevant to
that repo. Keep repo-specific paths, commands, role matrices, API names, and
domain language in the repo-local instructions.
