---
keyflow_id: sys_code_conventions
status: draft
type: human-reviewed-needed
---

# Code Conventions

Use when writing, changing, or reviewing code style, naming, structure,
comments, errors, and formatting.

Repo-local conventions, formatter, linter, and language idioms win over this
common baseline.

## Priority

1. Repo-local formatter, linter, compiler, and framework rules.
2. Existing local patterns in the touched area.
3. Language and platform idioms.
4. This shared baseline.

## Rules

- Make code easy to delete, move, and test.
- Prefer clear names over comments that explain unclear names.
- Keep each function, component, class, hook, or service focused on one reason to change.
- Keep UI, state, domain, data, and platform concerns separated at the nearest useful boundary.
- Do not add a new abstraction for one call site unless it protects a risky boundary.
- Do not scatter booleans for roles, permissions, entitlements, loading, or error states when a typed state or policy object would make behavior clearer.
- Prefer typed errors, result objects, or framework error types over string matching.
- Avoid hidden global state, implicit environment behavior, and hard-coded production data.
- Keep user-facing copy out of low-level logic when the repo has i18n or copy ownership.
- Comments should explain why, risk, contract, or non-obvious constraints. Do not narrate obvious code.

## Formatting

- Run the repo formatter or lint fix when configured.
- Do not reformat unrelated files or whole files unless the change requires it.
- Keep generated formatting churn separate from behavior changes when possible.
- Do not hand-edit generated code unless the repo documents that generated file as source.

## Size Signals

These are review signals, not universal failure thresholds:

- A function or component over about 150 lines often has more than one responsibility.
- A source file over about 400 lines often needs clearer sections or extraction.
- A diff touching more than about 10 source files or 300 non-test lines should have a narrow reason or be split.

Split only when it improves ownership, testability, or review. Do not create
extra files just to satisfy a line count.

## Check

- Can a reviewer name the responsibility of this unit in one sentence?
- Can the behavior be tested without booting unrelated systems?
- Did this follow nearby naming, formatting, and architecture?
- Is any complexity protecting a real product, platform, security, or data risk?
