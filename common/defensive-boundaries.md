---
keyflow_id: sys_defensive_boundaries
status: review
type: human-reviewed-needed
---

# Defensive Boundaries

Use when code consumes values from outside the current trusted boundary:
user input, environment, configuration, files, network responses, databases,
clocks, platform APIs, third-party SDKs, generated artifacts, or cached state.

## Default

Treat boundary values as unavailable, malformed, stale, duplicated, partial, or
out of range until validated.

Normalize boundary data before it reaches product logic. Prefer typed internal
states such as `available`, `unavailable`, `permissionDenied`, `stale`, or
`invalid` over sentinel values, magic numbers, empty strings, or string matching.

For environment-specific API origins, callback URLs, redirect URIs, webhook
endpoints, CORS origins, deep link hosts, or asset hosts, also use
`runtime-url-configuration.md`.

## Guard

- Null, missing, empty, and permission-denied values.
- Zero, negative, maximum, overflow, underflow, `NaN`, and infinite numbers.
- Values above expected percentages, quotas, limits, sizes, or durations.
- Malformed dates, stale timestamps, clock drift, and timezone assumptions.
- Partial payloads, version mismatches, unknown enum cases, and extra fields.
- Duplicate, out-of-order, delayed, retried, or cancelled events.
- Cached values that outlive permissions, membership, auth, configuration, or
  upstream state.
- Boundary calls that fail slowly, fail intermittently, or return success with
  unusable data.

## Map

- Parse and validate at the edge.
- Clamp only when clamping is product-correct; otherwise surface an explicit
  invalid or unavailable state.
- Preserve enough diagnostic detail for debugging without leaking sensitive data.
- Keep retries idempotent or explicitly duplicate-safe.
- Make fallback behavior visible to callers, not hidden inside unrelated UI or
  business logic.

## Verify

Cover the boundary cases that can change behavior:

- normal valid value
- lower and upper boundary values
- missing or permission-denied value
- malformed or unknown value
- stale, duplicated, or out-of-order value
- slow, failed, cancelled, or retried boundary call

Do not call a boundary safe only because the happy path works once.
