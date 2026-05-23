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
- `common/verification-policy.md`
- `common/secure-development-baseline.md`
- `common/generated-files-policy.md`
- `common/dependency-policy.md` when packages or lockfiles changed
- matching platform security or review card from `index.md`

## Steps

1. Identify artifact, source revision, target environment, release owner, and rollback or forward-fix path.
2. Inspect final diff for secrets, local config, generated files, migrations, dependency churn, and contract changes.
3. Run required build, package, migration, signing, or smoke checks.
4. Verify tag, version, source revision, and artifact provenance match when tags
   are part of the release process.
5. Verify environment config, secret injection, callback URLs, app ids, domains, and package identity when relevant.
6. Record user-visible changes, breaking changes, security impact, operator action, and known residual risk.
7. Confirm post-release smoke, logs, monitoring, or health checks can detect failure.

## Stop If

- The release artifact or target environment is unclear.
- A migration, signing, secret, or deployment change lacks a recovery path.
- Required verification cannot run and no owner has accepted the release risk.
