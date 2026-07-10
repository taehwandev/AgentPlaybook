---
keyflow_id: sys_product_spec_to_implementation
status: stable
type: ai-generated
---

# Product Spec To Implementation

Use when turning a product request, PRD, design note, or vague feature idea into implementation work.

## Start

- Identify the user outcome, not only the requested UI.
- Separate known facts, assumptions, and open decisions.
- Find and open repo-local PRD, spec, ARD, issue, design note, task doc, or
  product source-of-truth before inventing behavior or editing code.
- Treat this as a pre-edit hard gate. Do not implement first and reconstruct
  the PRD/spec/ARD search afterward.
- Ask only when ambiguity changes the result or risk.
- Use `workflows/skills/ambiguity-gate/SKILL.md` when an unknown might change behavior,
  architecture, security, release risk, or verification.

If no product source exists and the work introduces a new capability, flow,
multi-screen behavior, data model, API contract, auth/permission/billing policy,
release behavior, or durable acceptance criteria, create or update a PRD/spec
before implementation. If the work is a narrow slice that can proceed without a
PRD, record the PRD-skip reason and the acceptance criteria source.

## Define The Contract

Write acceptance criteria before coding when behavior is non-trivial.

```text
Given ...
When ...
Then ...
```

Cover success, empty, error, permission denied, and rollback/conflict states when relevant.

## Break Down Work

- Product contract
- Data model or API contract
- UI state and interaction
- Permission or entitlement rules
- Tests and verification
- Migration or compatibility needs

## Guardrails

- Do not hide a missing product decision inside a boolean or fallback.
- Do not ship UI copy that implies server capability before the backend exists.
- Keep project-specific role names, commands, and domain terms in the repo.
- Prefer one narrow vertical slice over broad speculative scaffolding.

## Done

Implementation, tests, and docs all point to the same contract. Any deferred decision is explicit.
