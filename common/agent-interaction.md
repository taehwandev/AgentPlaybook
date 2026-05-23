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

## Approval Requests

Ask for explicit approval before destructive work, external writes, credential
changes, deploys, package publishes, migrations, paid usage increases, or
network/package execution that is not already trusted by repo-local policy.

Approval requests should name the command or action, target, and risk. Do not
treat approval for one risky action as permission for unrelated risky actions.

## Status Updates

For long-running work, report what context was gathered, what changed in the
plan, and what verification remains. Keep updates short and evidence-based.

## Handoff

When stopping before completion, include:

- current goal
- files changed or inspected
- commands run and results
- blockers or decisions needed
- safest next step

For completed work, include changed files, verification, skipped checks, and
remaining risk.
