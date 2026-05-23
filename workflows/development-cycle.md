---
keyflow_id: sys_development_cycle_workflow
status: review
type: human-reviewed-needed
---

# Development Cycle Workflow

Use for multi-step implementation work from request intake through handoff. This
is the default workflow when the task is larger than a one-line edit.

The goal is one complete cycle: understand the request, make the smallest useful
change, verify the changed surface, audit side effects, and report evidence.

When this cycle is reached from `scripts/workflow.py`, treat the script output as
the command manifest and keep the implementation inside its listed gates.

## Read

- `common/agent-operating-skill.md`
- `common/llm-coding-discipline.md`
- `common/code-conventions.md`
- `common/change-size-policy.md`
- `common/worktree-hygiene.md` when the checkout already contains changes
- one matching platform architecture card from `index.md`
- task-specific concern cards from `index.md`

## Phases

1. Orient: identify target repo, repo-local rules, current user changes, affected
   surface, and existing verification commands.
2. Scope: name the requested behavior, acceptance criteria, non-goals, and the
   smallest safe slice.
3. Design: choose state, domain, data, platform, contract, and security
   boundaries. Name likely side-effect surfaces before editing.
4. Implement: change only the scoped files and keep generated, dependency,
   formatting, and release churn separate when possible.
5. Verify: run the narrowest reliable check that proves the changed surface.
6. Side-effect audit: inspect the final diff and affected call paths for behavior
   outside the requested slice.
7. Broaden only if needed: run wider checks when the narrow check cannot cover
   shared contracts, auth, persistence, platform integration, release, or user
   flow risk.
8. Handoff: report changed files, verification evidence, skipped checks, side
   effects considered, and residual risk.

## Minimum Verification

Pick the closest check to the changed boundary first:

- Docs/config only: formatting, link/path sanity, `git diff --check`, or repo
  docs build when available.
- Pure logic: focused unit test for the changed function, mapper, policy, parser,
  validator, or reducer.
- Boundary mapping: normal, invalid, missing, stale, duplicated, lower bound,
  and upper bound cases for the changed parser, mapper, adapter, or reducer.
- Type/interface changes: compile, typecheck, generated client check, or contract
  test for the changed module.
- UI/state change: focused state test, component/screen test, screenshot/layout
  check, or manual smoke path for the changed state.
- API/route/event change: request/response contract test, route/deep-link test,
  fixture parity check, or affected client compile/typecheck.
- Persistence/migration/sync change: migration, load/save, corrupted data,
  stale-write, retry, and cleanup check closest to the storage boundary.
- Security/auth/permission change: denied access, stale session, revoked
  permission, cross-tenant, and secret/log leak check where applicable.
- Release/deployment change: package, dry run, staging smoke, signing/config
  check, or rollback/forward-fix note.

Minimum verification is acceptable only when it proves the changed boundary. If
it does not, name the gap and either run the next wider check or report the
residual risk explicitly.

## Side-Effect Audit

After verification, inspect the final diff and ask:

- Did any file change outside the scoped owner boundary?
- Did formatting, generated files, lockfiles, dependency updates, or release files
  change unexpectedly?
- Did any public API, DTO, route, event, schema, storage format, or fixture change?
- Did any external, persisted, generated, cached, or user-provided value cross a
  boundary without validation?
- Did auth, permission, tenant, billing, privacy, logging, analytics, or secret
  handling change?
- Did state ownership, cache invalidation, lifecycle, background work, or cleanup
  behavior change?
- Did UI text, accessibility, localization, focus order, empty/error states, or
  responsive layout change?
- Did repo-local commands, build config, environment config, package identity,
  signing, or deployment behavior change?
- Can the change be reverted without removing unrelated behavior?

If the answer is yes, either verify that surface, split the change, or report the
remaining risk.

## Route To

- New feature or behavior: `workflows/feature-implementation.md`
- Bug, regression, or flaky behavior: `workflows/bugfix-debugging.md`
- Behavior-preserving cleanup: `workflows/refactor-cleanup.md`
- Release, package, deployment, or migration handoff: `workflows/release-readiness.md`
- Final review or commit: `workflows/review-and-commit.md`

## Stop If

- The target repo or product contract is ambiguous enough to change the result.
- The requested slice mixes unrelated behavior, refactor, dependency, generated, and release work.
- Verification cannot cover a risky change and the residual risk is not acceptable to state.
- The side-effect audit finds unrelated changes that should be split before
  handoff or commit.
