---
keyflow_id: sys_product_spec_to_implementation
status: review
type: ai-generated
---

# Product Spec To Implementation

Use when turning a product request, PRD, design note, or vague feature idea into implementation work.

## Start

- Identify the user outcome, not only the requested UI.
- Separate known facts, assumptions, and open decisions.
- Find repo-local product docs before inventing behavior.
- Ask only when ambiguity changes the result or risk.
- Use `workflows/ambiguity-gate.md` when an unknown might change behavior,
  architecture, security, release risk, or verification.

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
