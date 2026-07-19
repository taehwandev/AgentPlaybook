---
keyflow_id: sys_workflows_ambiguity_gate_md_skill
status: stable
type: ai-generated
---

# Ambiguity Gate

Use when routed to `workflows/skills/ambiguity-gate/SKILL.md` or when work needs this AgentPlaybook guidance area.

## Read

- `references/current-guidance.md` for the detailed guidance for this skill.
- Related `SKILL.md` entrypoints named by the reference before loading their detailed references.

## Process

1. Read this entrypoint first to confirm this guidance area applies.
2. Open `references/current-guidance.md` only when the task actually touches this area.
3. Follow the reference's decision rules, stop conditions, and verification requirements before editing, reviewing, or reporting completion.

## Evidence Contract

Keep existing finish-valid prose evidence compatible, but prefer structured
fields for new gate records so the ledger can reject incomplete decisions:

- `ambiguity check`: `blocker_status`, `assumptions`, and `decision`.
  `blocker_status` must be `none` or `resolved`, and `decision` must be
  `proceed`. Do not record success while a blocker remains unresolved.
- `alignment brief`: `shared_understanding`, `possible_differences`,
  `assumptions`, and `checkpoint`. `checkpoint` must be
  `user_visible_before_edits`; a private or post-edit summary is not an
  alignment checkpoint.

These fields record the decision that made work safe to start. They do not
replace the direct-answer-first rule or a required Grill-Me session.

## Do Not

- Do not look for legacy flat compatibility paths; load this skill bundle as the canonical context-loading target.
- Do not load broad references for unrelated work just because this skill was nearby in the route.

## Verification

- If route wiring changes, confirm the route loads this `SKILL.md` entrypoint.
- If detailed guidance changes, validate links and frontmatter for `references/current-guidance.md`.
