---
keyflow_id: sys_multi_perspective_review_workflow
status: review
type: human-reviewed-needed
---

# Multi-Perspective Review

Use for non-trivial reviews where a single correctness pass may miss product,
UX, architecture, reliability, security, release, or QA risk.

Review perspectives are lenses, not fictional voices. Each perspective should
produce concrete findings, risks, and verification gaps.

## Use When

- code changes are non-trivial
- UI, interaction, or navigation changed
- architecture, module boundaries, or refactors changed
- permissions, privacy, security, packaging, or distribution changed
- release candidates need a broad readiness pass
- a feature idea needs structured critique before implementation

For tiny mechanical edits, use `common/code-review.md` directly.

## Context Packet

Collect:

- user request or feature intent
- changed files or diff summary
- relevant PRD, ARD, issue, task, or design note
- product constraints and non-goals
- verification already run
- known unresolved questions and residual risk

Do not invent acceptance criteria when a blocking product decision is missing.
Use `workflows/ambiguity-gate.md` first.

## Perspectives

Product / Scope:

- product fit, scope creep, user value, non-goals, and whether the change belongs
  in this product surface

Platform UX:

- platform conventions, visual hierarchy, hit targets, menus, navigation,
  motion, accessibility labels, and discoverability

Workflow:

- repeated-use speed, keyboard and pointer ergonomics, fallback paths, and
  recovery from disabled or failed states

Architecture / Maintainability:

- module boundaries, state ownership, side effects, coupling, testability,
  migration safety, and whether complexity is reduced or hidden

Reliability / Performance:

- refresh cadence, async cancellation, resource use, timeouts, startup behavior,
  stale data, unavailable dependencies, and failure recovery

Security / Privacy / Release:

- permissions, secrets, user trust, private or privileged API risk, data
  retention, packaging, signing, deployment, and rollback

QA / Regression:

- edge cases, empty/loading/error/permission states, known regressions,
  automated coverage, smoke/manual coverage, and missing acceptance checks

## Specialist Personas

Use these as named lenses when they match the risk. They are roles in the review
packet, not separate authorities:

- Code Reviewer: correctness, readability, ownership, imports, side effects,
  maintainability, and nearest tests.
- Test Engineer: assertions, fixtures, state coverage, boundary values,
  regression evidence, and missing automated or manual checks.
- Security Auditor: auth, permission, tenant, secret, privacy, dependency,
  logging, and release trust boundaries.
- Web Performance Auditor: Core Web Vitals, bundle size, runtime cost, network,
  cache, layout shift, and measurement quality.

Split these across subagents only when each reviewer receives raw artifacts,
clear scope, and no leaked expected answer. Merge duplicate findings and keep
the final recommendation in one place.

## Output

Lead with findings:

```text
Findings:
- [Severity] Perspective: path:line or behavior area - issue, impact, recommendation, verification
```

Then include:

- cross-perspective tradeoffs
- open questions
- verification gaps
- concise recommendation

If there are no findings, say so clearly and list remaining test gaps or
residual risk.

## Severity

- Blocker: should not ship without a fix or decision.
- High: likely user-visible regression, data loss, permission confusion, trust
  risk, or unbounded maintenance cost.
- Medium: meaningful risk, missing tests, or workflow issue that should be fixed
  soon.
- Low: polish, clarity, naming, or minor maintainability improvement.
- Note: observation without required action.

## Modes

- Full review: use every perspective.
- Lightweight review: Product / Scope, Architecture / Maintainability, and
  QA / Regression.
- Release review: full review plus repo-local release checklist.
- Delegated review: split perspectives across agents only when write scopes and
  review ownership are explicit.

Merge duplicate findings. If perspectives disagree, name the tradeoff instead
of averaging it away.

## Stop If

- Required context is missing: request, diff, acceptance criteria, known risk, or
  verification evidence.
- A blocking product, security, release, or data decision is unresolved.
- The review would invent acceptance criteria instead of using the request,
  PRD, ARD, issue, or repo-local policy.
- A release review is requested but repo-local release artifacts or checks are
  unavailable.
