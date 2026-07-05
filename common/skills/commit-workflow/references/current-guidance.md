---
keyflow_id: sys_f20b4c0c0d16
status: review
type: ai-generated
---

# Commit Workflow

Use before creating commits, regardless of git client, IDE, CLI, or AI tool.

For AgentPlaybook-routed work, clear local commit requests must use the
lightweight `commit` route, or `git_commit` when the runtime uses that label.
Do not route a clear commit request through the general `task`, `review`, or
`triage` routes. The commit route exists to avoid running implementation gates
after the code work is already done.

## Read

- Repo-local commit, branch, signing, and generated-file rules.
- Current `git status --short --untracked-files=all`.
- Final diff for every file to be committed.
- Verification output for the changed boundary.
- Remote and repository visibility before pushing or publishing.

## Commit Unit

- One commit should carry one reviewable intent.
- Do not mix feature, refactor, formatting, generated files, and dependency churn unless they are inseparable.
- Every changed line should trace to the commit purpose.
- If a commit needs a long explanation, consider splitting it first.
- Use `common/change-size-policy.md` when a diff is broad or hard to review.
- Use `common/generated-files-policy.md` when generated files, lockfiles, or snapshots changed.

## Decision Rule

Commit only a unit that can be reviewed, tested, reverted, and explained as one
purpose. If the diff contains independent behavior, refactor, generated,
dependency, config, release, or documentation changes, split unless the pieces
cannot build, migrate, or make sense independently.

When a broad commit is necessary, record why it cannot split, which files are
mechanical versus behavioral, what verification covers the risky parts, and how
to rollback or forward-fix.

## Before Commit

- Check repo-local commit rules first.
- Run the lightweight code review first. If it finds an issue, stop before
  staging or committing and report the concrete fixes needed.
- Check repo-local branch, push, PR, or tag rules only when that action is in
  scope.
- Inspect the final diff, not memory of the work.
- Remove only unused code created by this change.
- Run the nearest useful verification, or record why it was skipped.
- Do not include secrets, local paths, debug logs, or temporary artifacts.
- Call out API contract, migration, release, accessibility, or security impact
  when the commit touches those surfaces.

## Commit Readiness Gate

Before creating a commit, confirm evidence rather than repeating a full review:

- staged diff contains only the current task scope
- unrelated or user-owned changes are excluded
- code review or Review Hook passed for the reviewed diff
- code conventions, formatting, lint, or repo style checks ran or were marked
  not applicable
- staged diff still matches the reviewed diff; rerun relevant checks if files
  changed after review
- nearest behavior, contract, build, docs, or manual smoke verification ran, or
  the skip reason and residual risk are explicit
- VibeGuard or the repo-local safety gate passed when required
- secrets, local env files, local paths, debug logs, signing material, and
  private data are absent from the staged diff
- generated, lockfile, dependency, migration, API, release, or security changes
  have source command, compatibility, rollback, or owner evidence
- commit message matches the staged diff and does not hide skipped checks,
  behavior changes, or release/security/migration risk

Commit readiness approves only the local commit. It does not approve branch
creation, push, PR creation, tag publication, release, deploy, or other external
state changes.

For web projects where a requested direct push to the default branch is the
documented production release path, treat the push as release publication. Add
or require a tag only when repo-local policy requires tags or tags are the only
durable release record, and only after the version/tag scheme and release
readiness evidence are known.

## Stage Deliberately

- Stage only files that belong to the commit purpose.
- Keep user-owned unrelated changes out of the commit unless the user explicitly
  asked to include them.
- Review staged diff, not only working tree diff.
- If generated files or lockfiles are included, explain the source command or
  reason they changed.
- If the commit crosses public contracts, migrations, release config, signing,
  credentials, billing, permissions, or data, confirm verification and rollback
  notes before committing.

## Message

Prefer:

```text
type(scope): what changed

Why:
- reason or product context

Verified:
- command or manual check
```

Keep the subject about behavior or structure, not effort. Mention migrations, breaking changes, security impact, and follow-up work explicitly.

## Do Not

- Do not commit secrets, local env files, debug logs, personal paths, private
  prompts, credentials, signing material, or unreviewed generated output.
- Do not hide failed or skipped verification in the message.
- Do not create a broad "cleanup" commit when the diff contains independent
  behavior, refactor, dependency, generated, or release changes that can split.
- Do not rewrite history, amend, tag, push, or publish unless the user requested
  that external state change.
- Do not assume `main`, `master`, `develop`, or `trunk` is the correct base or
  publish target without repo-local evidence.

## Verification

Before committing, verify:

- staged diff contains only the intended files and no unrelated user-owned work
- nearest behavior, contract, build, lint, format, or manual smoke check ran, or
  the skip reason and residual risk are explicit
- VibeGuard or repo-local safety gate passed when required
- generated files, lockfiles, snapshots, migrations, release config, or
  dependency changes have source command or rationale
- public contract, persistence, security, billing, permission, release, or
  migration changes have compatibility and rollback notes when applicable
- Commit Readiness Gate evidence above is satisfied

## Common Types

- `feat`: user-facing capability or product behavior
- `fix`: bug fix or regression repair
- `refactor`: structure change with no intended behavior change
- `test`: tests, fixtures, or verification support
- `docs`: documentation only
- `chore`: tooling, config, maintenance, or repository housekeeping
- `build`: build system, packaging, dependency, or lockfile change
- `perf`: performance improvement
- `security`: security hardening, secret handling, auth, or permission fix

Repo-local commit types win when they differ.

## Handoff

Report the commit SHA when a commit was created. If no commit was created,
report the files intentionally left staged or unstaged, verification status, and
any reason the diff should be split before commit.
