---
keyflow_id: sys_task_intake_effort_routing
status: review
type: human-reviewed-needed
---

# Task Intake And Effort Routing

Use at the start of an agent conversation or task when deciding whether the
request is clear enough, whether to ask a clarification drill, and how much
model effort, context loading, and workflow depth the task deserves.

The goal is to use the lowest capable effort level without skipping safety,
verification, or repo-local rules.

## Intake Decision

Classify the request before loading many documents or doing deep reasoning.

| Class | Signal | Default Action |
| --- | --- | --- |
| `clear-exact` | Names a file, symbol, command, error, stack trace, failing test, or precise behavior. | Use quick or standard effort; inspect the named target first. |
| `clear-scoped` | Names a screen/component/feature and intended change, but local context is needed. | Use standard effort; inspect local code and route to the matching platform card. |
| `vague-action` | Says "fix", "improve", "clean up", "make better", or similar without target behavior. | Use ambiguity gate or question drill before implementation. |
| `broad-product` | Asks for a new feature, architecture, PRD, multi-screen flow, data model, billing/auth, or release behavior. | Use product/PRD route and deeper effort. |
| `risky-unclear` | Could affect data, security, money, permissions, destructive changes, migrations, deploys, or external state. | Stop for blocker questions or approval. |

Examples:

- "Change the button on home" -> `vague-action`; ask which button, state, and
  expected behavior unless the repo has one obvious home button.
- "Improve the X button in `HomeScreen`" -> `clear-scoped`; inspect
  `HomeScreen`, nearby UI patterns, and platform UI cards.
- "Fix this compiler error: <error output>" -> `clear-exact`; inspect the
  referenced file and line before loading broad architecture cards.
- "Build invitations with roles and billing limits" -> `broad-product`; use PRD
  or product workflow with auth, invitation, and billing cards.

## Effort Profiles

Use runtime-specific model or reasoning controls only when the runtime supports
them. If model selection is not available, apply the same profile through
context loading, planning depth, and verification scope.

| Effort | Use When | Behavior |
| --- | --- | --- |
| `quick` | Clear exact target, low risk, one file/symbol/doc answer, or explicit error output. | Read local instructions plus the exact files/snippets; avoid broad planning; run the narrowest check. |
| `standard` | Scoped implementation, bugfix, refactor, or docs work with normal local context. | Use workflow route, relevant platform/common cards, focused plan, focused verification. |
| `deep` | Ambiguous product behavior, architecture choice, security/data/release risk, cross-module changes, or repeated failure. | Use ambiguity/product/multi-perspective routes, more context, explicit tradeoffs, stronger verification. |
| `specialist` | Platform/security/release/billing/auth/database/AI-tooling risk requires a specific skill or expert agent. | Route to the specialist card/agent and keep write scopes explicit. |

Do not default to the strongest model, longest reasoning, or full-document
loading when the request is clear and low risk. Escalate when evidence shows the
task is broader or riskier than first classified.

## Question Drill

A question drill is included, but it is not the default for every request. Use it
when the user wants requirements discovery, the request is `vague-action`, or
unknowns can change behavior, scope, risk, or verification.

Drill rules:

- Ask only blocker questions after checking available conversation and repo
  context.
- Ask one to three concise questions per pass.
- Prefer concrete choices with tradeoffs and a recommended default when the
  runtime allows structured choices.
- Stop the drill when the task can be classified as `clear-exact`,
  `clear-scoped`, or `broad-product` with known acceptance criteria.
- Do not use a drill to delay a clear low-risk task.
- Do not ask questions that repo-local docs, code, tests, PRD/ARD docs, or error
  output can answer.

If the user explicitly asks for "grill me", "ask me questions", "help define
requirements", or equivalent wording, run the drill as the deliverable until
enough decisions are captured.

## Token Controls

- Start with repo-local instructions and this intake card; do not load the full
  library.
- Use `scripts/workflow.py classify "<request>"` for unclear or multi-step
  requests when the script is available; skip it only for clear, low-risk,
  answer-only tasks.
- Route after classification: load only the command/platform/concern cards that
  match the task.
- For exact errors, read the error output, referenced files, and nearby code
  before broad docs.
- For exact UI targets, inspect the named screen/component and nearby patterns
  before product-wide architecture.
- For broad product requests, spend tokens on PRD/acceptance criteria before
  implementation details.
- Summarize large files or command output; keep only evidence needed for the
  next decision.

## Escalation Triggers

Escalate from `quick` to `standard` or `deep` when:

- the named file is not the real owner of the behavior
- the change crosses modules, platforms, data, auth, billing, release, or
  external state
- tests fail for reasons unrelated to the narrow change
- user-facing behavior, acceptance criteria, or verification is unclear
- a command failure repeats after one focused correction
- a safety or VibeGuard gate reports a blocker

## Report

When useful, report the classification briefly:

```text
Intake: clear-scoped / effort: standard
Reason: target screen and button are named, but local UI patterns need inspection.
Route: feature --platform <platform> --concern ui
```

For tiny tasks, do not over-report. The classification should reduce work, not
become a ceremony.
