---
keyflow_id: sys_retrospective_skill_feedback
status: stable
type: human-reviewed-needed
---

# Successful-Task Skill Feedback

Use after a successful work-producing task when the completed work, user
correction, review, or verification exposed a reusable gap in a skill the agent
actually loaded and applied. This Hermes-inspired flow is best-effort and
non-blocking:

```text
observe -> curate -> review -> stage -> maintain
```

Each arrow is an asynchronous boundary. No stage may borrow authority from the
next one.

The separation is adapted from Hermes Agent's documented skill-creation and
periodic curator model, while AgentPlaybook adds stricter content-free records,
explicit caps, staging, and verification before canonical writes:

- <https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/>
- <https://hermes-agent.nousresearch.com/docs/user-guide/features/curator>

## 1. Observe After Success

Ask one bounded question: would a future agent materially benefit from changing
one skill actually used in this task?

- If no, emit nothing. Do not create a no-change record merely to prove
  reflection.
- If yes, emit at most one allowlisted, content-free observation through the
  optional `skill-feedback` hook.
- The caller may name only a skill actually loaded and applied in the completed
  task. Do not name an unrelated or merely adjacent skill.
- The hook derives an opaque occurrence key from the current preflight run. It
  never stores the raw run id.
- If the hook, store, current preflight occurrence, or token budget is
  unavailable, defer or drop the observation. The completed task remains
  successful.

The observation hook only records facts. It does not deduplicate recurrence,
queue review, ask a model to judge the skill, create a patch, or edit a
canonical file.

## Observation Schema

Use structured fields with exact validation:

```text
Skill observation:
- observation_id: <opaque id>
- candidate_id: <opaque identity derived from skill_id + signal>
- skill_id: <canonical safe skill id>
- signal: <content-free safe signal slug>
- occurrence_key: <opaque key derived from the current preflight run>
- status: observed
- created_at: <timestamp>
```

Observation records contain only content-free metadata. Do not store a raw run
id, prompts, responses, natural-language explanations, commands, paths, repo or
branch names, diffs, logs, source content, environment values, secrets, or
project-specific display names. Gap classification and change judgment do not
belong in the observation.

## 2. Deterministic Curation

A separate curator processes observations without a model. It may run through
the explicit `skill-curate` hook or the existing bounded maintenance pass:

1. Validate the observation shape and safe `skill_id` and `signal` slugs.
2. Deduplicate replayed `observation_id` and opaque `occurrence_key` values.
3. Build the recurrence identity from exact structured fields:
   `skill_id + signal`.
4. Count only distinct valid occurrence keys. Queue review at exactly two
   distinct occurrences.
5. Queue one idempotent review item when the threshold is reached. Preserve its
   distinct-occurrence count and first/last observation timestamps in the queue
   record so later passive-history pruning does not erase the review basis.
6. Keep every state class bounded. The default implementation caps
   review-ready items at 100, staged items at 100, passive observations at 500,
   and completed records at 200. The observation cap is strict. If pruning
   removes a terminal record, it also removes that candidate's passive
   observations so an old `no_change`, `applied`, or `rejected` decision cannot
   be resurrected. Retention never deletes or rewrites canonical skills.

The lifecycle status is `observed -> review_ready -> no_change | staged_patch`,
followed later by `applied | rejected` only after bounded maintenance.

The curator must not infer truth, severity, similarity, or recurrence from
prose keywords, task text, prompt content, path names, model confidence, or
free-form explanations. It must not draft or apply a patch. If curation or
storage is unavailable, leave observations pending without blocking work.

## 3. Bounded Review

A separate bounded reviewer consumes one queued recurrence item and the
canonical skill bundle. It chooses exactly one result:

- `no_change`: existing guidance already covers the issue, evidence is too
  weak, the signal is task-specific, or no testable improvement is justified.
- `staged_patch`: the reviewer supplies content-free `gap_type`, `change_type`,
  and `promotion_target` slugs and writes the decision to an isolated staging
  artifact for later maintenance.

Do not require or store those three reviewer judgments for `no_change`.

The reviewer does not write canonical skill files. A staged patch is a proposal,
not guidance and not promotion evidence. The review should prefer a focused
test, validator, routing rule, or concise decision rule over natural-language
keyword exceptions.

Default to one capable reviewer and the smallest relevant context. Add
independent review only when impact, ambiguity, or cross-owner scope justifies
it. If a reviewer or token budget is unavailable, leave the review queued and
continue ordinary work.

## 4. Staged Maintenance

Canonical skill writes happen only in a later bounded maintenance task:

1. Revalidate the queued observations, reviewer result, canonical owner, and
   current skill contents.
2. Reject or restage stale, ambiguous, cross-owner, or unverifiable proposals.
3. Author and apply the canonical change only when the active task authorizes
   that maintenance and the applicable approval policy is satisfied.
4. Run focused verification plus normal AgentPlaybook documentation,
   workflow, review, and finish checks. The maintenance recorder accepts
   `applied` only when the named canonical target is currently changed, its
   path is structurally linked to the staged `promotion_target`, and one fixed
   verification kind (`workflow_validate`, `unittest`, `py_compile`, or
   `vibeguard`) returns zero.
5. Mark the review applied only after that structural check succeeds. Keep
   rejected and applied history within the documented completed-record cap.

No observation hook, curator, scheduled reviewer, background worker, or model
may automatically mutate canonical skill guidance. Scheduling maintenance is
not authority to apply it.

Do not expose a direct promotion API or a single-hop feedback-to-promotion
path, including for manual maintenance. Every applied improvement must traverse
review, staging, structural target linkage, and a live verification receipt.

## Stop Or Defer

- Defer without blocking when observation storage, curation capacity, reviewer
  capacity, token budget, or maintenance capacity is unavailable.
- Return `no_change` when evidence does not justify a testable improvement.
- Stop staged maintenance when ownership is uncertain, the patch is stale,
  verification fails, approval is required but absent, or the proposed change
  would encode task-specific prose as shared policy.
- Never mark maintenance applied from a free-form verification description or
  a caller-supplied success word.
