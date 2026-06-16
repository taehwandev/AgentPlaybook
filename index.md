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
- Request clarity, model/effort routing, token controls, question drill:
  `common/task-intake-effort-routing.md`
- All coding work: `common/llm-coding-discipline.md`
- Code conventions, naming, comments, formatting: `common/code-conventions.md`
- SOLID design principles, ISP contract/module splits, dependency inversion,
  and DDD/domain-modeling fit: `common/solid-design-principles.md`
- Code structure, file/module ownership, api/impl split:
  `common/code-structure-ownership.md`
- Reusable code design, extraction, shared module/package contracts:
  `common/reusable-code-design.md`
- Component API design, reusable view/hook/widget contracts:
  `common/component-api-design.md`
- Stack, package manager, framework, runtime, and command discovery:
  `common/stack-discovery.md`
- Project, app, repo, package, module, CLI, and service naming: `common/project-naming.md`
- Change size and reviewable diff scope: `common/change-size-policy.md`
- Existing checkout and user-owned diff safety: `common/worktree-hygiene.md`
- Dependencies, SDKs, packages, build plugins: `common/dependency-policy.md`
- Generated files, lockfiles, snapshots, build artifacts: `common/generated-files-policy.md`
- API, DTO, route, event, webhook contract compatibility: `common/api-contract-compatibility.md`
- Asset upload, URL, publish, cleanup, and embedded reference lifecycle:
  `common/asset-lifecycle.md`
- Defensive handling for external, persisted, generated, cached, or user-provided
  values: `common/defensive-boundaries.md`
- Environment-specific runtime URL configuration, callback URLs, CORS origins,
  webhook endpoints, API origins, and asset hosts:
  `common/runtime-url-configuration.md`
- Release, deployment, packaging, rollback: `common/release-deployment.md`
- Release version, tag, artifact, build number, and deployment id scheme:
  `common/release-versioning.md`
- Accessibility, localization, dates, numbers, UI text: `common/accessibility-i18n.md`
- Human-authored prose, voice fidelity, and AI-writing signal cleanup:
  `common/human-authored-writing.md`
- Architecture choice/change: `common/architecture-selection.md`
- Architecture design: `common/architecture-design.md`
- New feature or product ambiguity: `common/product-spec-to-implementation.md`
- LLM-readable wiki, knowledge-base, runbook, or durable documentation:
  `common/llm-wiki-documentation.md`
- Public discovery, SEO, AI search visibility, sitemap, metadata, previews, and
  canonical URLs:
  `common/public-discovery.md`
- App boundary/state/data shape: `common/app-architecture.md`
- State modeling, UiState, effects, reducers, stores, ViewModels, hooks:
  `common/state-modeling.md`
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
- Error modeling, typed failures, retryability, user-visible failure states:
  `common/error-modeling.md`
- Code review: `common/code-review.md`
- Commit review: start with code review, then add `common/commit-review.md`
- Commit creation: `common/commit-workflow.md`

## Platform

- Android architecture: `platforms/android/android-architecture.md`
- Android module/package structure:
  `platforms/android/android-module-structure.md`
- Android external skill source coverage and no-omission manifest:
  `platforms/android/android-external-skill-source-coverage.md`
- Android ViewModel, UiState, Flow, repository, persistence, one-off events:
  `platforms/android/android-viewmodel-state.md`
- Android Compose UI structure, stateful/stateless split, previews, packages:
  `platforms/android/android-compose-ui.md`
- Android state/data: `platforms/android/android-state-data.md`
- Android background work: `platforms/android/android-background-work.md`
- Android security: `platforms/android/android-security.md`
- Android review: `platforms/android/android-review.md`
- KMP architecture: `platforms/kmp/kmp-architecture.md`
- KMP module/source-set structure:
  `platforms/kmp/kmp-module-structure.md`
