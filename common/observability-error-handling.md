---
keyflow_id: sys_observability_error_handling
status: review
type: ai-generated
---

# Observability Error Handling

Use when adding or reviewing errors, logging, diagnostics, monitoring, audit events, support traces, or user-facing failure states.

For typed error shapes, retryability, recovery, and user-visible failure-state
design, also use `error-modeling.md`.

## Separate

- User-facing message
- Developer diagnostic
- Operational log
- Metric
- Trace or span
- Alert
- Audit event
- Recovery action

## Rules

- Every async boundary needs a visible success, loading, and failure path.
- Do not swallow errors silently.
- User messages should explain what the user can do next.
- Logs should help debug without leaking secrets or unnecessary personal data.
- Audit events should record actor, target, action, time, and result.
- Retry needs idempotency or a clear duplicate-handling strategy.
- Logs, metrics, traces, and alerts should answer the operator question the
  change creates: is it failing, where is it failing, how many users or jobs are
  affected, and what action is needed?
- Prefer symptom alerts over implementation-detail alerts when the symptom is
  measurable.
- Keep correlation ids stable across logs, traces, async work, and user-visible
  support states when the platform supports it.
- Keep metric cardinality bounded. Do not put user ids, secrets, raw URLs,
  prompts, customer data, or unbounded error strings in metric labels.

## Instrumentation

Choose signals by the surface being changed:

| Surface | Useful Signals |
| --- | --- |
| Request or API path | rate, errors, duration, status, dependency failure, correlation id |
| Worker or queue | enqueue rate, lag, retry count, dead-letter count, job duration |
| Storage or cache | hit/miss, stale read, write failure, migration/backfill progress |
| UI or client runtime | user-visible failure, startup/load time, key interaction error, crash |
| Release or migration | rollout stage, version, smoke result, rollback trigger, compatibility error |

Add instrumentation only when it answers a concrete support, operations, or
product reliability question. Do not add noisy logs or metrics because they are
easy to emit.

## Crash Reporting

Production client apps should have crash reporting or a documented exception
for privacy, regulatory, offline-only, cost, or product-stage reasons. Choose
one primary crash source of truth by default. Adding multiple crash providers
requires a written reason, because duplicate SDKs increase binary, privacy,
alerting, and cost surfaces.

Crash reporting setup must define:

- provider and release/channel mapping
- which user, device, breadcrumb, attachment, screenshot, and custom-key data is
  collected
- PII and secret scrubbing rules
- sampling, retention, quota, and current pricing or cost limit
- how crash reports connect to user-visible errors, logs, traces, and release
  health

Do not send access tokens, refresh tokens, private payloads, raw server
responses, local file paths, secrets, prompts, customer content, or unrestricted
logs to crash reports.

## Exception Handling

- Do not write empty catch blocks.
- Do not convert an exception into success without recording a typed failure,
  user-visible state, log, metric, audit event, or explicit recovery path.
- Preserve the original cause when wrapping or mapping errors.
- Rethrow, return a typed result, or surface a recoverable user state; do not
  hide the failure to make a command, test, or UI path appear successful.
- If an error is intentionally ignored, keep the scope narrow and leave a short
  reason. Ignored errors must not affect correctness, data integrity, security,
  billing, permissions, or user-visible completion.

## Error Shape

Prefer typed errors or result objects over string matching.

```text
code
status / HTTP status
message
retryable
field errors
correlation id
```

## Check

- Can support or engineering trace the failure?
- Can the user recover or understand the block?
- Is sensitive data excluded from logs and telemetry?
- Are repeated failures rate-limited or deduplicated?
- Does an alert point to a symptom that requires action?
- Was telemetry exercised with a test, local run, staging check, or explicit
  residual-risk note?
