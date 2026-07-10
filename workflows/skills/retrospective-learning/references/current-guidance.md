---
keyflow_id: sys_retrospective_learning_workflow
status: stable
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
- The agent missed any required workflow route gate, even once.
- A fake, placeholder, mocked, or TODO behavior was mistaken for complete behavior.
- A build, test, UI smoke, release, or commit-readiness check was unclear or absent.
- The next agent is likely to repeat the issue without a rule, doc, or test change.

Do not run a formal retrospective for trivial work with no reusable lesson.
For hook, finish-check, or required-gate recovery, use a short actionable
retrospective instead of a ceremonial write-up. It must name the immediate
correction plan, what can be fixed now, and what the next attempt must apply.
If nothing can be fixed safely, state the blocker and stop instead of writing an
empty retrospective.

## Read

- `workflows/skills/development-cycle/SKILL.md` for verification and side-effect audit context
- `workflows/skills/product-architecture-delivery/SKILL.md` when PRD or ARD gaps caused the issue
- `common/skills/code-review/SKILL.md` for finding severity and evidence style
- `common/skills/verification-policy/SKILL.md` when test or evidence gaps caused the issue
- `common/skills/agent-editing-safety/SKILL.md` when user changes, external state, or secrets were involved
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
6. Record the lesson in the global local lesson store when the wrapper produced
   a candidate, or create a safe candidate manually when needed. Use only
   content-free reusable slugs: failure type, missed gate, root-cause category,
   next action, promotion target, and promotion status.
7. Apply the doc, test, hook, validation, or task update when it is safe and in
   scope; otherwise record the follow-up owner and location.
8. Restart at the first missed gate or same failed scope after the retrospective
   decision and correction plan are recorded. The next attempt must cite or
   apply that plan.
9. Report the learning in a short, reusable form.

## Output

Use this shape:

```text
Retrospective:
- Trigger:
- AI mistake:
- Missed signal:
- Earliest gate that should catch it:
- Root cause:
- Proposed fix:
- Durable fix:
- Updated doc/test/task:
- Discussion result:
- Follow-up:
```

Keep the write-up factual. Do not assign blame or narrate effort. Write the
retrospective discussion result in the user's language for that task. For
example, answer in Korean when the user is working in Korean, and in English
when the user is working in English.

## Global Lesson Store

Use `~/.agentplaybook/lessons/` as the user-local cross-agent memory store.
This store is not project evidence and is not a substitute for shared docs,
tests, workflow validation, or hooks.

Recommended directories:

```text
~/.agentplaybook/
  lessons/
    inbox/
    accepted/
    promoted/
  index.json
```

- `inbox`: automatically generated or manually drafted lesson candidates after
  a missed gate, failed hook, or repeatable agent mistake.
- `accepted`: local cross-agent lessons that should be checked by future agents
  on this machine.
- `promoted`: lessons already turned into shared docs, tests, validation, or
  hooks.

Global lesson records must not contain prompts, responses, commands, file paths,
repo names, branch names, diffs, logs, source content, environment values,
secrets, or project-specific display names. If a useful lesson cannot be
expressed without private content, do not store it globally; summarize the
safe reusable category in the project-local retrospective only.

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
