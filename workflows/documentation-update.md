---
keyflow_id: sys_documentation_update_workflow
status: review
type: human-reviewed-needed
---

# Documentation Update Workflow

Use when creating, reviewing, or restructuring docs, guides, specs, READMEs,
agent instructions, release notes, or knowledge-base pages.

## Read

- `workflows/agent-task-lifecycle.md`
- `common/code-conventions.md` for naming and clarity
- `common/llm-wiki-documentation.md` for wiki, knowledge-base, runbook,
  onboarding, durable architecture, or operational docs
- `common/project-naming.md` when names, slugs, or product identifiers appear
- `common/verification-policy.md` when links, examples, or commands can be checked
- `common/human-authored-writing.md` when the task changes prose voice, tone, or
  AI-writing signals without changing facts
- task-specific architecture, product-pattern, security, or release cards when the docs describe those surfaces

## Steps

1. Identify the document audience, purpose, source of truth, and expected action.
2. Check existing docs for overlap before adding a new page or section.
3. Keep repo-specific commands, paths, role matrices, and domain terms in repo-local docs.
4. Write shared agent library guidance in English. Localize only public-facing
   site copy or repo-local docs that intentionally target another locale.
5. Link to shared cards instead of copying full guidance.
6. For prose cleanup, preserve the original factual commitments and report when
   a style edit would change meaning, genre, or voice ownership.
7. Verify examples, links, file paths, commands, and metadata where practical.
8. Report what changed, what was verified, and any stale or missing source material.

## Promote Local Lessons

Move a local lesson into shared docs only when it remains useful after removing
project names, service names, local paths, command names, and platform-specific
API names.

Shared docs should capture:

- the recurring risk
- when to load the guidance
- the decision rule
- the verification question

Keep local docs responsible for:

- product policy
- repository commands
- file paths
- domain vocabulary
- platform-specific implementation details
- examples that only make sense in one codebase

## Stop If

- The doc would invent product policy, commands, or architecture not present in the repo.
- The same guidance already exists and should be linked or updated instead.
- The requested doc depends on a private source that is unavailable.
