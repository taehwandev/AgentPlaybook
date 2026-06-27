---
keyflow_id: sys_agent_skill_card_anatomy
status: review
type: human-reviewed-needed
agentplaybook_card_contract: strict
---

# Agent Skill Card Anatomy

Use when creating, updating, or reviewing an AgentPlaybook common card,
workflow, platform card, product-pattern card, or agent-facing template.

The goal is to make each card executable by an agent: the card should say when
to load it, what to inspect, what decision to make, what not to do, and what
evidence proves the work.

## Use When

- A shared guidance card is added or materially changed.
- A workflow, platform, or product-pattern page is too broad to act on.
- A recurring mistake needs to become durable guidance.
- A document is expected to be read before code, review, release, or handoff.

Do not use this as a reason to rewrite unrelated cards. Apply it to the cards
that govern the current task or the recurring lesson being promoted.

## Decision Rule

A card is mature enough when an agent can answer these questions without
guessing:

- When should this card be loaded?
- What should be inspected before acting?
- What is the decision rule or ordered process?
- What actions are forbidden or should stop the work?
- What evidence verifies completion?
- What should the final report, review, PR, or handoff say?

If the card cannot answer those questions, either tighten the card or mark the
gap explicitly. Do not pad with generic advice.

## Card Contract

Prefer these sections for new or substantially revised cards:

1. `Use When`: trigger, scope, and exclusions.
2. `Inspect First` or `Read`: local docs, source files, contracts, examples, or
   related cards to load before action.
3. `Decision Rule` or `Process`: ordered behavior, not only principles.
4. `Common Rationalizations`: excuses agents use to skip the rule.
5. `Red Flags`: symptoms that should trigger review, escalation, or a stop.
6. `Do Not`: forbidden actions stated negatively and concretely.
7. `Stop If`: blockers that must prevent editing, release, or handoff.
8. `Verification`: smallest evidence that proves the changed surface.
9. `Report` or `Output`: what the final response or review must include.

Short review cards may combine sections, but they still need priority, checks,
evidence gaps, and output shape.

## Common Rationalizations

| Rationalization | Required Response |
| --- | --- |
| "This is obvious, so no verification section is needed." | Add the smallest evidence that proves the rule. |
| "The positive rule already implies what not to do." | Add an explicit `Do Not`, `Stop If`, or `Red Flags` section. |
| "The card is shared, so examples should be broad." | Keep examples small and remove repo-specific names, commands, and policy. |
| "A new card is easier than updating the old one." | Check overlap first and update the existing source of truth when possible. |
| "More context will make the card safer." | Use progressive disclosure; link detailed references instead of loading everything by default. |

## Red Flags

- A page describes ideals but has no decision rule, stop condition, or evidence.
- Multiple cards answer the same question with different language.
- A shared card encodes one product's role names, service setup, commands, or
  deployment model.
- A workflow page lacks entry criteria, ordered gates, stop signals, or
  completion evidence.
- A platform card lacks ownership boundaries, forbidden dependency leaks, state
  expectations, or target verification.

## Do Not

- Do not copy a third-party skill, vendor workflow, or repo-local policy
  wholesale into shared AgentPlaybook guidance.
- Do not add a new card when an existing card should be tightened or linked.
- Do not create separate "quick reference", "changelog", or auxiliary docs for
  a card unless the route explicitly needs a reference file.
- Do not put private paths, account names, product policy, commands, or service
  setup in shared guidance.
- Do not hide blockers only inside positive prose.

## Stop If

- The proposed card would become the source of truth for one product, team,
  account, deployment, or vendor-specific workflow.
- The source material is private or unavailable and the card would invent facts.
- The guidance conflicts with repo-local security, data, release, or
  verification policy.
- The card would require agents to load broad context for a narrow task.

## Verification

For document-only changes, run the repository's workflow validation and a diff
sanity check. For strict AgentPlaybook cards, validation should confirm
frontmatter and the required action sections.

When a route, concern, or command should load the card, add or update workflow
router tests that prove the card appears in the route manifest.

## Report

Report:

- cards added or tightened
- route, concern, or command wiring changed
- validation commands run
- remaining cards that still need anatomy cleanup
