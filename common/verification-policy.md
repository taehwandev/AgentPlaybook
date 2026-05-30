---
keyflow_id: sys_verification_policy
status: review
type: human-reviewed-needed
---

# Verification Policy

Work is not done just because files changed. Completion requires evidence or a
clear explanation of why evidence could not be collected.

## Verification Order

Prefer the smallest reliable check first:

```text
format / static check
typecheck / compile
unit test
focused integration test
UI or end-to-end test
manual smoke test
package / release check
```

Run broader checks when the change touches shared models, cross-module
contracts, API or schema compatibility, persistence, auth, permissions,
payments, filesystem, network, accessibility-critical UI, platform integration,
deployment, migration, or release packaging.

## Choose Checks By Change Type

Use repo-local commands and names. This table defines the minimum evidence shape,
not exact command strings.

| Change type | Minimum verification |
| --- | --- |
| Documentation only | markdown/frontmatter/link check when available, plus whitespace or diff check |
| Formatting only | formatter or diff check, and confirm behavior files were not unintentionally changed |
| Copy or labels | locale/message parity when applicable, plus affected UI or snapshot check when text can overflow |
| Pure refactor | nearest tests for the moved or extracted behavior; typecheck/build when exported contracts changed |
| Runtime behavior | targeted unit, integration, or component test; manual smoke for the affected user/API path when no test exists |
| Boundary value mapping | normal, missing, invalid, lower bound, upper bound, stale, duplicate, and unavailable cases for the parser, mapper, or adapter |
| Shared module, API, schema, or DTO | caller-focused tests plus contract, serialization, or compatibility check |
| UI layout or interaction | component or browser check for main interaction, loading, empty, error, disabled, and responsive states as relevant |
| Auth, permissions, tenant, billing, or privacy | allowed and denied paths; stale, revoked, or invalid input path when relevant |
| Persistence, cache, sync, or migration | write/read/update/delete or load/save path; invalidation, stale data, rollback, or backward compatibility note |
| External integration, background job, filesystem, network write, release, or deploy | dry run, sandbox, staging, or explicit approval path; idempotency or rollback evidence when applicable |

If a change fits multiple rows, use the highest-risk applicable row.

## Risk Levels

- Low: docs, comments, isolated copy, or mechanical formatting. A narrow static
  check may be enough.
- Medium: local component, hook, utility, route, or command behavior. Run the
  nearest targeted automated check when available.
- High: auth, permissions, billing, personal data, persistence, cache,
  migration, public API, external state, platform integration, release, or
  shared contract. Use targeted tests plus a contract, integration, manual
  scenario, or explicit residual-risk report.

High-risk work is not complete with only a formatter, linter, typecheck, or
successful page load.

## Evidence To Preserve

In the final response, include:

- exact command names for automated checks
- whether each check passed, failed, or was not run
- a short reason for skipped checks
- residual risk when verification is partial
- workflow gate ledger status when a scripted route was used

Prefer this compact format when multiple checks were run:

```text
Verified:
- PASS `command`: what it proved
- FAIL `command`: failure summary and next action
- SKIP `command`: why it was skipped and residual risk
```

For manual checks, name the user path, environment, input, and observed result.
Do not report screenshots, logs, or smoke checks as proof unless they exercise
the changed behavior.

When a scripted route was used, every route gate must have evidence before the
work is reported complete. If a required gate was not executed, follow missed
gate recovery instead of reporting completion.

Traffic-light gate status is part of verification:

- `🐱🔵 PENDING`: not reached yet.
- `🐱🟢 GREEN`: executed with evidence.
- `🐱🟡 YELLOW`: blocked or paused; completion cannot be claimed.
- `🐱🔴 RED`: missed or missing evidence after the gate should have run; follow
  missed-gate recovery.

Before final report, commit, release, or handoff, every required gate must be
`🐱🟢 GREEN`.

Manual evidence should be specific:

```text
Manual:
- Scenario: unauthenticated user opens protected resource
- Environment: local browser, desktop viewport
- Action: visit the protected URL
- Expected: login or denied state
- Observed: redirected to login with the original destination preserved
```

## When Tests Are Missing

If no useful test exists:

- add a focused test when the change is risky enough
- otherwise perform a manual smoke check
- state that automated coverage is missing
- do not replace a missing high-risk test with a weaker assertion merely to make
  the check pass

## When Commands Fail

Use `common/tool-failure-recovery.md`. A failed command is evidence, not a
reason to guess. Read stdout/stderr, identify the failing file, line, error code,
or test name, make the smallest relevant correction, and rerun the narrowest
proving command. Do not repeat the same command blindly or downgrade assertions
only to make the check pass.

## Do Not Overclaim

Do not say a feature is complete when:

- behavior is mocked or placeholder-only
- the user path was not exercised
- persistence or sync-back was not verified
- auth, permissions, or data loss cases are untested
- only formatting or compilation was checked for a behavioral change
- UI visibility was checked but the protected command or trusted boundary was not
  exercised
- boundary-dependent behavior was checked only with normal input
- an API response, DTO, migration, cache, or generated artifact changed without a
  compatibility or consumer check
- a visual snapshot was updated without stating the product reason
- tests were skipped only because they were slow, broad, or inconvenient
- generated files changed and their inclusion in the task was not confirmed
