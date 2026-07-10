---
keyflow_id: sys_common_doc_conventions
status: stable
type: human-reviewed
---

# Document Conventions

Output path and naming rules for generated documents (PRD, spec, ARD).
An agent must follow these rules when creating documents, unless the target
repo's own instructions override them. Repo-local rules always win.

## Core Rule: Feature Folder

PRD, spec, ARD are a trio for one feature. Keep them together.

```
docs/
└── <feature-name>/
    ├── prd.md     ← required: product requirements (always project-level)
    ├── spec.md    ← optional: technical specification
    └── ard.md     ← optional: architecture decision record
```

## Module-level Docs

When a project is modularized, each module can have its own implementation docs
inside the module directory. PRD is never at module level — it is always
at the project root because it describes user-facing requirements, not internals.

```
<module-name>/
└── docs/
    └── <feature-name>/
        ├── spec.md    ← module implementation spec
        └── ard.md     ← module architecture decision
```

When a feature spans multiple modules, the spec and ARD belong at project level
(`docs/<feature-name>/`), not inside a single module.

## Scope Placement Matrix

Use the project-level row when the feature is cross-module, user-facing across
boundaries, or not clearly owned by one module. Use the single-module row only
after confirming the spec or ARD is implementation detail for that module.

| Scope | `prd.md` | `spec.md` | `ard.md` |
| --- | --- | --- | --- |
| Project-level or cross-module feature | `docs/<feature-name>/prd.md` | `docs/<feature-name>/spec.md` | `docs/<feature-name>/ard.md` |
| Single-module implementation detail | `docs/<feature-name>/prd.md` when user-facing; otherwise no PRD | `<module-name>/docs/<feature-name>/spec.md` | `<module-name>/docs/<feature-name>/ard.md` |

## When Each Document Is Required

| Document | Write when |
|----------|------------|
| `prd.md` | Any user-facing feature or behavior change |
| `spec.md` | Technical decisions span multiple files, modules, or services |
| `ard.md` | Architecture approach is non-obvious or has meaningful trade-offs |

Small features may only need `prd.md`. Do not create empty placeholder docs.

## Naming Rules

- Feature folder: `kebab-case`, describe the feature not the type
- Add date prefix only when no stable feature name exists: `2026-07-10-<topic>/`
- File names are fixed: `prd.md`, `spec.md`, `ard.md` — no date in filenames
- Module name: follow the target repo's existing module naming convention

## Handoff Rule

When creating any document, the agent must state the file path in the handoff.
State path, status (`draft` / `review` / `stable`), and the next recommended
step (`review`, `implement`, `stop`).

## Override Order

1. Target repo `AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md` doc paths
2. This skill (`common/skills/doc-conventions/SKILL.md`)
