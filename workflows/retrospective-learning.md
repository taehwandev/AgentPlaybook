---
keyflow_id: sys_retrospective_learning_workflow
status: review
type: human-reviewed-needed
---

# Retrospective Learning Workflow

Use after a task, delivery cycle, review, incident, blocked run, or subagent handoff
when the work revealed a repeatable lesson. This is a post-cycle workflow, not a
required step for every small change.

The goal is to convert missed signals into better shared guidance, repo-local
rules, tests, or follow-up tasks.

## Trigger

Run this workflow when any of these happened:

- The same mistake or confusion appeared more than once.
- PRD, ARD, repo-local docs, or shared cards missed a requirement that changed the work.
- Verification passed but product, UI, security, data, release, or contract risk was still missed.
- A subagent or handoff caused duplicated work, conflict, or loss of context.
- The agent loaded the wrong docs, too many docs, or not enough docs.
- A fake, placeholder, mocked, or TODO behavior was mistaken for complete behavior.
- A build, test, UI smoke, release, or commit-readiness check was unclear or absent.
- The next agent is likely to repeat the issue without a rule, doc, or test change.

Do not run a formal retrospective for trivial work with no reusable lesson.

## Read

- `workflows/development-cycle.md` for verification and side-effect audit context
- `workflows/product-architecture-delivery.md` when PRD or ARD gaps caused the issue
- `common/code-review.md` for finding severity and evidence style
- `common/verification-policy.md` when test or evidence gaps caused the issue
- `common/agent-editing-safety.md` when user changes, external state, or secrets were involved
- matching platform, product-pattern, or concern cards from `index.md`

## Steps

1. State the trigger and the concrete work item where it appeared.
2. Separate facts, assumptions, missed signals, and unknowns.
3. Identify the earliest gate that should have caught it: PRD, ARD, pre-code review,
   code work, review, tests, UI tests, commit readiness, handoff, or release.
4. Name the root cause as a missing rule, unclear ownership, weak verification,
   stale docs, missing platform card, ambiguous product decision, or execution error.
5. Decide the smallest durable fix: shared doc update, repo-local instruction,
   PRD/ARD update, test, checklist item, TODO, or no change.
6. Apply the doc or task update when it is safe and in scope; otherwise record the
   follow-up owner and location.
7. Report the learning in a short, reusable form.

## Output

Use this shape:

```text
Retrospective:
- Trigger:
- Missed signal:
- Earliest gate that should catch it:
- Root cause:
- Durable fix:
- Updated doc/test/task:
- Follow-up:
```

Keep the write-up factual. Do not assign blame or narrate effort.

## Durable Fix Options

- Update `common/` when the rule is platform-neutral and reusable.
- Update `platforms/` when the rule is specific to Android, iOS, Web, Server, or Application.
- Update `workflows/` when the problem is sequencing, handoff, verification, or commit readiness.
- Update `product-patterns/` when the lesson is about auth, invitations, billing,
  entitlements, tenant boundaries, or other reusable product mechanics.
- Update repo-local `AGENTS.md`, PRD, ARD, TODO, or docs when the lesson is project-specific.
- Add or update tests when the problem should be caught automatically next time.

## Stop If

- The lesson depends on private data, secrets, prompt logs, or credentials that
  cannot be safely summarized.
- The root cause is still unknown and the retrospective would only speculate.
- The durable fix would require changing repo policy, product policy, security
  posture, release behavior, or external state without approval.
- The update would duplicate an existing rule instead of linking to it.
