---
keyflow_id: sys_agent_operating_skill
status: review
type: human-reviewed-needed
---

# Agent Operating Skill

Use this before implementation, review, refactoring, debugging, documentation, or verification work. This is the baseline skill for reducing repeated agent mistakes.

## Core Loop

1. Identify the target project and task type.
2. Classify request clarity and effort before loading broad context. If the user asks a direct question, answer it before starting workflow routing, editing, or project-specific commands.
3. Read repo-local instructions before changing files.
4. Discover the project stack before choosing commands or libraries.
5. For multi-step tasks, run `scripts/workflow.py route ... --request "<USER_REQUEST>"` before selecting task documents, editing, reviewing, committing, or reporting completion.
6. Read the route's listed docs before editing, reviewing, coding, or running
   project-specific work. Record `route docs read` evidence when the route
   includes that gate; the evidence must name that routed skill/guidance docs
   were read before code, implementation, or edits.
7. For requirements analysis or modification work, give a compact alignment
   brief before drafting requirements or changing files. State shared
   understanding, possible mismatch, and unsupported assumptions or minimal
   blocker questions. Do this even when the work is not PRD-sized.
8. Check preflight's global lesson summary when available. Accepted or promoted
   lessons from `~/.agentplaybook/` apply across repos unless repo-local
   instructions conflict.
9. Keep a gate execution ledger for the route and mark each gate with evidence when it is executed. Show a short gate signal after each completed gate or task step.
10. Use `index.md` to load only relevant AgentPlaybook cards.
11. Parallelize independent read-only orientation when the runtime supports it:
    selected document reads, file searches, stack inspection, git status, and
    preflight evidence may run together after request intake is settled.
12. Inspect existing code, docs, tests, and local conventions.
13. For code or architecture work that crosses files, packages, folders, or
    modules, record a compact structure packet before editing: chosen boundary,
    package/folder map, file split, allowed imports, forbidden imports,
    callers/tests, and nearest verification.
14. When a product alias or investigation crosses repositories, choose the
    primary repo from the acceptance path and stop for a workspace scope
    checkpoint before writing to any secondary repo.
15. Make the smallest change that genuinely addresses the request.
16. For code work, record the multi-agent split decision before editing and use
    parallel agents when scopes are disjoint and stable.
17. Update/create affected docs and add/update/run the nearest useful test when
    code behavior or workflow policy changes.
18. Verify with the narrowest reliable command first.
19. Confirm the route gate ledger before reporting completion.
20. Report what changed, what was verified, and what risk remains.

## Mistake Prevention Checklist

Before editing:

- Confirm target path and project.
- Classify the request as clear-exact, clear-scoped, vague-action, broad-product, risky-unclear, or direct-question before choosing effort.
- If classified as direct-question, answer first and do not start work unless a separate actionable request remains.
- If the direct question asks how to start app, product, or feature work, answer with the PRD -&gt; ARD -&gt; implementation sequence first. Do not give an implementation-only workflow for product delivery.
- If a blocker unknown can change behavior, scope, risk, acceptance criteria, or
  verification and repo context cannot answer it, ask before editing. Do not
  invent product intent or acceptance criteria silently.
- For requirements analysis, feature, bugfix, refactor, docs, workflow setup, or
  other modification routes, record an alignment brief before drafting or
  editing. It must be a concise same/different/assumption check, not a full
  Grill-Me `/grilling` session unless blockers require one.
- Check repo-local `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md`, `CODEX.md`, `.agents/README.md`, `CONTRIBUTING.md`, or equivalent docs.
- Check stack manifests, lockfiles, and config before running commands, adding dependencies, or using framework-specific APIs.
- Read the route's `Read In Order` docs before code, implementation, review,
  or edit work. Do not treat the route output as a passive suggestion; if the
  route includes `route docs read`, finish evidence must state that routed
  skill/guidance docs were read before work.
- When implementation can add or move more than one file, package, folder, or
  module, write the structure packet first. Do not start by dumping all code
  into one feature, `common`, `shared`, `utils`, `helpers`, `services`, or
  `manager` folder.
- Check whether the task touches data, auth, permissions, billing, persistence, filesystem, network, release, or external state.
- Check whether the task touches secrets, client keys, local config, logs, analytics, crash reporting, or open-source-safe setup.
- If a product/workspace alias may map to multiple repos, use local workspace
  group discovery or ask for the primary repo. Do not guess a single repo from
  the alias alone.
