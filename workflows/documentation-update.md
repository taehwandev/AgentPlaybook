---
keyflow_id: sys_documentation_update_workflow
status: review
type: human-reviewed-needed
---

# Documentation Update Workflow

Use when creating, reviewing, or restructuring docs, guides, specs, READMEs, agent instructions, release notes, or knowledge-base pages.

## Read

- `workflows/agent-task-lifecycle.md`
- `common/code-conventions.md` for naming and clarity
- `common/llm-wiki-documentation.md` for wiki, knowledge-base, runbook, onboarding, durable architecture, or operational docs
- `common/agent-skill-card-anatomy.md` when creating or materially updating an
  AgentPlaybook guidance card
- `common/project-naming.md` when names, slugs, or product identifiers appear
- `common/verification-policy.md` when links, examples, or commands can be checked
- `common/human-authored-writing.md` when the task changes prose voice, tone, or AI-writing signals without changing facts
- task-specific architecture, product-pattern, security, or release cards when the docs describe those surfaces

## Steps

 1. Identify the document audience, purpose, source of truth, and expected action.
 2. Check existing docs for overlap before adding a new page or section.
 3. For feature, product, workflow-policy, architecture, or public-contract
    changes, search and open PRD, spec, ARD, issue, design note, task doc, or
    source-of-truth docs before deciding what to write. If no source exists,
    record that absence and decide whether a PRD/spec must be created.
 4. Apply the commonization test before changing shared docs: the guidance must remain correct after removing one repo, product, service, vendor, customer, team, environment, or account context.
 5. Do not set the shared baseline from a specific service's workflow, API shape, naming scheme, role model, permission policy, deployment model, provider setup, or product policy.
 6. Keep repo-specific commands, paths, role matrices, and domain terms in repo-local docs.
 7. Write shared agent library guidance in English. Localize only public-facing site copy or repo-local docs that intentionally target another locale.
 8. Link to shared cards instead of copying full guidance.
 9. For prose cleanup, preserve the original factual commitments and report when a style edit would change meaning, genre, or voice ownership.
10. Verify examples, links, file paths, commands, and metadata where practical.
11. Report what changed, what was verified, and any stale or missing source material.

## Documentation Impact Checkpoint

For every work-producing task, make the documentation impact decision before
code, implementation, install/repair, or other edit work starts. This is the
prompt that keeps agents from treating docs as an afterthought.

Record:

- affected doc path or doc class, such as `AGENTS.md`, `README.md`, PRD/spec,
  ARD, runbook, platform card, workflow card, API reference, or "no durable doc
  class affected"
- intended decision: `updated`, `created`, `unchanged`, or `not applicable`
- why the changed behavior, workflow policy, public contract, operator action,
  or acceptance criteria do or do not require a documentation update

This checkpoint does not replace the final documentation decision. If the
implementation changes meaning, revisit the checkpoint and update the final
documentation evidence.

## Documentation Decision

For every work-producing task, record one of these decisions before completion:

| Decision | Use When | Evidence Must Name |
| --- | --- | --- |
| `updated` | Existing source-of-truth docs changed because behavior, workflow policy, public contract, operator action, or acceptance criteria changed. | Doc path, changed source, and reason. |
| `created` | No suitable source existed and the work introduced durable product, architecture, workflow, or operational meaning. | New doc path, owner/audience, and reason. |
| `unchanged` | Existing docs were inspected and already covered the change. | Doc path/class inspected and why no edit was needed. |
| `not applicable` | The task was answer-only or purely local/mechanical with no durable behavior, policy, contract, or operator meaning. | Checked doc class and why docs are out of scope. |

"Updated docs", "checked docs", or "no docs needed" is not enough finish
evidence. The evidence must say which document or document class was considered
and why that decision is correct.

## Review Readiness

For documentation review, do not stop at link and frontmatter validity. Report
the reviewed Markdown scope's readiness distribution:

- frontmatter missing or malformed count
- `status` values such as `draft`, `review`, `stable`, or `deprecated`
- `type` values such as `ai-generated`, `human-reviewed-needed`, or
  `human-reviewed`
- human-review queue count and the highest-risk docs still needing review

This readiness check is required for `docs-review` routes. A large
`human-reviewed-needed` queue is not a broken link, but it is a workflow risk
because agents may treat active guidance as more mature than it is.

## Minimum Card Maturity

Do not leave an AgentPlaybook card as a rough summary when it is meant to guide
agent behavior. A useful shared card should answer these questions directly:

- When to load it: the triggering task, file type, platform, workflow, or risk.
- What to inspect first: repo-local rules, source files, contracts, examples,
  manifests, commands, or related cards.
- Decision rule: when to keep work local, when to escalate, and what tradeoff
  justifies the heavier path.
- Do not / stop signals: mistakes that should block implementation, review,
  release, or handoff.
- Verification: the smallest evidence that proves the changed boundary, plus
  broader checks for higher-risk surfaces.
- Report contract: what the final response, PR, commit, or handoff must say
  when that card governed the work.

Use `common/agent-skill-card-anatomy.md` as the stricter contract when a card is
new, broad-use, recurring-mistake guidance, or expected to be loaded before
code, review, release, or handoff. The preferred shape includes explicit
anti-rationalization, red-flag, do-not, stop-if, verification, and report
sections so the guidance is executable rather than inspirational.

For short review cards, include at least findings priority, review checks,
verification focus, and output shape. For platform implementation cards, include
ownership boundaries, forbidden leaks, state/error/data handling, and target
verification. For workflow cards, include entry criteria, steps, stop signals,
and completion evidence.

Prefer an explicit `Do Not`, `Stop If`, `Do Not Approve When`, or equivalent
section when the card guides implementation or review. Do not hide blocking
mistakes only inside positive "Rules" prose; agents follow negative constraints
more reliably when the forbidden action is named directly.

If a card cannot answer these questions yet, mark the gap explicitly instead of
padding with generic advice.

## Promote Local Lessons

Move a local lesson into shared docs only when it remains useful after removing project names, service names, vendor names, account or environment names, local paths, command names, product policy, domain vocabulary, and platform-specific API names.

Shared docs should capture:

- the recurring risk
- when to load the guidance
- the decision rule
- the verification question

Keep local docs responsible for:

- product policy
- repository commands
- file paths
- service-specific workflows
- provider setup and deployment details
- domain vocabulary
- platform-specific implementation details
- examples that only make sense in one codebase

## Stop If

- The doc would invent product policy, commands, or architecture not present in the repo.
- The same guidance already exists and should be linked or updated instead.
- The requested doc depends on a private source that is unavailable.
