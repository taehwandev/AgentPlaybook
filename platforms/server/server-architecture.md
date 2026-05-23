---
keyflow_id: sys_5401647d98b8
status: review
type: ai-generated
---

# Server Architecture

Use for API, worker, database, auth, tenancy, and integration-service work.

For migrations, transactions, jobs, webhooks, queues, or external systems, also
use `server-data-jobs.md`. For auth, tenant isolation, API input, rate limits,
uploads, webhooks, outbound calls, or secrets, also use `server-security.md`.

## Boundaries

```text
Route/Handler -> Use Case/Service -> Repository/Client -> Database/External System
```

## Rules

- Keep request parsing separate from product rules.
- Enforce auth, permission, tenant boundary on the server.
- Keep DB schema/entity details out of API response shaping when possible.
- Make side effects explicit: email, billing, webhooks, jobs, files.
- Use idempotency for retries, payments, webhooks, and background jobs.
- Log operational detail without leaking secrets or personal data.

## Refactor Signals

- Route handler owns validation, permission, DB, and side effects.
- Tenant filter is optional or repeated manually.
- External API errors leak directly to clients.
- Background job retry behavior is unclear.
