---
keyflow_id: sys_release_readiness_workflow
status: review
type: human-reviewed-needed
---

# Release Readiness Workflow

Use before packaging, deploying, publishing, tagging, migration rollout,
signing, or handing off release-sensitive work.

## Read

- `common/release-deployment.md`
- `common/release-versioning.md`
- `common/commit-workflow.md` and `common/worktree-hygiene.md` when the release
  action creates, moves, pushes, or publishes a source-control tag or branch
- `common/ci-cd-automation.md` when workflow files, release automation,
  package publishing, deployment jobs, or CI gates are touched
- `common/deprecation-migration.md` when release work removes, renames,
  migrates, or changes compatibility
- `common/verification-policy.md`
- `common/secure-development-baseline.md`
- `common/generated-files-policy.md`
- `common/runtime-url-configuration.md` when runtime URLs, callback URLs,
  redirect URIs, webhook endpoints, CORS origins, or asset hosts vary by
  environment
- `common/dependency-policy.md` when packages or lockfiles changed
- matching platform security or review card from `index.md`

## Steps

1. Identify artifact, source revision, version scheme, target environment,
   release owner, and rollback or forward-fix path.
2. Inspect final diff for secrets, local config, generated files, migrations,
   dependency churn, and contract changes.
3. Run required build, package, migration, signing, or smoke checks.
4. Verify tag, version, source revision, and artifact provenance match when tags
   are part of the release process.
5. Verify environment config, secret injection, callback URLs, app ids, domains,
   and package identity when relevant.
6. Record user-visible changes, breaking changes, security impact, operator
   action, and known residual risk.
7. Confirm post-release smoke, logs, monitoring, or health checks can detect
   failure.
8. Confirm CI/CD gates, publish/deploy permissions, and rollback automation are
   scoped to the intended branch, tag, environment, or approval path.

## Release Orchestration Context

Treat a scoped release request as one release sequence, not as unrelated
requests for commit, review, packaging, tagging, and publishing. Once the
artifact, source revision policy, version/tag candidate, verification boundary,
publication action, and rollback or forward-fix path are known, carry that
release context through the substeps. Do not reclassify a commit-first,
review-first, package-first, or tag-push substep as broad product work solely
because the release sequence is mentioned.

Commit and code review still belong before releasing pending source changes,
but they must stay scoped to the intended commit unit. A review hook may flag a
pre-existing oversized function, file, or owner as structure evidence and
residual risk; it should force an immediate refactor only when the current diff
grows that unit, adds responsibility, changes public owner surface, or the
release cannot be verified without the split.

Evidence should be durable release evidence, not repeated prose reconstruction.
Prefer one release ledger that names the source revision, version/tag,
artifact, verification, publish boundary, and rollback/forward-fix path. Use
substep evidence for the commit, package, tag, and push only where it proves a
real release condition; do not create extra retrospective files for a receipt
path or wording correction unless the same gate fails again or the failure
reveals a reusable process bug.

## Verification

Release evidence should cover the artifact that will actually ship:

- source revision, version, tag, build number, package id, artifact name, and
  release channel agree
- build/package/sign/notarize/publish dry run or release command completed for
  the intended target
- migration, backfill, seed, generated artifact, or config change has rollback
  or forward-fix evidence
- secrets, env injection, callback URLs, app ids, domains, permissions, and
  signing material are supplied through the intended deployment mechanism
- smoke, health check, logs, metrics, crash reporting, or rollback monitor can
  detect the primary failure modes

Do not treat a local typecheck or formatter as release evidence when packaging,
deployment, signing, migration, or external configuration changed.

## Stop If

- The release artifact or target environment is unclear.
- The version scheme, reset rule, or version/tag/artifact relationship is
  unclear.
- A tag will be created, moved, pushed, or published but repo-local tag policy,
  current branch/remote, or worktree state has not been checked.
- A migration, signing, secret, or deployment change lacks a recovery path.
- Required verification cannot run and no owner has accepted the release risk.
