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
5. Maintainability
6. Style

## Check

- Does this satisfy the request?
- Does it follow project/product guidance and repo-local rules?
- Are failure and edge states handled?
- Are client and server permission boundaries consistent?
- Are data, privacy, billing, or tenant boundaries affected?
- Are API, DTO, route, event, webhook, or fixture contracts still compatible?
- Do user-facing UI changes preserve accessibility, localization, long text, and error states?
- Are release, deployment, migration, or rollback risks documented when affected?
- Does it follow local patterns?
- Is the diff wider than needed?

## Review Stance

- Be critical, not decorative.
- Review the changed work, not the author's intent.
- Do not rewrite unrelated code during review.
- Separate blockers from optional improvements.
- Prefer concrete file/line findings over broad advice.

## Format

```text
Findings:
- [High] path:line issue and impact

Open questions:
- ...

Summary:
- ...
```

If no findings, say so and mention remaining test gaps.
