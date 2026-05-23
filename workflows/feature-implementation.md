---
keyflow_id: sys_0086dc0e66ec
status: review
type: ai-generated
---

# Feature Implementation Workflow

Use when implementing a scoped feature slice or meaningful behavior change after
the product front matter is known.

Do not use this workflow to skip PRD and ARD. If the request is broad app,
product, multi-screen, data, route, contract, auth, billing, release, or
architecture work, use `workflows/product-architecture-delivery.md` first and
return here only for the ARD-scoped code slice.

## Read

- `common/agent-operating-skill.md`
- `common/llm-coding-discipline.md`
- `common/code-conventions.md`
- `common/product-spec-to-implementation.md`
- `workflows/product-architecture-delivery.md` when PRD and ARD gates are needed
- `workflows/development-cycle.md` for the full verify and side-effect audit cycle
- one matching platform architecture card
- task-specific common cards for touched API contracts, release config,
  accessibility, persistence, security, dependencies, or generated files

## Steps

1. Check whether the request needs PRD/ARD gates. If yes, stop this route and
   reroute to `product`.
2. Restate the requested behavior and assumptions.
3. Identify the smallest implementation boundary.
4. Check repo-local instructions, existing patterns, affected contracts, and affected tests.
5. Implement only the requested behavior.
6. Verify with the nearest useful command or manual smoke check.
7. Run the side-effect audit from `workflows/development-cycle.md`.
8. Report what changed, how it was verified, and any residual risk.

## Stop If

- The requirement has multiple incompatible interpretations.
- The implementation needs product policy not present in the repo.
- PRD acceptance criteria or ARD ownership boundaries are missing for a
  non-trivial product change.
- Verification is impossible and the risk is not acceptable to state explicitly.
