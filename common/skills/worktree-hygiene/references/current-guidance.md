---
keyflow_id: sys_worktree_hygiene
status: stable
type: human-reviewed-needed
---

# Worktree Hygiene

Use when working in an existing checkout, especially when the agent did not
start from a clean tree.

## Default

User-owned changes are part of the environment. Preserve them unless the user
explicitly asks to remove or replace them.

## Before Editing

- Check the current diff or status when edits, commits, reviews, or releases are
  in scope.
- Identify files already changed before the task.
- Read a file before editing it, especially if it is already modified.
- Keep formatting, generated output, dependency changes, and cleanup separate
  from the requested behavior unless they are required.

Use concrete evidence instead of memory:

```text
git status --short --untracked-files=all
git diff --name-only
git diff -- <path>
```

For long tasks, record the initial changed-file list in your notes. When the
repo is already dirty, treat that list as user-owned until you have inspected
the file and can identify the lines you changed.

## During Work

- Do not revert, restage, reformat, or overwrite unrelated user changes.
- If user changes touch the same file, edit around them and preserve intent.
- If user changes make the requested work ambiguous or unsafe, stop and state the
  conflict instead of guessing.
- Keep commits, patches, and summaries limited to changes made for the task.
- Treat generated files and lockfiles as user-visible diff noise unless the task
  or toolchain requires them.

## Rollback Missed Gate Scope

Use when a workflow gate was missed and the agent must retry that gate.

- Roll back only changes made by the agent that depend on the missed gate or
  must be undone before retrying that gate.
- Preserve pre-existing user changes, even in files the agent also touched.
- Prefer a targeted reverse patch or explicit file edit over broad repository
  reset commands.
- Do not roll back completed earlier gates or unrelated valid work.
- Do not use destructive history or filesystem cleanup without a direct user
  request.
- If safe rollback cannot be separated from user-owned changes, stop and report
  the blocker instead of guessing.

## Before Reporting

- Re-check the final diff or touched files.
- Separate changes made by the agent from pre-existing changes.
- Mention skipped cleanup or unrelated issues instead of bundling them into the
  task.
- Do not claim the worktree is clean unless it has been checked.

Before staging or committing, compare staged files against the task scope:

```text
git diff --name-only
git diff --cached --name-only
git status --short --untracked-files=all
```

Stage only files that were inspected and are part of the current task.

Before branch creation, push, PR, or tag publication, check the branch context:

```text
git status -sb
git branch --show-current
git remote -v
```

Use repo-local policy and `common/skills/branch-strategy/SKILL.md` to decide whether the
current branch is a work branch, integration branch, release branch, or
protected branch. If the repo has multiple plausible bases or targets, stop
before moving work or mutating remote state.

## Never

- Use destructive history or filesystem commands to simplify the task without a
  direct user request.
- Hide unrelated edits inside a broad refactor or formatting pass.
- Commit files that were not inspected when they contain pre-existing changes.
