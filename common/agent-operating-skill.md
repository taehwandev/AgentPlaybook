---
keyflow_id: sys_agent_operating_skill
status: draft
type: human-reviewed-needed
---

# Agent Operating Skill

Use this before implementation, review, refactoring, debugging, documentation,
or verification work. This is the baseline skill for reducing repeated agent
mistakes.

## Core Loop

1. Identify the target project and task type.
2. Read repo-local instructions before changing files.
3. Use `index.md` to load only relevant KeyFlow cards.
4. Inspect existing code, docs, tests, and local conventions.
5. Make the smallest change that genuinely addresses the request.
6. Verify with the narrowest reliable command first.
7. Report what changed, what was verified, and what risk remains.

## Mistake Prevention Checklist

Before editing:

- Confirm target path and project.
- Check repo-local `AGENTS.md`, `CLAUDE.md`, `CODEX.md`,
  `.agents/README.md`, `CONTRIBUTING.md`, or equivalent docs.
- Check whether the task touches data, auth, permissions, billing,
  persistence, filesystem, network, release, or external state.
- Check whether the task touches secrets, client keys, local config, logs,
  analytics, crash reporting, or open-source-safe setup.
- Check for existing user changes in files you may touch.

While editing:

- Follow existing architecture and naming before inventing a new pattern.
- Keep unrelated refactors out of feature or bug-fix work.
- Preserve user-owned changes.
- Do not expose secrets, tokens, private prompts, or credential contents.
- Do not claim mocked, placeholder, or TODO behavior is complete.

Before finishing:

- Run the most relevant test, build, typecheck, lint, or smoke check.
- If verification cannot run, state why and what risk remains.
- Include file references when explaining non-trivial changes.

## Task Routing

- Architecture: `common/architecture-selection.md`,
  `common/architecture-design.md`, or `common/app-architecture.md`.
- Code conventions: `common/code-conventions.md`.
- Change size or broad diffs: `common/change-size-policy.md`.
- Dependencies, SDKs, or build plugins: `common/dependency-policy.md`.
- Generated files, lockfiles, or snapshots: `common/generated-files-policy.md`.
- Refactoring: `common/refactoring.md`.
- Tests and evidence: `common/testing.md` and
  `common/verification-policy.md`.
- Code review: `common/code-review.md`.
- Local programs, agent CLIs, or usage telemetry: `common/local-tools.md`.
- Secrets, external state, or user-owned changes:
  `common/agent-editing-safety.md`, `common/secure-development-baseline.md`,
  and `common/security-privacy-review.md`.
- React, iOS, Android, server, application, or Mac work: load the matching
  platform card from `index.md`.

## Output Contract

Use short evidence-based reporting:

```text
Changed:
- ...

Verified:
- ...

Remaining risk:
- ...
```

For small tasks, a concise paragraph is enough, but verification status still
matters.
