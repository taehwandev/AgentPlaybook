---
keyflow_id: sys_generated_files_policy
status: stable
type: human-reviewed-needed
---

# Generated Files Policy

Use when codegen, lockfiles, snapshots, build artifacts, schema clients,
translations, icons, assets, or formatting tools modify files.

## Classify First

Before editing or committing, classify generated files as:

- source of truth generated from repo inputs
- derived artifact that should not be committed
- lockfile or manifest required for reproducible installs
- snapshot or baseline used by tests
- release artifact that belongs outside normal source diffs
- generated documentation, wiki output, search index, or source map that may be
  derived from committed code and docs

Repo-local rules decide what is committed.

## Rules

- Do not hand-edit generated files unless the repo explicitly treats them as source.
- Regenerate from the documented command when possible.
- Keep generated churn separate from behavior changes when it would obscure review.
- Commit lockfile changes when dependency resolution changed intentionally.
- Do not commit build outputs, local cache, editor state, private config, or temporary files.
- Review generated files for secrets, endpoints, app ids, signing data, local paths, and environment-specific values before committing.
- When generated clients, manifests, config files, or assets contain API origins,
  callback URLs, redirect hosts, webhook endpoints, CORS origins, or asset
  hosts, review them with `runtime-url-configuration.md`. Environment-specific
  URLs are configuration concerns unless they contain credentials or expose
  private infrastructure.
- Snapshot updates require a reason tied to behavior, visual output, or accepted product change.
- Generated documentation should name the source revision and generator version
  when it is published, committed, or reviewed. If it is stored as a build
  artifact, keep the source docs and generation manifest as the reviewable
  source of truth.
- Generated knowledge graphs, wiki exports, search indexes, HTML reports, and
  source maps are publishable only when they are intentionally selected
  artifacts, reproducible from committed/public-safe inputs, and reviewed for
  secrets, local paths, private source material, internal endpoints, and stale
  source references. Keep local cache, temporary extraction files, token/cost
  trackers, and intermediate runtime sidecars ignored unless the repo explicitly
  treats one of them as a source-of-truth artifact.

## When Generated Diff Is Large

Record:

- command used to generate it
- source input that changed
- whether the diff is expected mechanical output
- how the generated result was verified
- for generated documentation or graph outputs, the publish/commit boundary:
  ignored runtime state, committed reviewable artifact, or separately deployed
  release artifact

## Check

- Can another developer reproduce this file from committed inputs?
- Is this file supposed to be committed in this repo?
- Does the generated output contain secrets, local paths, or private data?
- Would separating generated output make the behavior diff easier to review?
