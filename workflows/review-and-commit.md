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
3. Run or record the nearest useful verification.
4. Remove only unused code created by the change.
5. Split unrelated work before committing.
6. Write a commit message that states intent, context, and verification.

## Stop If

- The diff includes unrelated feature, refactor, generated, dependency, or release changes that can be split.
- Required verification failed and the failure is not understood.
- Secrets, local config, signing material, or private data appear in the diff.
- The commit message would need to hide uncertainty about product behavior,
  migration risk, security impact, or skipped checks.
