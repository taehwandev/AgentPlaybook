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
3. Give a compact alignment brief before editing: what the user and agent appear
   to understand the same way, what may differ, and which unsupported
   assumptions will be used by default unless a blocker question changes them.
4. Identify the smallest implementation boundary.
5. Record the boundary plan before editing: owned files/modules, affected
   caller-facing contracts, existing same-file scope or new package boundary,
   and the nearest verification that will prove the change.
6. Check repo-local instructions, existing patterns, affected contracts, and affected tests.
7. Implement only the requested behavior.
8. Update source-of-truth docs or record why docs are intentionally unchanged.
9. Verify with the nearest useful command or manual smoke check.
10. Run the side-effect audit from `workflows/development-cycle.md`.
11. Report what changed, how it was verified, and any residual risk.

## Pre-Code Packet

Before editing non-trivial code, record:

- acceptance criteria or observable outcome;
- alignment brief: same understanding, possible mismatch, and default
  assumption or blocker question;
- boundary plan: owner, scope, contracts, imports or same-file scope;
- test/check plan tied to that boundary;
- subagent/multi-agent split decision or the serial reason.

Do not start implementation when the boundary plan cannot name the owner,
caller contract, and verification path. Ask for clarification or reroute to
product/architecture work instead.

## Verification

Use the acceptance criteria and changed boundary to choose evidence:

- state or reducer test when user intent changes visible state
- component/UI/screenshot/manual path when visual or interaction behavior changes
- contract test, generated-client check, or caller compile when route/API/DTO
  behavior changes
- persistence/cache/sync check when durable state changes
- permission/auth/billing denied-path check when protected behavior changes
- platform adapter, lifecycle, cancellation, or cleanup check when OS/runtime
  integration changes

Do not report a feature complete when only happy-path rendering, mocked data, or
formatter/typecheck evidence ran for behavior that can fail at runtime.

## Stop If

- The requirement has multiple incompatible interpretations.
- The implementation needs product policy not present in the repo.
- PRD acceptance criteria or ARD ownership boundaries are missing for a
  non-trivial product change.
- Verification is impossible and the risk is not acceptable to state explicitly.
