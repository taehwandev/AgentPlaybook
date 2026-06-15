---
keyflow_id: sys_5541ae16ddef
status: review
type: ai-generated
---

# Server Review

Use for API, worker, database, auth, tenancy, migration, and integration review.

## Findings Priority

1. Auth bypass, cross-tenant access, data loss, unsafe migration, duplicate
   side effect, or secret leak.
2. Broken API, webhook, event, schema, generated-client, or persistence contract.
3. Missing validation, idempotency, transaction, retry, or rollback behavior.
4. Missing focused tests for changed route, use case, repository, job, or
   migration boundary.
5. Maintainability, layering, query efficiency, observability, or naming risk.

## Review

- Check auth, permission, tenant boundary, validation, and rate-limit behavior.
- Check route/resolver, validator, use case, repository, and response/error
  boundaries against `server-api-implementation.md` when API code changed.
- Verify request parsing is separate from product rules.
- Check idempotency for payments, webhooks, retries, and jobs.
- Review migrations for reversibility, backfill risk, locks, and data loss.
- Ensure errors and logs do not leak secrets, tokens, or personal data.

## Do Not Approve When

- Client-controlled input can set server-owned fields such as tenant, role,
  owner, billing, quota, audit, or visibility.
- A route or worker performs validation, authorization, persistence, external
  calls, response shaping, logging, and retry logic in one untestable block.
- Tenant filters, permission checks, idempotency keys, or transaction boundaries
  are optional call-site details.
- Public response shapes expose database rows, provider payloads, stack traces,
  secret values, or private existence signals without product approval.
- A migration, backfill, webhook, or job can partially apply without retry,
  rollback, or forward-fix evidence.

## Tools

- Static: compiler/typecheck, lint, schema validation.
- Unit: services, policies, validators, mappers.
- Integration: database, cache, queue, external client fakes.
- Contract: API request/response, OpenAPI, GraphQL schema, webhook payloads.
- Load/smoke: only for performance-sensitive or release-critical paths.

## UI/API Test Focus

- API returns correct status, body, and error shape.
- Unauthorized, forbidden, cross-tenant, and expired-session paths are tested.
- Background jobs retry safely and do not duplicate side effects.
- Migration and rollback path is verified when data risk exists.

## Output

Lead with concrete findings and include the server boundary involved:

```text
Findings:
- [High] platforms/server/... - issue, impact, affected contract, required verification
```

If no findings remain, say so and list contract, migration, load, or security
checks that were not run.