- KMP Compose Multiplatform UI: `platforms/kmp/kmp-compose-ui.md`
- KMP state/data: `platforms/kmp/kmp-state-data.md`
- KMP platform integration: `platforms/kmp/kmp-platform-integration.md`
- KMP security: `platforms/kmp/kmp-security.md`
- KMP review: `platforms/kmp/kmp-review.md`
- Flutter architecture: `platforms/flutter/flutter-architecture.md`
- Flutter project/package structure:
  `platforms/flutter/flutter-project-structure.md`
- Flutter widget UI: `platforms/flutter/flutter-widget-ui.md`
- Flutter state/data: `platforms/flutter/flutter-state-data.md`
- Flutter platform integration: `platforms/flutter/flutter-platform-integration.md`
- Flutter security: `platforms/flutter/flutter-security.md`
- Flutter review: `platforms/flutter/flutter-review.md`
- Swift architecture: `platforms/swift/swift-architecture.md`
- Swift package/target/file structure:
  `platforms/swift/swift-code-structure.md`
- Swift design system, tokens, primitives, component variants, and previews:
  `platforms/swift/swift-design-system.md`
- Swift review: `platforms/swift/swift-review.md`
- iOS architecture: `platforms/ios/ios-architecture.md`
- iOS target/package structure:
  `platforms/ios/ios-module-structure.md`
- iOS SwiftUI UI structure, ViewModel contracts, UiState, previews, packages:
  `platforms/ios/ios-swiftui-ui.md`
- iOS UIKit UI structure, coordinators, view controllers, lists, forms:
  `platforms/ios/ios-uikit-ui.md`
- iOS state/concurrency: `platforms/ios/ios-state-concurrency.md`
- iOS security: `platforms/ios/ios-security.md`
- iOS review: `platforms/ios/ios-review.md`
- Web/React architecture: `platforms/web/web-architecture.md`
- Web file/feature structure and import boundaries:
  `platforms/web/web-code-structure.md`
- Web/React UI implementation, container/screen split, hooks, UiState:
  `platforms/web/web-react-ui.md`
- Web/React state/data: `platforms/web/web-state-data.md`
- Web design system, tokens, primitives, component variants, and styling:
  `platforms/web/web-design-system.md`
- Web accessibility/i18n: `platforms/web/web-accessibility-i18n.md`
- Web security: `platforms/web/web-security.md`
- Web review: `platforms/web/web-review.md`
- Server architecture: `platforms/server/server-architecture.md`
- Server API implementation: `platforms/server/server-api-implementation.md`
- Server data/jobs: `platforms/server/server-data-jobs.md`
- Server security: `platforms/server/server-security.md`
- Server review: `platforms/server/server-review.md`
- Application architecture: `platforms/application/application-architecture.md`
- Application command/UI implementation:
  `platforms/application/application-command-ui.md`
- Application React desktop renderer structure:
  `platforms/application/application-react-desktop.md`
- Application system integration: `platforms/application/application-system-integration.md`
- Application security: `platforms/application/application-security.md`
- Application review: `platforms/application/application-review.md`

## Product Pattern

- Auth/RBAC/permissions: `product-patterns/auth-rbac-permissions.md`
- Auth/RBAC implementation: `product-patterns/auth-rbac-implementation.md`
- Invitation flows: `product-patterns/invitation-workflows.md`
- Invitation implementation: `product-patterns/invitation-implementation.md`
- Billing/entitlements/quota: `product-patterns/billing-entitlements.md`
- Billing/entitlements implementation:
  `product-patterns/billing-entitlements-implementation.md`

## Workflow

- Workflow script command list:
  `python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py list`
- Preflight evidence wrapper:
  `python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-preflight.py --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> --command <command> --request "<USER_REQUEST>"`
- Finish evidence wrapper:
  `python3 <AGENTPLAYBOOK_ROOT>/scripts/agent-finish-check.py --project <TARGET_REPO> --rules <AGENTPLAYBOOK_ROOT> --gate "request intake=<evidence>" ...`
