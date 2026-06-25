---
keyflow_id: sys_request_triage_workflow
status: review
type: human-reviewed-needed
---

# Request Triage Workflow

Use when the agent needs to decide whether a user request is clear, whether a
Grill-Me `/grilling` session is needed, and what effort level or route should be used
before planning or implementation.

## Read

- `common/task-intake-effort-routing.md`
- `common/agent-interaction.md`
- `workflows/ambiguity-gate.md` when blockers remain
- `index.md` only after the task is classified

## Steps

1. Identify the requested deliverable: answer, edit, review, PRD, plan,
   debugging, refactor, release, or handoff.
2. Classify clarity: `direct-question`, `clear-exact`, `clear-scoped`,
   `vague-action`, `broad-product`, or `risky-unclear`.
3. Select effort: `quick`, `standard`, `deep`, or `specialist`.
4. For requirements analysis, record the compact alignment brief before a
   Grill-Me session: shared understanding, possible mismatch, and
   unsupported assumptions or blocker questions.
5. If `direct-question`, answer before workflow routing, editing, or
   project-specific commands. Stop unless a separate actionable request remains.
6. If `clear-exact`, inspect the named target and avoid broad route loading.
7. If `clear-scoped`, run the smallest matching workflow route.
8. If `vague-action` or `risky-unclear`, run Grill-Me or use the ambiguity gate.
9. If `broad-product`, use PRD/product workflow before implementation.
10. Record the selected route only when it changes the work.

## Grill-Me Output

Use when clarification is the deliverable or blockers prevent safe work:

```text
Intake: vague-action / effort: deep-until-clarified

Decision needed:
- A: <recommended concrete direction> - <tradeoff>
- B: <alternative> - <tradeoff>

Why this matters:
- <behavior, risk, verification, or scope impact>
```

## Stop If

- The request could affect data, security, billing, release, destructive
  changes, or external state and the key decision is unclear.
- The user asked a direct question and the agent is about to start work without
  answering it.
- The user asked for requirements discovery and the agent is about to implement.
- The agent is about to use deep effort or a specialist agent for a clear
  low-risk request without a reason.
- The agent is about to answer a vague task with invented acceptance criteria.
