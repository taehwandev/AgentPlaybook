---
keyflow_id: sys_release_deployment
status: review
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
- Release notes should mention user-visible changes, migrations, breaking
  changes, security impact, and required operator action.
- Never print or commit deployment secrets, signing material, or generated
  production config.
- Release tags should identify the exact source revision used to build and
  publish artifacts, not just the latest branch head.
- Version schemes should follow `common/release-versioning.md` and the
  repo-local release contract.

## Versioning

Before choosing or changing a release version, read
`common/release-versioning.md`.

Do not impose one calendar versioning scheme across unrelated projects. The
shared rule is to choose a documented scheme per artifact and keep it stable:

- SemVer for compatibility-sensitive libraries, APIs, SDKs, generated clients,
  plugins, or packages.
- Monthly CalVer for apps, services, and date-oriented product releases.
- Weekly CalVer only for real weekly release trains or operations cadences.

## Tag And Artifact Ownership

When a release uses source-control tags:

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