- Agent task lifecycle: `workflows/agent-task-lifecycle.md`
- Request triage: `workflows/request-triage.md`
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
Run `scripts/workflow.py route ...` to generate the command route before
manually selecting workflow documents, editing, reviewing, committing, or
reporting completion. Treat the route's gate ledger as a required execution
record, not a summary to reconstruct after the work. If the script cannot run,
stop and report the blocker or fallback approval before continuing with
`index.md`. Show a short gate signal after each completed gate or task step.
When wrapper scripts are available, run `agent-preflight.py` before editing and
`agent-finish-check.py` before final report, commit, release, or handoff.
Missing wrapper evidence or missing route gate evidence is non-compliant.

For any new request, first classify clarity and effort with
`common/task-intake-effort-routing.md`. Do not use the strongest model, longest
reasoning, or full-document loading by default. Use quick effort for exact
low-risk requests, standard effort for scoped implementation, and deep effort
only for ambiguous, broad, high-risk, or cross-boundary work.

Before running project commands, adding dependencies, or using framework-specific
APIs, use `common/stack-discovery.md`. When a command fails, use
`common/tool-failure-recovery.md` before retrying or changing code. When the
agent needs to ask a blocker question or approval, use
`common/agent-interaction.md`.

For PRD-only work, use `workflows/prd-creation.md` and run this scripted route:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route prd --platform <platform> --concern <concern>
```

For product or feature work that needs PRD -> ARD -> implementation ->
verification gates, use `workflows/product-architecture-delivery.md` and run
this scripted route:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route product --platform <platform> --concern <concern>
```

Use this `product` route, not the lower-level `feature` route, when the request
is broad app-building, product delivery, a new multi-screen flow, architecture,
data/auth/billing/release behavior, or a "show me how to build it" request that
will continue into code. The `feature` route is only for scoped slices where the
PRD/ARD gate is already satisfied or clearly unnecessary.

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
When deciding file layout, package layout, module ownership, public contracts,
or `api`/`impl` splits, also read `common/code-structure-ownership.md`.
Do not make `api`/`impl` modules by default. Choose that split only when a
stable external contract, navigation/deep-link/registration boundary,
implementation swap, dependency isolation, ownership split, or cycle/build
coupling pressure exists.
When code is extracted into shared modules, reused by multiple callers, or
promoted into a package/API, also read `common/reusable-code-design.md`.
When designing reusable UI components, hooks, widgets, controls, or other
caller-facing component APIs, also read `common/component-api-design.md`.
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

For prose, documentation tone, release notes, marketing copy, emails, or
AI-writing signal cleanup, read `common/human-authored-writing.md`. For UI text,
forms, localized copy, or accessibility-sensitive content, also read
`common/accessibility-i18n.md`.

For uploads, downloads, generated files, media, attachments, signed or temporary
URLs, public/private asset movement, asset cleanup, or asset references embedded
in persisted content, read `common/asset-lifecycle.md`.

For sitemap, robots, metadata, Open Graph previews, short links, public search,
AI search visibility, AEO/GEO claims, canonical URLs, link previews, structured
data, or public discovery feeds, read `common/public-discovery.md`.

For code that consumes external, persisted, generated, cached, platform, or
user-provided values, read `common/defensive-boundaries.md`.

For UI, application, async, cache, reducer, store, ViewModel, hook, or state
machine work, read `common/state-modeling.md`.

For error handling, typed failures, retries, and user-visible failure states,
read `common/error-modeling.md`. Add `common/observability-error-handling.md`
when logs, metrics, diagnostics, support traces, or audits are touched.

For UI layout, visible state, interaction, text overflow, responsive behavior,
or accessibility-visible changes, read `common/ui-visual-verification.md`.

For server-rendered data, API response caching, framework data cache,
request-level memoization, edge/CDN cache, database query cache, materialized
read models, or cache invalidation, read `common/server-side-caching.md`.

For Android work touching background execution, release builds, exported
components, deep links, WebView, permissions, or secrets, load the Android
background/security cards instead of relying only on the architecture card.

For Android Compose screen or component work, load
`platforms/android/android-compose-ui.md` before implementation. This includes
stateful/stateless boundaries, previews, component package structure, and
design-system promotion decisions.

For Android module, package, feature API, repository API, build-logic, or
shared-core ownership work, load
`platforms/android/android-module-structure.md` before implementation.

