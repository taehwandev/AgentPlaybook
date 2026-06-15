---
keyflow_id: sys_llm_wiki_documentation
status: review
type: human-reviewed-needed
---

# LLM Wiki Documentation

Use when creating or reviewing wiki, knowledge-base, runbook, onboarding,
architecture, decision, or operational docs that humans and AI agents will read.

An LLM wiki is not a content dump. It is a durable knowledge layer that helps an
agent retrieve the right facts, distinguish source of truth from commentary, and
act without inventing missing policy.

## Page Contract

Each durable wiki page should make these fields obvious, either in frontmatter or
the opening section:

- title
- audience
- purpose
- status: draft, review, stable, or deprecated
- owner or source of truth
- last verified date when commands, links, behavior, or external facts can age
- applies-to scope: repo, app, platform, feature, workflow, or team
- related pages

Use frontmatter when the repo already supports it. Otherwise keep the contract as
a short "At a glance" section near the top.

Shared AgentPlaybook cards may use the smaller `keyflow_id` / `status` / `type`
frontmatter contract. Add owner, source of truth, last verified, applies-to, and
related pages when a page is a durable wiki, runbook, operational procedure, or
runtime-facing integration guide whose facts can age independently.

## Structure

- Start with what the reader can do after reading the page.
- Put canonical facts before examples, history, or discussion.
- Use stable headings that can be linked by agents and search tools.
- Keep one concept per section. Split mixed pages when each section has a
  different owner, lifecycle, or verification path.
- Put procedures in ordered steps and reference material in tables or short
  lists.
- Mark assumptions, decisions, and open questions explicitly.
- Link to source docs instead of copying long policies from another page.
- Keep examples small and current enough to copy safely.

## Actionability

A durable agent-facing page should make the next action hard to miss:

- For a policy page, state the decision rule and what action is blocked.
- For a workflow page, state entry criteria, ordered gates, stop conditions, and
  completion evidence.
- For a platform page, state ownership boundaries, forbidden dependency leaks,
  state/error/data expectations, and target-specific verification.
- For a review page, state severity priority, concrete checks, evidence gaps,
  and output shape.
- For a reference page, state which facts are canonical, which are examples, and
  when the page must be refreshed.

Avoid pages that only describe ideals. Each page should include at least one of:
`Steps`, `Decision Rule`, `Do Not`, `Stop If`, `Review Checklist`,
`Verification`, `Tests`, or `Output`, using the heading that best matches the
page's purpose.

## Retrieval Rules

- Use literal names for APIs, commands, files, routes, events, and products when
  they are the lookup key.
- Add common synonyms only when readers actually search for them.
- Avoid clever titles. Prefer searchable titles over branded wording.
- Do not hide important constraints only in prose. Surface them as bullets,
  tables, "Do not", "Stop if", or "Check" sections.
- Put dates in exact form, such as `2026-05-23`, when time matters.

## Source Boundaries

- Keep repo-local commands, paths, service names, role matrices, and product
  policy in repo-local docs.
- Keep reusable agent behavior, review rules, and platform-neutral guidance in
  shared docs.
- Do not mix marketing copy with operational source-of-truth guidance.
- Do not paste secrets, private prompts, tokens, credential contents, customer
  data, or private incident details into wiki pages.
- Do not present guesses as established behavior. Label inferred or unverified
  content.

## Language

For agent-facing or cross-repo operational wiki pages, prefer English as the
canonical source. Localized versions can exist for onboarding or distribution,
but they should link back to the canonical page and avoid becoming a separate
policy source.

## Maintenance

- Update the page when behavior, ownership, commands, contracts, or verification
  changes.
- Deprecate stale pages instead of leaving competing guidance active.
- Merge duplicate pages when they answer the same reader question.
- Split pages when a page mixes policy, procedure, reference, and changelog
  content that age at different speeds.
- Record verification evidence for commands, links, screenshots, generated
  output, or external facts when practical.

## Check

- Can an agent identify the page's owner, scope, status, and source of truth?
- Is the action path clear without reading unrelated pages?
- Are stale facts, assumptions, and open questions visible?
- Does this page duplicate another page that should be updated instead?
- Are secrets, private data, and repo-specific details kept in the right place?

## Tests

For documentation-only changes, verify frontmatter or page contract, internal
links, referenced files, command examples, and duplicate overlap where practical.
For public or localized docs, also verify language switching, missing
translations, long text layout, and that localized copy does not conflict with
the canonical source.
