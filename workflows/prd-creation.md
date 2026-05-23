---
keyflow_id: sys_prd_creation_workflow
status: review
type: human-reviewed-needed
---

# PRD Creation Workflow

Use when the deliverable is a PRD or product requirements note before ARD,
implementation, tests, or release planning.

For agent execution, prefer the scripted route:

```text
python3 <AGENTPLAYBOOK_ROOT>/scripts/workflow.py route prd --platform <platform> --concern <concern>
```

Use `workflows/product-architecture-delivery.md` only when the work continues
from PRD into ARD and code.

## Read

- target repo-local agent instructions and product docs
- `workflows/ambiguity-gate.md`
- `common/product-spec-to-implementation.md`
- matching platform, product-pattern, security, data, accessibility, or release
  cards when those surfaces shape the PRD

## Steps

1. Source of truth: read the request, repo-local instructions, current product
   docs, issue, design note, or existing PRD before writing new requirements.
2. Ambiguity check: classify unknowns as blocker, researchable, assumable, or
   out-of-scope. Ask only when the answer can change behavior, risk, or
   verification.
3. Actor and outcome: name the user or system actor and the outcome that should
   change.
4. Scope: define what is in scope, explicitly out of scope, and what should not
   change.
5. States and surfaces: cover success, loading, empty, error, permission denied,
   offline, conflict, rollback, data, auth, permission, billing, privacy,
   external services, and release impact when relevant.
6. Acceptance criteria: write testable criteria before ARD or code. Prefer
   Given/When/Then when behavior has clear inputs and outcomes.
7. Open decisions: name decisions that block ARD, implementation, security,
   data, release, or verification.
8. Handoff: state where the PRD lives, what evidence was used, and the next
   recommended route: `product`, `planning`, `ambiguity`, or stop.

Show a gate signal after each completed step when using a scripted route.

## Output

Use this shape unless the target repo has a PRD template:

```text
PRD:
- User or actor:
- Desired outcome:
- Current behavior:
- Proposed behavior:
- In scope:
- Out of scope:
- States:
- Data/auth/permission/billing/privacy/external surfaces:
- Acceptance criteria:
- Open decisions:
- Verification signals:
- Next route:
```

## Stop If

- The PRD would invent product, legal, billing, security, or data policy not
  present in the target repo.
- Acceptance criteria cannot be made testable without a blocker answer.
- The request is already implementation-ready and a lightweight note is enough.
- The agent cannot identify the target project or source of truth.
