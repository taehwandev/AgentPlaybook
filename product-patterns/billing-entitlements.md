---
keyflow_id: sys_billing_entitlements
status: review
type: ai-generated
---

# Billing Entitlements

Use for plans, seats, quota, feature access, invoices, subscription status, payment failures, and downgrade behavior.

For concrete billing account/subscription/plan/entitlement/usage modeling,
provider webhooks, quota, seats, cache invalidation, and tests, also use
`billing-entitlements-implementation.md`.

## Separate

- Billing account: who pays.
- Subscription: current commercial contract.
- Entitlement: what the product enables.
- Usage: measured consumption.
- Permission: who can manage or use the feature.

## Rules

- Billing state should not be trusted from client-only storage.
- Feature access should read entitlements, not raw plan names scattered through UI.
- Payment failure, cancellation, trial end, and downgrade need explicit product states.
- Seat and quota enforcement should define grace, blocking, and recovery behavior.
- Billing management permission is separate from normal admin/editor permission.
- Invoices, taxes, and payment method details usually belong to a billing provider boundary.

## Do Not

- Do not use client-visible plan names, local cache, or UI state as the trusted
  source of entitlement.
- Do not mix billing management permission with normal workspace admin,
  editor, or owner checks unless product policy says they are equivalent.
- Do not let downgraded, cancelled, payment-failed, trial-ended, over-quota, or
  revoked states fall through to generic success or generic permission denied.
- Do not perform billing-provider mutations, webhook handling, quota increments,
  or seat changes without idempotency and retry behavior.
- Do not expose provider payloads, payment method details, invoice internals, or
  billing account existence beyond the documented product contract.

## Check

- Who can view billing, change plan, manage seats, or download invoices?
- What happens when usage exceeds quota?
- What features remain available after downgrade?
- Does UI copy distinguish role limitation from plan limitation?
- Is server enforcement aligned with client messaging?

## Tests

Cover entitlement on/off, quota exceeded, downgrade, payment failure, cancelled
subscription, trial end, revoked billing manager, stale entitlement cache,
provider webhook retry, duplicate webhook delivery, and seat/usage race
conditions when applicable.
