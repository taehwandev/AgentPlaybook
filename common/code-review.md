---
keyflow_id: sys_739117e591d2
status: review
type: ai-generated
---

# Code Review

Use to review the current work product: working tree, diff, PR, or
implementation result. Review against the user's request, repo-local
instructions, and any project or product guidance.

## Priority

1. User-visible regression
2. Security, privacy, permission bug
3. Data loss, auth, billing risk
4. Missing or weak tests
5. Missing or stale source-of-truth documentation
6. Maintainability
7. Style

## Read

- User request, acceptance criteria, PRD/ARD, issue, or commit message.
- Repo-local instructions and any matching AgentPlaybook platform/product cards.
- Final diff, including generated files, lockfiles, fixtures, snapshots, and
  config.
- Verification output or evidence gaps.
- Affected source-of-truth docs, runbooks, API references, architecture notes,
  and agent instructions when behavior, commands, contracts, setup, or
  ownership changed.
- Nearby ownership boundaries, public contracts, state owners, and side effects
  when the diff crosses them.

## Check

- Does this satisfy the request?
- Does it follow project/product guidance and repo-local rules?
- Are failure and edge states handled?
- Are client and server permission boundaries consistent?
- Are data, privacy, billing, or tenant boundaries affected?
- Are API, DTO, route, event, webhook, or fixture contracts still compatible?
- Does production code follow SOLID responsibility and dependency rules,
  especially narrow caller-facing contracts for Interface Segregation?
- Are broad services, repositories, contexts, component props, hook return
  objects, SDK clients, or module exports forcing callers or tests to depend on
  behavior they do not use?
- Do module public exports stay narrower than their implementations, or do they
  leak implementation, platform, SDK, fixture, generated, or unrelated feature
  dependencies to consumers?
- Are environment-specific API origins, callback URLs, redirect URIs, deep link
  hosts, webhook endpoints, CORS origins, and asset hosts supplied through the
  platform's config mechanism rather than hard-coded runtime literals?
- Do user-facing UI changes preserve accessibility, localization, long text, and error states?
- Are release, deployment, migration, or rollback risks documented when affected?
- Did behavior, setup, commands, contracts, architecture, or ownership change in
  a way that requires docs to be updated or explicitly left unchanged with a
  reason?
- Does it follow local patterns?
- Is the diff wider than needed?

## Findings Criteria

Report a finding when a reviewer would reasonably ask for a code or test change
before approval:

- The behavior can fail for a real user, caller, platform target, or external
  system.
- The change violates an ownership, dependency, public contract, security,
  privacy, data, billing, release, accessibility, or persistence boundary.
- Verification is missing for a changed high-risk boundary.
- The change leaves stale documentation, runbooks, agent instructions, API
  references, or architecture notes that a future implementer would reasonably
  follow.
- The diff mixes unrelated work enough to hide risk or block rollback.

Do not report preference-only style notes as findings unless they violate
repo-local rules or obscure correctness. Put optional cleanup in open questions
or summary only when it helps the handoff.

## Review Stance

- Be critical, not decorative.
- Review the changed work, not the author's intent.
- Do not rewrite unrelated code during review.
- Separate blockers from optional improvements.
- Prefer concrete file/line findings over broad advice.
- If no issue is found, say that directly and still name unverified surfaces.
- Treat documentation freshness as part of the review, not as a separate
  follow-up hook.

## Hook Scope

When review is enforced through `scripts/agent-hook.py review`, treat the hook
as a read-only gate:

- Do not let the hook run fixers, formatters, generated-code updates,
  dependency updates, migrations, broad cleanup, broad refactors, or VibeGuard
  `--fix`.
- Do not let the hook apply documentation updates, code review fixes, or
  structure rewrites. It records whether those decisions were already handled or
  should fail.
- If the diff is too broad to review confidently in one pass, fail the hook and
  split the work before retrying.
- Check changed runtime source/style files for file size, added-line budget, and
  function, component, hook, handler, script-step, or style-block size. Test,
  fixture, mock, spec, Markdown, MDX, prose documentation, and other docs are
  excluded from these code-size hard gates unless a repo-local rule explicitly
  treats them as runtime source.
- Enforce these default hard gates for runtime source/style files: a new file
  over 400 lines fails; a file adding more than 200 lines fails; an existing
  file already over 400 lines must not grow; a function, component, hook,
  handler, script-step, or style block over 120 lines fails.
- A runtime source/style file over the review-pressure threshold requires
  explicit structure-review evidence before approval, but evidence must not
  override the hard gates.
- Check large units against responsibility splits, not only line count. A unit
  that mixes parse, validate, fetch, map, render, mutate, persist, log, navigate,
  retry, or recovery concerns should fail even when it is still under the
  numeric limit.
- On `FAIL`, explain the failing check in detail: exact path and line when
  available, observed size, configured threshold, why it blocks approval, and
  the smallest safe next action.
- Do not stop at a vague failure report. After a first `FAIL`, immediately fix
  scoped and safe issues outside the hook, then rerun the same hook once with
  `--retry-attempt 1`. Ask only when recovery requires a scope decision,
  destructive action, credential change, external state, or a broader refactor.
- If the review finds a required fix, report the smallest actionable failure and
  run the normal workflow for that fix. Do not hide the fix inside the hook.
- If a hook command changes the worktree, treat that as a hook failure.

## Format

```text
Findings:
- [High] path:line issue and impact

Open questions:
- ...

Summary:
- ...
```

Severity:

- `Critical`: data loss, auth bypass, secret exposure, destructive external
  state, release blocker, or crash on a primary path.
- `High`: user-visible regression, permission/billing/privacy bug, broken public
  contract, unsafe migration, or missing high-risk verification.
- `Medium`: edge-case behavior bug, maintainability risk that will likely cause
  defects, or weak but not blocking verification.
- `Low`: small correctness, clarity, or follow-up issue that should not block
  the main change alone.
