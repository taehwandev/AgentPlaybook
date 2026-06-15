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
2. Review against the user request, repo-local rules, project/product guidance,
   platform risks, and side-effect audit questions.
3. Confirm affected docs are updated, or record why no docs changed.
4. Run or record the nearest useful verification.
5. Remove only unused code created by the change.
6. Split unrelated work before committing.
7. Write a commit message that states intent, context, and verification.

## Verification

Before handoff or commit, confirm:

- every required scripted workflow gate is `🐱🟢 SUCCESS`
- VibeGuard or the repo-local safety gate passed when required
- Review Hook passed with code review evidence and docs freshness evidence
- the nearest behavior, contract, build, or manual smoke check ran or the skip
  reason and residual risk are explicit
- `git diff --check` or repo formatter/lint covered whitespace or formatting
  when documentation/code formatting changed
- staged diff matches the intended commit scope when a commit is being created

Do not commit based on memory. Review the exact staged diff and verification
evidence that will be represented by the commit message.

## Output

Report changed files or commit SHA, verification results, skipped checks,
remaining risk, and any intentionally unstaged or unrelated user-owned changes.

## Stop If

- The diff includes unrelated feature, refactor, generated, dependency, or release changes that can be split.
- Required verification failed and the failure is not understood.
- Secrets, local config, signing material, or private data appear in the diff.
- The commit message would need to hide uncertainty about product behavior,
  migration risk, security impact, or skipped checks.