For Android ViewModel, `UiState`, Flow, repository, persistence, or one-off
event work, load `platforms/android/android-viewmodel-state.md` before
implementation.

For KMP or Compose Multiplatform work, load
`platforms/kmp/kmp-architecture.md`. For shared modules, source-set hierarchy,
umbrella frameworks, Gradle module splits, or KMP package ownership, also load
`platforms/kmp/kmp-module-structure.md`; for shared Compose UI, also load
`platforms/kmp/kmp-compose-ui.md`; for shared state, repositories, coroutines,
persistence, or adapters, load `platforms/kmp/kmp-state-data.md`; for source
sets, `expect`/`actual`, native interop, files, shell, clipboard, permissions,
or target capabilities, load
`platforms/kmp/kmp-platform-integration.md`.

For Flutter work, load `platforms/flutter/flutter-architecture.md`. For
feature folders, local packages, package exports, plugin package shape, or
federated plugin splits, also load
`platforms/flutter/flutter-project-structure.md`; for widgets, forms, routes,
design-system components, or golden/widget tests, also load
`platforms/flutter/flutter-widget-ui.md`; for state owners, streams,
repositories, storage, or async effects, load
`platforms/flutter/flutter-state-data.md`; for MethodChannel, EventChannel,
plugins, permissions, lifecycle, isolates, desktop, mobile, or web target
behavior, load `platforms/flutter/flutter-platform-integration.md`.

For Swift or Apple-platform work, load
`platforms/swift/swift-architecture.md`. For Swift Package Manager layout,
Xcode targets, package products, public APIs, access control, target
membership, resources, or file ownership, also load
`platforms/swift/swift-code-structure.md`. For SwiftUI, UIKit, or AppKit
design-system tokens, styles, primitives, reusable controls, variants, previews,
or visual QA, load `platforms/swift/swift-design-system.md`. For Swift review,
load `platforms/swift/swift-review.md`.

For iOS targets, local Swift packages, package exports, access control, feature
contracts, or target membership work, load
`platforms/ios/ios-module-structure.md` before implementation.

For iOS SwiftUI screen or component work, load
`platforms/ios/ios-swiftui-ui.md` before implementation. This includes
route/screen/section boundaries, ViewModel contracts, explicit `UiState`,
architecture tracks, previews, and design-system promotion decisions.

For iOS UIKit screen or component work, load `platforms/ios/ios-uikit-ui.md`
before implementation. This includes coordinator/view-controller boundaries,
typed UI state, lists, forms, navigation, and UI tests.

For iOS work touching Keychain, Universal Links, URL schemes, app extensions,
WebViews, permissions, entitlements, signing, release builds, or secrets, load
the iOS security card instead of relying only on the architecture card.

For desktop/application work touching menu bar/tray controls, shell, file,
clipboard APIs, power assertions, IPC, signing, notarization, updates, or first
launch, load the application system/security cards.

For desktop/application UI, commands, windows, panels, shortcuts, menu bar/tray,
background tasks, or renderer bridges, load
`platforms/application/application-command-ui.md`.

For React-based desktop app work, such as Tauri, Electron, WebView, or a native
shell with an embedded React renderer, load
`platforms/application/application-react-desktop.md` together with the matching
application command/system/security cards and the relevant web React structure
cards.

For macOS Swift apps, combine the Swift cards with the Application cards:
Swift owns package, state, design-system, and architecture boundaries;
Application owns window/panel/menu bar/tray commands, OS resources, IPC,
privileged APIs, packaging, signing, and updates.

For server API, GraphQL, RPC, webhook, route handler, validation, use case,
repository, response shape, or API error work, load
`platforms/server/server-api-implementation.md`.

When the task touches keys, auth, permissions, user data, logs, analytics,
external integrations, local config, release config, or a public/open-source
repo, read `common/secure-development-baseline.md` before implementation.

For React/web feature work, usually read:

```text
common/llm-coding-discipline.md
common/code-conventions.md
platforms/web/web-architecture.md
platforms/web/web-react-ui.md
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
