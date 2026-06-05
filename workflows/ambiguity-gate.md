---
keyflow_id: sys_ambiguity_gate_workflow
status: review
type: human-reviewed-needed
---

# Ambiguity Gate

Use before PRD, ARD, task breakdown, implementation plan, or code work when the request has unknowns that could change behavior, scope, risk, or verification.

For initial request clarity, effort level, token budget, and question-drill decisions, also use `../common/task-intake-effort-routing.md`.

## Core Rule

Do not turn unknowns into silent assumptions.

Inspect the current conversation, repo-local instructions, product docs, architecture docs, existing code, tests, and recent artifacts before asking the maintainer. Do not ask for information that is already available in the repo or conversation.

## Unknown Classes

Classify each unknown as exactly one of these:

- `blocker`: The answer can change user-facing behavior, scope, architecture, permissions, privacy, data safety, release risk, or acceptance criteria.
- `researchable`: The answer should be found in repo docs, code, tests, platform docs, current artifacts, or local context before asking.
- `assumable`: The answer is a reversible implementation detail, follows local patterns, and does not change product meaning or risk.
- `out-of-scope`: The request conflicts with current product direction or should be deferred or rejected.

Ask the maintainer only for `blocker` unknowns.

## Question Drill

Use a question drill when the user asks the agent to refine the request, or when the request is too vague to classify without inventing behavior.

Examples:

- "Change the button on home" usually needs a drill unless the repo has one obvious home button and a reversible local pattern.
- "Improve the X button in `HomeScreen`" is usually scoped enough to inspect `HomeScreen` first and ask only if behavior or acceptance remains unclear.
- A pasted compiler/test/runtime error is usually clear enough for quick or standard debugging without a drill.

Do not use the drill as ceremony for clear low-risk tasks.

## Mandatory Blockers

Stop and ask when any of these are unclear:

- user problem or intended outcome
- scope and explicit non-goals
- visible UI behavior, entry point, or state model
- success, empty, loading, unavailable, permission-denied, and failure behavior
- persistence, destructive changes, migrations, rollback, or compatibility
- permissions, privacy, secrets, network access, external state, or release impact
- feasibility when the feature depends on fragile platform or third-party behavior
- acceptance criteria or verification strategy

## Question Pass

- Ask one to three concise questions by default.
- Ask up to five only when multiple high-risk blockers exist.
- Each question should name the decision being made and why it matters.
- Do not ask preference questions already settled by repo docs, product docs, architecture docs, existing UI, or platform constraints.
- Batch questions once, then wait. Do not proceed into PRD, ARD, or implementation while blockers remain.

When blocked, use this shape:

```text
Decision: needs-clarification

Blocking unknowns:
- <category>: <why this changes behavior, risk, or verification>

Questions:
1. <decision question and consequence>

Safe assumptions:
- <only non-blocking assumptions, if any>
```

## Assumptions

If no blockers remain, record assumptions explicitly:

```text
Assumption: <specific default>
Reason: <repo pattern, product rule, or reversible implementation detail>
Risk: <what changes if this assumption is wrong>
```

When the maintainer asks the agent to proceed with assumptions, choose the smallest reversible option that matches existing product and architecture rules.

## PRD Conversion

After blockers are resolved:

- summarize maintainer decisions and repo-researched facts separately
- list assumptions separately from decisions
- write behavior scenarios in `Given / When / Then` form
- include success, empty, loading, unavailable, permission-denied, and failure states when relevant
- tie scenarios to acceptance criteria and verification

Do not leave unresolved blockers as open questions. Open questions are allowed only for non-blocking future follow-up.

## Stop If

- A blocker unknown can change product behavior, security, data handling, release risk, or verification.
- The answer should exist in repo-local docs or code but has not been inspected.
- The maintainer asks for a PRD, ARD, task breakdown, or implementation while blocker unknowns remain.
- Proceeding would require inventing product policy, acceptance criteria, or permission behavior.