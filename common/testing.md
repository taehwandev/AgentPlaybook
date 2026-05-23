---
keyflow_id: sys_4d909f6cacff
status: review
type: ai-generated
---

# Testing Principles

Test behavior users or other code depend on.

## Prioritize

1. Product rules and permissions
2. Data mapping and API contracts
3. State transitions and errors
4. Critical user flows
5. Bug regressions

## Cover

- success
- loading
- empty
- permission denied
- validation error
- API/network error
- boundary values, including zero, minimum, maximum, overflow, malformed,
  stale, duplicated, cancelled, and unavailable inputs

## Prefer

- Unit tests for pure policy, mapper, validator logic.
- State tests for ViewModel, hook, reducer, store.
- UI tests by visible text, role, label, and interaction.
- E2E only for high-value cross-boundary flows.

## Isolation

- Mock at external boundaries: network, database, filesystem, clock, random,
  payment, email, analytics, and platform APIs.
- Prefer deterministic fixtures and builders over copied production payloads.
- Keep fixtures close to the test or shared contract they prove.
- Do not weaken assertions only to make a flaky test pass; identify the unstable
  boundary first.
- Test permission, tenant, billing, migration, and generated-client contracts at
  the boundary where they can actually fail.

## Report

If a test cannot run, state the command skipped, why, and residual risk.
