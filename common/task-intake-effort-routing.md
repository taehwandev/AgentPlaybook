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
| `direct-question` | Asks for an explanation, timing, policy, status, or meaning without asking the agent to change files or run work. | Answer first. Do not start workflow routing, editing, or project-specific commands unless a separate action remains. If the question asks how to start app, product, or feature work, the answer must include the PRD -> ARD -> implementation path before lower-level coding steps. |
| `clear-exact` | Names a file, symbol, command, error, stack trace, failing test, or precise behavior. | Use quick or standard effort; inspect the named target first. |
| `clear-scoped` | Names a screen/component/feature and intended change, but local context is needed. | Use standard effort; inspect local code and route to the matching platform card. |
| `vague-action` | Says "fix", "improve", "clean up", "make better", or similar without target behavior. | Use ambiguity gate or question drill before implementation. |
| `broad-product` | Asks for a new feature, architecture, PRD, multi-screen flow, data model, billing/auth, or release behavior. | Use product/PRD route and deeper effort. |
| `risky-unclear` | Could affect data, security, money, permissions, destructive changes, migrations, deploys, or external state. | Stop for blocker questions or approval. |

Examples:

- "When does the agent run VibeGuard update?" -> `direct-question`; answer that
  update is only used after explicit approval to refresh an existing managed
  VibeGuard block, otherwise audit current guardrails.
- "Change the button on home" -> `vague-action`; ask which button, state, and
  expected behavior unless the repo has one obvious home button.
- "Improve the X button in `HomeScreen`" -> `clear-scoped`; inspect
  `HomeScreen`, nearby UI patterns, and platform UI cards.
- "Fix this compiler error: <error output>" -> `clear-exact`; inspect the
  referenced file and line before loading broad architecture cards.
- "Build invitations with roles and billing limits" -> `broad-product`; use PRD
  or product workflow with auth, invitation, and billing cards.
- "Show me how we build an app/feature in this repo" -> `direct-question` if
  answer-only, but the answer must front-load PRD -> ARD -> implementation. If
  the user asks to proceed, use the `product` route, not `feature`.

## Decision Rule

The selected route must protect the highest-risk part of the request, not the
last word the user used. If a request includes both a simple edit and auth,
data, billing, release, migration, external state, or architecture risk, route
for the risky surface.

Use `direct-question` only until the question is answered. If the same turn also
contains an actionable request, continue with the appropriate route after the
answer and keep the answer as request-intake evidence.

Do not downgrade effort only because a task names one file. If that file is a
composition point, public contract, migration, release config, app shell, or
security boundary, inspect the owner boundary and escalate.

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
For Korean requests, treat "그릴미" as the same explicit drill request.
When wrapper evidence is available, a route classification with
`question_drill: true` must finish with question-drill evidence such as
`question drill if needed=<evidence>` or `ask blockers=<evidence>`. Missing
drill evidence is `🐱🔴 FAIL` and requires missed-gate recovery plus the
retrospective workflow before final report, commit, release, or handoff.

## Token Controls

- Start with repo-local instructions and this intake card; do not load the full
  library.
- Use `scripts/workflow.py classify "<request>"` for unclear, direct-question,
  or multi-step requests when the script is available; skip it only for clear,
  low-risk answer-only tasks after answering them.
- Use `scripts/workflow.py route <command> --request "<request>"` for multi-step
  routes. If the script reports `direct-question`, answer before routing. If it
  reports `question_drill: true`, use `triage` or `ambiguity` before work.
- Route after classification: load only the command/platform/concern cards that
  match the task.
- For exact errors, read the error output, referenced files, and nearby code
  before broad docs.
- For exact UI targets, inspect the named screen/component and nearby patterns
  before product-wide architecture.
- For broad product requests, spend tokens on PRD/acceptance criteria before
  implementation details. Do not collapse "app-making" or "feature delivery"
  into implementation-only steps.
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

## Verification

Intake is verified when the route and effort explain:

- why the request is answer-only, exact, scoped, vague, broad, or risky
- which repo-local or AgentPlaybook documents must be read before work
- which gate or question drill blocks implementation, if any
- which verification surface will prove the request when work is complete

When a scripted route is used, the route output and wrapper preflight evidence
are the intake record. When no route is needed, keep the classification implicit
unless it affects scope, safety, or user expectations.

## Report

When useful, report the classification briefly:

```text
Intake: clear-scoped / effort: standard
Reason: target screen and button are named, but local UI patterns need inspection.
Route: feature --platform <platform> --concern ui
```

For tiny tasks, do not over-report. The classification should reduce work, not
become a ceremony.
