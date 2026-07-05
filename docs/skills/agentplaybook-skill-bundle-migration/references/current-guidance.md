---
keyflow_id: sys_agentplaybook_skill_bundle_migration
status: review
type: human-reviewed-needed
---

# AgentPlaybook Skill Bundle Migration

Use this as the source of truth for maintaining AgentPlaybook's skill-bundle
layout. The canonical guidance shape is now `SKILL.md` entrypoints with scoped
`references/` files; flat `.md` paths are compatibility entrypoints.

## Goal

AgentPlaybook loads like a skill library:

```text
<area>/skills/<skill-name>/SKILL.md
<area>/skills/<skill-name>/references/<focused-detail>.md
```

`SKILL.md` is the small executable entrypoint: when to load, what to read, the
decision rule, stop conditions, and verification. `references/` holds examples,
deep checklists, source coverage, migration notes, and version-sensitive detail.

## Target Layout

Use this shape for new or materially reworked guidance:

```text
common/skills/<skill-name>/SKILL.md
common/skills/<skill-name>/references/*.md

workflows/skills/<workflow-name>/SKILL.md
workflows/skills/<workflow-name>/references/*.md

platforms/<platform>/skills/<skill-name>/SKILL.md
platforms/<platform>/skills/<skill-name>/references/*.md

product-patterns/skills/<pattern-name>/SKILL.md
product-patterns/skills/<pattern-name>/references/*.md

docs/skills/<doc-name>/SKILL.md
docs/skills/<doc-name>/references/*.md
```

Keep flat files as compatibility stubs while downstream repo instructions or
older runtime bridges may still reference them. Do not put full guidance back
into flat files; the detailed source should live in the bundle reference.

## Bundle Contract

Each `SKILL.md` should include:

- `Use When`: exact triggers and exclusions.
- `Read`: local instructions, related cards, source manifests, and reference
  files to open before work.
- `Decision Rule` or `Process`: ordered behavior, not background explanation.
- `Do Not` or `Stop If`: concrete actions that block editing, review, release,
  or handoff.
- `Verification`: smallest evidence that proves the changed surface.
- `Report`: source docs, changed cards, validation, and residual risk.

Reference files should be named by the decision they support, not by file type.
Prefer names such as `intent-security.md`, `release-measurement.md`, or
`route-boundaries.md` over `notes.md`, `details.md`, or `misc.md`.

## Maintenance Order

1. Create or update the canonical `SKILL.md` entrypoint first.
2. Put detailed rules, examples, source coverage, and long checklists in
   focused files under `references/`.
3. Keep the flat compatibility file as a short pointer to the bundle.
4. Update `index.md` and workflow routing to prefer bundle entrypoints.
5. Run workflow validation, route smoke, VibeGuard, and review hooks.
6. When splitting a broad `current-guidance.md`, preserve decision rules, stop
   conditions, and verification in either `SKILL.md` or a directly linked
   focused reference.

## Routing Policy

The workflow router should return canonical bundle entrypoints by default.
Legacy catalog constants may still name flat paths, but `workflow_route.py`
canonicalizes them through `scripts/workflow_skill_paths.py`.

During specialized migrations, routes may include multiple bundle entrypoints
when one entrypoint owns the manifest and another owns source application, such
as Android source coverage.

Keep a flat alias only as a compatibility stub. Do not route new work to a full
flat guidance file.

## Stop If

- A path change would break `scripts/workflow.py route`, docs-read receipts, or
  `python3 scripts/workflow.py validate`.
- A new bundle duplicates detailed guidance instead of using a focused
  reference.
- A reference file becomes the only source of a required stop condition.
- A shared reference copies third-party skill text instead of distilling a
  reusable rule.

## Verification

For each structural change:

1. Run `python3 scripts/workflow.py validate`.
2. Run a route that should include the new bundle and confirm the route output.
3. Run `vibeguard audit . --rules .`.
4. Check links and paths touched by the slice.
5. Review the diff for compatibility stubs, stale references, and duplicated
   source-of-truth language.
