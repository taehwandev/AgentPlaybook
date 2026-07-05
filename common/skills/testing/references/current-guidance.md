---
keyflow_id: sys_4d909f6cacff
status: review
type: ai-generated
---

# Testing Principles

Use when choosing, adding, reviewing, or reporting tests, fixtures, snapshots,
manual smoke checks, or verification evidence.

When writing or meaningfully reviewing test code, also open
`common/scenario-driven-testing.md`. Test cases should be framed as actor
scenario -> action -> response condition -> observable success, failure,
exception, or recovery result before dropping down to framework-specific
Arrange/Act/Assert code.

Test behavior users or other code depend on.

## Decision Rule

Choose the smallest test that can fail for the behavior being changed. Broaden
only when the risk crosses a boundary that the smaller test cannot see.

Do not add a test only because a file changed. Add or update a test when the
change affects a product rule, public contract, state transition, mapper,
permission, persistence, cache, platform adapter, release behavior, or known
regression.

## Test-First

Use test-first when the expected behavior is clear enough to name before
implementation. Design the scenario and the smallest failing test before
changing production code, then implement only enough code to pass that test and
the adjacent regression checks.

Test-first is not a reason to guess missing product behavior. If the expected
outcome, permission rule, data-loss rule, migration behavior, or error copy is
unclear, clarify the source of truth before writing the test.

For bug fixes, reproduce the failure with a focused failing test when practical.
For new behavior, write the test against the public boundary or state transition
the caller depends on, not private implementation steps.

## Unit Test F.I.R.S.T. Check

When adding or reviewing unit tests, check that they are:

- Fast: narrow enough to run during normal local development.
- Isolated: independent from other tests and external mutable state.
- Repeatable: deterministic across machines, time, order, locale, and network
  availability.
- Self-validating: assertions decide pass or fail without manual log inspection.
- Timely: written before or alongside the production change while the expected
  behavior is still explicit.

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

## Match Test To Boundary

| Changed boundary | Preferred evidence |
| --- | --- |
| Pure function, mapper, parser, formatter, policy | Unit test with normal, missing, invalid, boundary, and duplicate cases |
| State owner, reducer, ViewModel, hook, store | Transition test for action -> state/effect, including failure and retry |
| UI component or screen | Component/UI test, preview, screenshot, or manual path for visible states and user intent |
| API route, DTO, event, webhook, generated client | Contract or request/response test plus affected caller check |
| Persistence, cache, migration, sync | Read/write/update/delete, stale data, invalidation, rollback, or compatibility check |
| Permission, auth, tenant, billing, privacy | Allowed and denied paths, stale/revoked state, and boundary enforcement |
| Platform, filesystem, shell, browser, SDK, background work | Adapter test, fake integration, lifecycle/cancellation check, or manual smoke path |
| Release, package, signing, deployment | Dry run, build/package check, staging/manual smoke, or rollback note |

## Isolation

- Mock at external boundaries: network, database, filesystem, clock, random,
  payment, email, analytics, and platform APIs.
- Prefer deterministic fixtures and builders over copied production payloads.
- Keep fixtures close to the test or shared contract they prove.
- Do not weaken assertions only to make a flaky test pass; identify the unstable
  boundary first.
- Test permission, tenant, billing, migration, and generated-client contracts at
  the boundary where they can actually fail.

## Stack Discovery For Tests

Before adding a test in an unfamiliar repo, discover the existing test stack:
unit framework, integration harness, UI framework, screenshot/snapshot tooling,
dependency injection, mocking/fake style, device/browser/runtime runner, and E2E
scope. Prefer the repo's existing framework and fake patterns before introducing
new test libraries or broad mocks.

For UI changes, cover the states and form factors affected by the change:
common, loading, empty, error, disabled/read-only, permission denied, long text,
theme, font scale, and the relevant screen or window sizes. Use screenshots or
previews only when they prove the changed visual contract; pair them with
focused assertions for behavior.

## Do Not

- Do not replace a missing high-risk test with a formatter, typecheck, or
  snapshot update.
- Do not snapshot broad output when a focused assertion would explain the
  behavior.
- Do not mock the unit under test so deeply that the product rule cannot fail.
- Do not add fixtures copied from private production data.
- Do not mark behavior verified when only mocked, placeholder, or happy-path
  behavior ran.

## Common Rationalizations

| Rationalization | Required Response |
| --- | --- |
| "The change is small." | Check whether the risk is small; add the nearest test when a contract or state transition changed. |
| "The compiler passed." | Compiler success does not prove behavior, permissions, persistence, UI, or release paths. |
| "Manual testing is faster." | Record the manual scenario and add automated coverage when the risk is recurring or high. |
| "The existing test is flaky." | Diagnose the unstable boundary; do not weaken assertions to get a pass. |

## Red Flags

- A behavior change has only formatting, lint, or typecheck evidence.
- A high-risk path is tested only through mocks of the unit under test.
- A snapshot update hides a product or layout change without a focused
  assertion.
- Tests cover the happy path but omit error, empty, permission, stale, or
  unavailable states that the changed boundary can produce.

## Report

For automated checks, report command, result, and what boundary it proved. For
manual checks, report scenario, environment, action, expected result, and
observed result.

If a test cannot run, state the command skipped, why, and residual risk.