- Before writing to a secondary repo, record a workspace scope checkpoint:
  starting primary, secondary/source of truth, selected mode, write scope,
  session model, and cross-repo verification.
- Check for existing user changes in files you may touch.
- After route selection, read independent route documents and run read-only
  orientation commands in parallel when possible. Do not serialize document
  reads unless one document determines whether another is needed.
- `agent-preflight.py` may run in parallel with read-only orientation after the
  request is answered or classified, but no edit, setup, update, fix, commit,
  push, release, migration, or external-state change may start until preflight
  succeeds.

While editing:

- Follow existing architecture and naming before inventing a new pattern.
- Keep unrelated refactors out of feature or bug-fix work.
- Preserve user-owned changes.
- Do not expose secrets, tokens, private prompts, or credential contents.
- Do not claim mocked, placeholder, or TODO behavior is complete.
- For larger implementation work, split work across parallel agents only when
  the owned files, packages, contracts, and forbidden files are explicit and do
  not overlap. Serialize shared contracts, generated files, migrations,
  dependency changes, release config, and architecture boundaries.

Before finishing:

- Confirm every required workflow route gate has ledger evidence when a scripted route was used.
- Run the most relevant test, build, typecheck, lint, or smoke check.
- For code work, include evidence for ambiguity handling, docs freshness,
  tests, and multi-agent split decision when the route requires them.
- If verification cannot run, state why and what risk remains.
- Include file references when explaining non-trivial changes.
- If any required gate is missed or fails, run the retrospective workflow before
  retrying the same scope or reporting completion. Treat the generated global
  lesson candidate as a prompt to promote a recurring lesson into shared docs,
  tests, validation, or hooks.

## Task Routing

- Request clarity, Grill-Me, model/effort routing, or token reduction: `common/task-intake-effort-routing.md` and `workflows/request-triage.md`.
- Scripted workflow route: `workflows/scripted-agent-workflow.md` and `scripts/workflow.py` are mandatory for multi-step tasks when the script is available. Pass `--request "<USER_REQUEST>"` so the script can block direct questions and unclear work before implementation. If the script cannot run, report the blocker before using `index.md` as a fallback.
- Stack, package manager, framework, runtime, or command discovery: `common/stack-discovery.md`.
- Failed commands, compiler errors, lint errors, or broken verification: `common/tool-failure-recovery.md`.
- User questions, approval requests, and ambiguity communication: `common/agent-interaction.md`.
- Any multi-step agent task: `workflows/agent-task-lifecycle.md`.
- Interrupted or transferred work: `workflows/agent-handoff-continuation.md`.
- Ambiguous requests or blocker unknowns before PRD, ARD, task breakdown, or implementation: `workflows/ambiguity-gate.md`.
- PRD or product requirements note: `workflows/prd-creation.md`.
- App, product, or feature delivery that may continue into code: `workflows/product-architecture-delivery.md`. Use this before the lower-level feature workflow unless the request is already a trivial, scoped change.
- Multi-step development: `workflows/development-cycle.md`.
- Delegated or parallel agent work: `workflows/multi-agent-collaboration.md`.
- Non-trivial review or release candidate review: `workflows/multi-perspective-review.md`.
- Planning or research: `workflows/planning-research.md`.
- Documentation update: `workflows/documentation-update.md`.
- Feature work: `workflows/feature-implementation.md`.
- Bug or regression: `workflows/bugfix-debugging.md`.
- Refactor or cleanup: `workflows/refactor-cleanup.md`.
- Release-sensitive work: `workflows/release-readiness.md`.
- Final review or commit: `workflows/review-and-commit.md`.
- Architecture: `common/architecture-selection.md`, `common/architecture-design.md`, or `common/app-architecture.md`.
- LLM-readable wiki, knowledge-base, runbook, or durable documentation: `common/llm-wiki-documentation.md`.
- Code conventions: `common/code-conventions.md`.
- File/module layout, ownership, public contracts, `api`/`impl` splits, or
  `assertions`/test-support modules: `common/code-structure-ownership.md`,
  `common/solid-design-principles.md`, and
  `common/reusable-code-design.md`. These cards are a bundle for boundary
  work; do not load only one when the task changes dependency direction,
  caller-facing contracts, reusable fakes, fixtures, recorders, or assertion
  DSLs.
