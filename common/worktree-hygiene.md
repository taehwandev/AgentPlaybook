---
keyflow_id: sys_worktree_hygiene
status: review
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

## During Work

- Do not revert, restage, reformat, or overwrite unrelated user changes.
- If user changes touch the same file, edit around them and preserve intent.
- If user changes make the requested work ambiguous or unsafe, stop and state the
  conflict instead of guessing.
- Keep commits, patches, and summaries limited to changes made for the task.
- Treat generated files and lockfiles as user-visible diff noise unless the task
  or toolchain requires them.

## Before Reporting

- Re-check the final diff or touched files.
- Separate changes made by the agent from pre-existing changes.
- Mention skipped cleanup or unrelated issues instead of bundling them into the
  task.
- Do not claim the worktree is clean unless it has been checked.

## Never

- Use destructive history or filesystem commands to simplify the task without a
  direct user request.
- Hide unrelated edits inside a broad refactor or formatting pass.
- Commit files that were not inspected when they contain pre-existing changes.
