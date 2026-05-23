---
keyflow_id: sys_d1a668105819
status: draft
type: ai-generated
---

# Review And Commit Workflow

Use after implementation, before handing off or committing.

## Read

- `common/code-review.md`
- `common/change-size-policy.md`
- matching platform review card
- `common/commit-workflow.md`
- `common/commit-review.md` when reviewing existing commits
- `common/generated-files-policy.md` when generated files, lockfiles, or snapshots changed

## Steps

1. Inspect the final diff, not memory of the work.
2. Review against the user request, repo-local rules, service guide, and platform risks.
3. Run or record the nearest useful verification.
4. Remove only unused code created by the change.
5. Split unrelated work before committing.
6. Write a commit message that states intent, context, and verification.

## Commit Rule

One commit should carry one reviewable intent. Do not mix feature, refactor,
formatting, generated churn, and dependency changes unless they are inseparable.
