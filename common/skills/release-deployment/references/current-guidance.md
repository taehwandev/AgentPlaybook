---
keyflow_id: sys_release_deployment
status: stable
type: human-reviewed-needed
---

# Release Deployment

Use when packaging, deploying, publishing, migrating, signing, tagging, creating
release notes, changing environment config, or preparing rollback-sensitive work.

## Default

A release is not complete because the build succeeded. It needs a clear artifact,
environment, verification gate, and rollback or forward-fix path.

## Separate

- Build artifact
- Runtime configuration
- Secrets and credentials
- Database or storage migration
- Feature flag or rollout policy
- Deployment action
- Post-release smoke and monitoring
- Rollback or forward-fix plan

## Rules

- Keep local, development, staging, and production configuration separate.
- Do not hard-code environment behavior that should be injected by deployment,
  release config, or local config.
- Use `runtime-url-configuration.md` when API origins, callback URLs, redirect
  URIs, webhook endpoints, CORS origins, app link hosts, or asset/CDN hosts vary
  by release environment.
- Verify signing, credentials, package identity, bundle id, domain, callback URL,
  or app id before release when applicable.
- Make migrations backward compatible when old and new app versions can overlap.
- Run destructive migrations only with a rollback, restore, or forward-fix plan.
- Feature flags need an owner, default, rollout condition, monitoring signal, and
  cleanup plan.
- CI/CD automation should separate build, test, package, publish, deploy, and
  smoke stages enough that failures are diagnosable and rollback remains
  realistic. Use `common/skills/ci-cd-automation/SKILL.md` when automation changes.
- Deprecation, migration, or removal work needs compatibility mode, migrated
  callers, docs, and zero-usage or rollback evidence. Use
  `common/skills/deprecation-migration/SKILL.md` when release behavior removes or replaces a
  path.
- Release notes should mention user-visible changes, migrations, breaking
  changes, security impact, and required operator action.
- Never print or commit deployment secrets, signing material, or generated
  production config.
- Release tags should identify the exact source revision used to build and
  publish artifacts, not just the latest branch head.
- Version schemes should follow `common/skills/release-versioning/SKILL.md` and the
  repo-local release contract.

## Versioning

Before choosing or changing a release version, read
`common/skills/release-versioning/SKILL.md`.

Do not impose one calendar versioning scheme across unrelated projects. The
shared rule is to choose a documented scheme per artifact and keep it stable:

- SemVer for compatibility-sensitive libraries, APIs, SDKs, generated clients,
  plugins, or packages.
- Weekly CalVer `YY.WW.N` for date-based release tags and operational
  artifacts: two-digit year, ISO week, and release count starting at `1`.
- Monthly CalVer only when the repo-local release contract explicitly says the
  release unit is month-based.

Do not use four-digit years such as `2026.27.1` for CalVer release tags; use
`26.27.1` or `v26.27.1` according to the repo-local tag prefix policy.

## Tag And Artifact Ownership

When a release uses source-control tags:

- Treat tag creation, tag movement, and tag push as release-sensitive
  source-control operations. Read the release readiness, release deployment,
  release versioning, commit workflow, and worktree hygiene guidance before
  mutating a local or remote tag; version naming guidance alone is not enough.
- Create or move the tag only after the intended release revision has passed the
  required source and artifact verification.
- Keep the tag on the revision used to build the published artifacts.
- Do not move a prior release tag to a later commit for documentation, workflow,
  or unrelated follow-up reasons.
- If a post-release fix changes behavior or artifacts, publish a new version or
  release candidate instead of moving the old tag.
- If a post-release fix changes only process or documentation, commit it after
  the release tag and leave the tag where it is.
- Do not overwrite, force-push, or republish an existing public release without
  explicit approval and a clear correction note.
- For annotated tags, verify the peeled commit target, not only the tag object.

## Direct Push And Tags

Repo-local release policy decides whether a release uses PR merge, direct push,
release branch, or tag. Shared guidance must not choose that model.

When a web repo documents direct push to the default branch as the production
release path, treat that push as release publication. Create or require a tag
for the exact source revision only when repo-local policy requires tags or tags
are the only durable release record.

Do not tag when the push is only preview or staging, the version/tag scheme is
unknown, release provenance is missing, or release readiness evidence has not
passed.

## Release Gate

Before release, confirm:

- source revision and artifact version are known
- release tag, package version, and artifact provenance point to the same source
  revision when tags are used
- required tests, builds, or smoke checks passed or have accepted risk
- config and secret injection happened in the intended environment
- monitoring, logs, crash reports, or health checks can show failure
- rollback or forward-fix path is realistic for the changed surface

## Post-Release Check

Verify the most important user or system path after release. If verification is
manual, record exactly what was checked and what was not checked.
