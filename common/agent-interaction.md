---
keyflow_id: sys_agent_interaction
status: review
type: human-reviewed-needed
---

# Agent Interaction

Use when an agent needs clarification, approval, a status update, or a handoff
message.

## Default

Keep momentum. Ask only when the answer can change behavior, safety,
architecture, data handling, cost, or external state. Otherwise make a
reasonable assumption, state it briefly, and proceed.

If the user asks a direct question, answer it before starting workflow routing,
editing files, or running project-specific commands. Continue into work only
when the same message also contains a separate actionable request or the user
follows up with one.

Match the user's language for conversation. Keep shared agent-facing documents
in English.

## Communication

- Be concise, factual, and action-oriented.
- Report evidence and progress instead of generic confidence.
- Avoid open-ended questions when a concrete decision frame is possible.
- Avoid overclaiming; separate what was verified from what remains risky.

## Questions

Runtime, system, and developer instructions take precedence over this card. If
the runtime requires one short question, ask one short question. Use structured
choices only when they are allowed by the active runtime and helpful for the
decision.

Use `task-intake-effort-routing.md` to decide whether the request needs a
question drill or can proceed with quick/standard effort.

When a question is needed:

- Ask one to three questions at most.
- Prefer concrete choices over open-ended prompts.
- Include the recommended option first when there is a clear recommendation.
- State the tradeoff or consequence for each option.
- Name the default assumption if the user does not answer and it is safe to
  continue.

Use this shape:

```text
Decision needed:
- A: ... (recommended) - consequence
- B: ... - consequence

Default if safe:
```

## Question Drill

A question drill is a short sequence of blocker questions used to turn a vague
request into a clear task. Use it only when the user asks for requirements
discovery or when ambiguity changes behavior, risk, scope, or verification.

- Do not drill when the request names a file, symbol, error, or exact behavior
  and local inspection can answer the remaining details.
- Do not ask more than one pass of questions unless the user's answer creates a
  new blocker.
- Match the user's language in the conversation.

## Approval Requests

Ask for explicit approval before destructive work, external writes, credential
changes, deploys, package publishes, migrations, paid usage increases, or
network/package execution that is not already trusted by repo-local policy.

Approval requests should name the command or action, target, and risk. Do not
treat approval for one risky action as permission for unrelated risky actions.

For VibeGuard, `audit` is the normal safety gate. Run `update` only after the
user explicitly approves refreshing an existing managed VibeGuard block. Run
`setup` only for a first-time target repo with no guardrails or after explicit
approval. If the user asks when VibeGuard is updated, answer this policy before
doing any work.

## Status Updates

For long-running work, report what context was gathered, what changed in the
plan, and what verification remains. Keep updates short and evidence-based.

When a scripted workflow route is used, show a gate signal after each completed
gate or task step:

```text
Gate signal: GREEN | gate: <gate> | evidence: <evidence> | next: <next gate>
```

Use `GREEN` only when the gate was executed and has evidence. Use `YELLOW` when
the gate is blocked or paused. Use `RED` when the gate was missed or lacks
evidence after it should have run. Do not wait until the final response to reveal
that a required gate was skipped.

## Handoff

When stopping before completion, include:

- current goal
- files changed or inspected
- commands run and results
- blockers or decisions needed
- safest next step

For completed work, include changed files, verification, skipped checks, and
remaining risk.
