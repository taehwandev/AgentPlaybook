---
keyflow_id: sys_planning_research_workflow
status: review
type: human-reviewed-needed
---

# Planning Research Workflow

Use when the task is to investigate, compare options, write an implementation
plan, assess risk, or prepare a recommendation before editing code.

## Read

- `workflows/agent-task-lifecycle.md`
- `common/architecture-selection.md` or `common/architecture-design.md` when structure is affected
- `common/product-spec-to-implementation.md` when behavior or acceptance criteria are unclear
- `common/security-privacy-review.md` when sensitive surfaces are involved
- platform or product-pattern cards from `index.md` for the affected domain

## Steps

1. State the question, decision, or plan outcome being produced.
2. Separate facts found locally, assumptions, unknowns, and user decisions.
3. Inspect existing code, docs, issues, tests, and conventions before proposing structure.
4. Identify affected boundaries, risks, and verification paths.
5. Prefer the smallest reversible plan that proves the goal.
6. Report recommended path, rejected alternatives, risks, and next concrete step.

## Evidence

Planning output should distinguish:

- observed local facts from repo files, docs, tests, commands, or source code
- external facts that were verified with current sources
- assumptions that need user or owner confirmation
- options rejected and the concrete tradeoff behind each rejection
- verification that would prove the recommended path during implementation

Do not present an implementation plan as settled architecture when the relevant
code, contracts, product policy, or external facts were not inspected.

## Stop If

- The plan would require product, legal, billing, security, or release policy that is not present.
- Current external information is required but cannot be verified.
- The recommendation depends on code or docs that have not been inspected.
