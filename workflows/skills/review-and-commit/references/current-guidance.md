---
keyflow_id: sys_d1a668105819
status: review
type: ai-generated
---

# Review And Commit Workflow

Use after implementation, before handing off or committing.

## Read

- `common/code-review.md`
- `common/change-size-policy.md`
- `common/worktree-hygiene.md`
- `workflows/development-cycle.md` for side-effect audit questions
- matching platform review card
- `common/commit-workflow.md`
- `common/commit-review.md` when reviewing existing commits
- `common/generated-files-policy.md` when generated files, lockfiles, or snapshots changed
- `common/api-contract-compatibility.md` when API, route, DTO, event, webhook, or fixture contracts changed
- `common/release-deployment.md` when packaging, deployment, signing, migration rollout, or release config changed

## Steps

1. Inspect the final diff, not memory of the work.
2. Use the Review Hook as the default final code-review gate when it is
   installed and applicable. Do not duplicate a full manual code review only to
   repeat hook checks.
3. Confirm boundary-plan evidence exists for code work, or record why the
   change had no code boundary.
4. Confirm affected docs are updated, or record why no docs changed.
5. Confirm side-effect audit evidence names the final diff and unexpected
   generated, lockfile, public-contract, external-state, formatting, or
   unrelated behavior.
6. Run or record the nearest useful verification.
7. Remove only unused code created by the change.
8. Split unrelated work before committing.
9. Confirm Commit Readiness Gate evidence from `common/commit-workflow.md`.
10. Discover repo-local policy before any branch creation, push, PR, tag, or
   release publication.
11. Write a commit message that states intent, context, and verification.

Run a targeted manual review only when the Review Hook is unavailable, fails,
does not cover the changed surface, or the task touches high-risk behavior that
requires human judgment beyond the hook: auth, permissions, data loss,
migrations, billing, release, deployment, public API compatibility, or broad
architecture changes.

## Verification

Before handoff or commit, confirm:

- every required scripted workflow gate is `🐱🟢 SUCCESS`
- VibeGuard or the repo-local safety gate passed when required
- Review Hook passed with code review evidence and docs freshness evidence, and
  it did not mutate the worktree or hide broad fixes inside the hook
- for code-work routes, Review Hook received boundary-plan and side-effect audit
  evidence from the actual route, not a generic "done" phrase
- if the Review Hook was unavailable or skipped, the final report explains the
  replacement review evidence and residual risk
- the nearest behavior, contract, build, or manual smoke check ran or the skip
  reason and residual risk are explicit
- `git diff --check` or repo formatter/lint covered whitespace or formatting
  when documentation/code formatting changed
- staged diff matches the intended commit scope when a commit is being created
- Commit Readiness Gate evidence is satisfied
- external-state targets are discovered from repo-local policy before branch
  creation, push, PR, tag, release, or deploy

Do not commit based on memory. Review the exact staged diff and verification
evidence that will be represented by the commit message.

## Output

Report changed files or commit SHA, verification results, skipped checks,
remaining risk, and any intentionally unstaged or unrelated user-owned changes.

## Stop If

- The diff includes unrelated feature, refactor, generated, dependency, or release changes that can be split.
- The Review Hook reports that the changed path count is too broad for one
  review pass.
- The review requires a fix larger than the current scoped task; start a
  separate routed task instead of folding the update into review.
- Required verification failed and the failure is not understood.
- Secrets, local config, signing material, or private data appear in the diff.
- The commit message would need to hide uncertainty about product behavior,
  migration risk, security impact, or skipped checks.
- The correct base branch, PR target, release branch, or tag target is ambiguous
  and the next action would mutate git history or remote state.
