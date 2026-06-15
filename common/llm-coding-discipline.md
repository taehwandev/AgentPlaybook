---
keyflow_id: sys_llm_coding_discipline
status: review
type: human-reviewed-needed
---

# LLM Coding Discipline

Use before coding. These rules reduce common LLM mistakes. Bias toward caution over speed; use judgment for trivial tasks.

## Think First

- State assumptions when they affect implementation.
- If multiple interpretations exist, surface them.
- Ask when ambiguity changes the result.
- Push back on unnecessary scope or complexity.

## Keep It Simple

- Build only what was asked.
- No speculative features, config, flexibility, or abstractions.
- No single-use abstraction.
- If the solution feels much larger than the problem, simplify.

## Do Not Pack Everything Together

- Do not solve implementation speed by dumping unrelated code into one file.
- Do not write one large function, component, hook, handler, job, or script step
  that owns parsing, validation, IO, state changes, rendering, and recovery.
- Do not add new behavior to an oversized unit without first naming the
  responsibility being added and choosing the nearest useful split.
- Do not create helper functions or files that are not reusable, testable, or
  reviewable. A helper must have a clear responsibility; otherwise keep the
  logic inline or file-private.
- Do not create generic architecture folders before the code has a real owner,
  caller contract, or dependency boundary.

## Change Surgically

- Touch only lines tied to the request.
- Match existing style.
- Do not refactor adjacent code unless required.
- Remove only unused code created by your change.
- Mention unrelated dead code; do not delete it.

## Verify The Goal

Turn work into one to three concrete checks before or during the change:

```text
1. User request -> observable outcome -> verification evidence.
2. Risk touched -> guardrail or regression check -> verification evidence.
```

Examples:

- README install guidance changed -> links and commands still resolve -> run
  markdown link/path check or document why it cannot run.
- Login error behavior changed -> invalid login shows the expected error and
  valid login still works -> run the focused test or manual path.
- Refactor without intended behavior change -> public behavior stays equivalent
  -> run the existing narrow test or compare before/after behavior.

If success cannot be verified, name the gap before proceeding.
