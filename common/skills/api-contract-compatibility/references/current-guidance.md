---
keyflow_id: sys_api_contract_compatibility
status: review
type: human-reviewed-needed
---

# API Contract Compatibility

Use when changing HTTP APIs, DTOs, schemas, SDK clients, route contracts,
deep links, events, webhooks, queues, import/export formats, or shared fixtures.

For SOLID, Interface Segregation, substitutable implementations, and dependency
direction around code-level contracts, also use
`common/solid-design-principles.md`.

## Default

Treat contracts as product surfaces. A contract is not only server code; it is
what clients, tests, docs, integrations, and users can rely on.

## Rules

- Identify the contract owner and consumers before changing fields or routes.
- Prefer additive changes over breaking changes.
- Do not add a required request field without a compatibility or migration plan.
- Do not remove, rename, narrow, or repurpose response fields without checking
  all clients.
- Keep stable identifiers stable. Changing ID shape is a breaking change.
- Keep error shape typed and documented enough for clients to recover.
- Define pagination, sorting, filtering, timezone, currency, locale, and null
  behavior explicitly when they affect users or clients.
- Use idempotency or duplicate handling for retries, writes, billing, webhooks,
  background jobs, and import flows.
- Keep auth, tenant, permission, entitlement, and quota enforcement at the trusted
  boundary, not only in the client.
- Keep code-level client and server interfaces narrow. Do not force clients,
  adapters, fakes, or tests to implement unrelated operations to satisfy one
  broad API surface.

## Compatibility Questions

- Which released client versions or external integrations depend on this shape?
- Is the change backward compatible, forward compatible, or intentionally
  breaking?
- What happens when an old client talks to a new server?
- What happens when a new client talks to an old server?
- Are fake data, fixtures, generated clients, docs, and tests updated together?
- Is the contract versioned by URL, schema version, event type, feature flag, or
  migration window?

## Tests

Cover contract tests or equivalent verification for:

- request validation
- response shape
- denied access and cross-tenant access
- old-client compatibility when relevant
- error shape and retry behavior
- fixture or generated client parity