- Reusable code extraction or shared module/package contracts:
  `common/reusable-code-design.md`, plus `common/solid-design-principles.md`
  when the shared API exposes callbacks, interfaces, adapters, fakes, or
  replaceable implementations. When the task creates packages, folders,
  source sets, modules, or shared/core/common boundaries, include a package
  boundary note that names owner, allowed imports, forbidden imports, callers,
  and focused verification before editing. If the task adds several roles, also
  include the file split and package/folder map before writing code.
- Reusable component, hook, widget, control, or caller-facing API design: `common/component-api-design.md`.
- UI, async, reducer, store, ViewModel, hook, cache, or state-machine state design: `common/state-modeling.md`.
- Error handling, typed failures, retry classification, or failure UX: `common/error-modeling.md`.
- Project, app, repo, package, module, CLI, or service naming: `common/project-naming.md`.
- Change size or broad diffs: `common/change-size-policy.md`.
- Existing checkout, user-owned changes, or commit preparation: `common/worktree-hygiene.md`.
- Dependencies, SDKs, or build plugins: `common/dependency-policy.md`.
- Generated files, lockfiles, or snapshots: `common/generated-files-policy.md`.
- API, DTO, route, event, webhook, or shared fixture contracts: `common/api-contract-compatibility.md`.
- Upload, download, media, attachment, signed URL, public/private asset movement, cleanup, or embedded asset references: `common/asset-lifecycle.md`.
- External, persisted, generated, cached, platform, or user-provided values: `common/defensive-boundaries.md`.
- Environment-specific runtime URLs, API origins, callback URLs, redirect URIs,
  webhook endpoints, CORS origins, or asset hosts:
  `common/runtime-url-configuration.md`.
- Release, deployment, packaging, signing, rollout, rollback, versioning, or tags: `common/release-deployment.md` and `common/release-versioning.md`.
- User-facing text, forms, controls, dates, numbers, or localization: `common/accessibility-i18n.md`.
- User-facing prose, documentation tone, release notes, marketing copy, emails, voice fidelity, or AI-writing signal cleanup: `common/human-authored-writing.md`.
- SEO, AI search visibility, AEO/GEO claims, sitemap, robots, metadata, Open Graph, short links, canonical URLs, or public discovery feeds: `common/public-discovery.md`.
- UI layout, interaction, text overflow, responsive behavior, or accessibility-visible state: `common/ui-visual-verification.md`.
- Refactoring: `common/refactoring.md`.
- Tests and evidence: `common/testing.md` and `common/verification-policy.md`.
- Code review: `common/code-review.md`.
- Local programs, agent CLIs, or usage telemetry: `common/local-tools.md`.
- Secrets, external state, or user-owned changes: `common/agent-editing-safety.md`, `common/secure-development-baseline.md`, and `common/security-privacy-review.md`.
- React, iOS, Android, server, desktop, or application work: load the matching platform card from `index.md`.
- Android Navigation 3, deep links, typed route/back-stack contracts,
  mixed Compose/Activity routing, or route callbacks/events:
  `platforms/android/android-architecture.md` and
  `platforms/android/android-module-structure.md`, plus the structure/SOLID
  bundle above when route contracts, `api`/`impl`, `assertions`, fixtures,
  recording fakes, or assertion DSLs are added or moved. Add
  `platforms/android/android-security.md` when exported components, app links,
  WebView, permissions, or credentials are touched.
- Android Compose performance, stability, lazy lists, side effects, custom
  modifiers, baseline profiles, or measurement claims:
  `platforms/android/android-compose-ui.md`,
  `platforms/android/android-review.md`,
  `platforms/android/android-external-skill-source-coverage.md`, and the
  testing/verification cards. Do not claim a performance fix without the
  repo's relevant measurement evidence or a clear statement that only a
  structural risk was reduced.
- Android platform-surface or SDK work such as AGP upgrades, Android CLI/device
  inspection, R8/keep rules, Perfetto traces, XML-to-Compose migration,
  adaptive layouts, edge-to-edge, Compose Styles, CameraX, Credential Manager,
  Play Billing, Play Engage, Wear Compose, XR/Glimmer, or AppFunctions:
  load the Android architecture/module/Compose/security card that matches the
  surface, then apply the no-omission source manifest in
  `platforms/android/android-external-skill-source-coverage.md` before editing.

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

For small tasks, a concise paragraph is enough, but verification status still matters.
