---
keyflow_id: sys_docs_agentplaybook_skill_bundle_migration_md_skill
status: review
type: ai-generated
---

# AgentPlaybook Skill Bundle Migration

Use when creating, moving, splitting, routing, or reviewing AgentPlaybook
guidance in the `SKILL.md` plus `references/` layout.

## Read

- `references/current-guidance.md` for the canonical layout, routing policy,
  stop conditions, and verification.
- The affected area entrypoints, such as `common/skills/.../SKILL.md`,
  `workflows/skills/.../SKILL.md`, `platforms/<platform>/skills/.../SKILL.md`,
  or `product-patterns/skills/.../SKILL.md`.

## Process

1. Add or update the small `SKILL.md` entrypoint first.
2. Move detailed examples, source maps, checklists, and version-sensitive
   material into directly linked reference files.
3. Keep legacy flat `.md` files as compatibility stubs only.
4. Update `index.md` and route canonicalization when the load target changes.
5. Validate links, route output, and docs-read behavior before reporting
   completion.

## Do Not

- Do not put full guidance back into a flat compatibility file.
- Do not create a bundle that merely duplicates long prose without reducing the
  default route context.
- Do not hide a required stop condition only in a deep reference.

## Verification

- `python3 scripts/workflow.py validate`
- A route smoke that should load the changed bundle and shows `SKILL.md` in
  `Read First` or `Reference On Demand` as appropriate for the task.
- `vibeguard audit . --rules .`
