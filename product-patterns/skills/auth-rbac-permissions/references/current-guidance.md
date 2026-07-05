---
keyflow_id: sys_8a635e708aeb
status: review
type: ai-generated
---

# Auth, RBAC, Permissions

Use for login, membership, role, permission, entitlement, and tenant-boundary work.

For concrete identity/session/membership/role/permission/entitlement modeling,
server enforcement, cache invalidation, and tests, also use
`auth-rbac-implementation.md`.

## Separate

- Auth: who the user is.
- Authorization: what action is allowed.
- Role: product-facing permission bundle.
- Permission: action-level allow/deny.
- Entitlement: plan or feature access.

## Rules

- Server is the final authority.
- Client checks are for UX and request prevention.
- Distinguish unauthenticated, unauthorized, plan-limited, not-a-member.
- Prefer action permissions over role-name checks.
- Recheck permissions after role change, org switch, invite accept, logout.

## Do Not

- Do not treat hidden UI controls as authorization.
- Do not trust role, tenant, owner, entitlement, or permission values supplied by
  client-controlled storage, request bodies, local cache, or browser state.
- Do not scatter raw role-name checks through UI or services when action
  permissions would describe the protected command.
- Do not cache permissions across logout, tenant switch, membership revoke,
  role change, invite accept, plan change, or session refresh without
  invalidation.
- Do not leak whether private users, tenants, resources, invites, or billing
  objects exist unless product policy explicitly allows it.

## Check

- Is this enforced on server and represented in UI?
- Does cache update after permission changes?
- Does the error avoid leaking sensitive data?

## Tests

Cover unauthenticated, unauthorized, wrong-tenant, stale session, revoked role,
membership change, entitlement mismatch, and client-cache refresh paths when
applicable. Verify protected actions fail at the trusted boundary, not only
because UI controls are hidden.
