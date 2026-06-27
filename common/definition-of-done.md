---
keyflow_id: sys_definition_of_done
status: review
type: human-reviewed-needed
agentplaybook_card_contract: strict
---

# Definition Of Done

Use before final report, handoff, commit, release, or PR creation to decide
whether an agent task is actually complete.

The goal is to prevent "changed files" from being mistaken for done work.

## Use When

- A task created or changed code, docs, config, tests, workflows, generated
  artifacts, release metadata, or runtime instructions.
- A review needs a single completion checklist.
- A workflow route is about to finish.
- Verification was skipped, partial, mocked, or failed and residual risk must be
  reported.

For answer-only work, use the relevant planning or review output contract unless
the answer claims a verified state.

## Inspect First

- Current user request and any acceptance criteria.
- Route gates and finish-check evidence when a scripted route was used.
- Repo-local instructions, PRD/ARD, issue, design note, or source of truth.
- Final diff, changed files, generated artifacts, lockfiles, and config.
- Verification output and skipped-check reasons.
- User-owned dirty files that must not be included in the claim.

## Decision Rule

A task is done only when all required gates are satisfied, the changed surface
has matching evidence, and unresolved risk is either out of scope, explicitly
accepted, or clearly reported as not done.

If the route has required gates, every gate must be `🐱🟢 SUCCESS` before
completion. A missing or vague gate is `🐱🔴 FAIL`, not a warning.

## Done Checklist

| Area | Done Means |
| --- | --- |
| Request | The final behavior or artifact matches the user's current request, not an older interpretation. |
| Scope | Unrelated refactors, generated files, dependency changes, release changes, and user-owned dirty files are excluded or explicitly explained. |
| Requirements | Known facts, assumptions, open decisions, and non-goals are visible when behavior is non-trivial. |
| Architecture | New or changed boundaries have owners, allowed imports, forbidden imports, callers, and nearest verification when relevant. |
| Code | Implementation follows local style, avoids speculative abstractions, and keeps responsibilities reviewable. |
| Docs | Durable behavior, workflow policy, public contract, or operator action changes are reflected in the relevant docs. |
| Tests | The nearest useful automated or manual check ran, or the skip reason and residual risk are explicit. |
| Security | Secrets, private data, permissions, tenant, billing, and external-state risks were checked when touched. |
| Release | Packaging, migration, rollout, rollback, and monitoring are covered when release-sensitive work changed. |
| Report | The final response names what changed, what was verified, what was skipped, and what risk remains. |

## Common Rationalizations

| Rationalization | Required Response |
| --- | --- |
| "The diff looks right." | Run or report the nearest verification and inspect side effects. |
| "Tests passed, so docs are unnecessary." | Update docs when durable behavior, workflow policy, or public contracts changed. |
| "Only docs changed." | Still run frontmatter, link, route, or diff checks when available. |
| "The remaining issue is unrelated." | State the unrelated dirty file or failing check and why it is out of scope. |
| "The hook warned but the work is fine." | A required gate or hook failure must be recovered before completion. |

## Red Flags

- The final response says "done" but no command or manual scenario is named.
- A required route gate is missing or has evidence like "done" or "checked".
- The diff includes lockfiles, generated files, release config, or unrelated
  source files not mentioned in the request.
- A high-risk change has only format, lint, typecheck, or screenshot evidence.
- The task used a broad assumption but never showed the user the possible
  mismatch.
- A review or finish hook failed and the agent moved to summary anyway.

## Do Not

- Do not mark a task complete because a file was edited.
- Do not hide skipped tests, partial manual checks, or environment failures.
- Do not claim user-owned dirty files as part of your work.
- Do not finalize with unresolved required gate failures.
- Do not use screenshots, setup logs, config shape, or mocked payloads as proof
  of runtime behavior unless they exercise the changed behavior.
- Do not treat release, migration, deploy, credential, or paid-usage risk as
  complete without approval and recovery evidence.

## Stop If

- The target project, current request, source of truth, or required route gates
  are unclear.
- Required repo-local instructions or task docs are unavailable.
- A gate, hook, VibeGuard audit, test, build, or validation command failed and
  the failure is in scope.
- Verification cannot prove a high-risk change and no owner has accepted the
  residual risk.
- The final diff includes unrelated changes that must be split before handoff or
  commit.

## Verification

Use the verification card that matches the highest-risk changed surface. At
minimum, completion evidence should include:

- route gate status when a workflow route was used
- exact commands or manual scenarios run
- whether each check passed, failed, or was skipped
- final diff or side-effect audit result
- residual risk

For AgentPlaybook maintenance, `workflow.py validate`, the nearest unit tests,
`git diff --check`, review hook, finish-check, and VibeGuard audit are the usual
completion evidence.

## Report

Use a compact completion report:

```text
Changed:
- ...

Verified:
- PASS `command`: what it proved

Remaining risk:
- ...
```

If work is not complete, say what blocks completion and the safest next action.
