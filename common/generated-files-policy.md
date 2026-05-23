---
keyflow_id: sys_generated_files_policy
status: draft
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

Repo-local rules decide what is committed.

## Rules

- Do not hand-edit generated files unless the repo explicitly treats them as source.
- Regenerate from the documented command when possible.
- Keep generated churn separate from behavior changes when it would obscure review.
- Commit lockfile changes when dependency resolution changed intentionally.
- Do not commit build outputs, local cache, editor state, private config, or temporary files.
- Review generated files for secrets, endpoints, app ids, signing data, local paths, and environment-specific values before committing.
- Snapshot updates require a reason tied to behavior, visual output, or accepted product change.

## When Generated Diff Is Large

Record:

- command used to generate it
- source input that changed
- whether the diff is expected mechanical output
- how the generated result was verified

## Check

- Can another developer reproduce this file from committed inputs?
- Is this file supposed to be committed in this repo?
- Does the generated output contain secrets, local paths, or private data?
- Would separating generated output make the behavior diff easier to review?
