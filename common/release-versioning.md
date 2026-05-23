---
keyflow_id: sys_release_versioning
status: review
type: human-reviewed-needed
---

# Release Versioning

Use when choosing, changing, reviewing, tagging, or documenting a release,
deployment, package, app, build, or artifact version.

## Default

Versioning is an artifact-local contract. Do not force one calendar scheme
across unrelated projects. Do choose one scheme for each released artifact,
document it in the repo-local release instructions, and keep it stable.

The shared default is:

- Use SemVer for libraries, SDKs, APIs, plugins, generated clients, and packages
  where compatibility expectations matter.
- Use monthly CalVer for apps, services, internal tools, and operational
  artifacts when date-oriented releases are useful.
- Use weekly CalVer only when the project has a real weekly release train or
  operational cadence.

## Supported Schemes

### SemVer

Use `MAJOR.MINOR.PATCH` when consumers need compatibility signals.

```text
2.4.7
2.5.0-rc.1
```

- Increment `MAJOR` for breaking changes.
- Increment `MINOR` for backward-compatible features.
- Increment `PATCH` for backward-compatible fixes.
- Prefer SemVer when package managers, app stores, or dependency resolvers
  expect SemVer semantics.

### Monthly CalVer

Use `YY.MM.N` for product, app, service, or deployment releases organized by
month.

```text
26.05.1
26.05.2
26.06.1
```

- `YY` is the two-digit year.
- `MM` is the release month.
- `N` starts at `1` each month and increments for each released artifact or
  production deployment, as defined by the repo.
- This is the preferred date-based scheme when there is no weekly release train.

### Weekly CalVer

Use `YY.WW.N` only when releases are planned, reported, or operated by week.

```text
26.21.1
26.21.2
26.22.1
```

- `WW` should be the ISO week unless the repo explicitly documents another
  calendar.
- `N` starts at `1` each week and increments for each released artifact or
  production deployment, as defined by the repo.
- Document the timezone used to decide the release week.

## Required Repo-Local Contract

Every repo that uses calendar or custom versioning must document:

- scheme name: `semver`, `calver-monthly`, `calver-weekly`, or custom
- pattern and examples
- timezone or calendar source for date-based versions
- whether `N` counts published artifacts, production deployments, or public
  release attempts
- reset rule for `N`
- tag prefix, such as `v26.05.1`, and whether package metadata omits `v`
- prerelease format, such as `26.05.1-rc.1`
- build metadata or monotonic build number when stores or platforms require it

## Rules

- Do not mix `YY.MM.N` and `YY.WW.N` for the same artifact.
- Do not switch schemes without a migration note and release owner approval.
- Do not infer month versus week from shape alone; read the repo-local contract.
- Use UTC for date-based versions unless repo-local release policy names another
  timezone.
- Decide whether the date comes from release cut, artifact publication, or
  production deployment, and keep that rule stable.
- Do not count failed builds, failed deploy attempts, or unpublished artifacts
  unless the repo explicitly says deployment attempts are the release unit.
- Keep package version, tag, artifact name, release notes, and deployment record
  consistent.
- If a SemVer-only tool rejects zero-padded date fields, use SemVer or a
  tool-compatible documented variant instead of forcing CalVer.

## Examples

Use monthly CalVer:

```text
scheme: calver-monthly
pattern: YY.MM.N
timezone: UTC
release unit: production deployment
example: v26.05.1
```

Use weekly CalVer:

```text
scheme: calver-weekly
pattern: YY.WW.N
calendar: ISO week
timezone: UTC
release unit: weekly release train artifact
example: v26.21.1
```

Use SemVer:

```text
scheme: semver
pattern: MAJOR.MINOR.PATCH
release unit: published package
example: v2.4.7
```

## Stop If

- The artifact, package, app display version, build number, tag, and deployment
  id are being treated as the same thing but the platform distinguishes them.
- The repo already uses a different scheme and no migration approval exists.
- The version would collide with an existing tag, artifact, package, or
  deployment record.
- Tooling rejects the chosen version format.
