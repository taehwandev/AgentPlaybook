---
keyflow_id: sys_a66e7e6b4a9d
status: review
type: ai-generated
---

# Invitation Workflows

Use for team, tenant, workspace, or organization invite flows.

For concrete invite records, token handling, state machine, accept-time
revalidation, delivery side effects, and tests, also use
`invitation-implementation.md`.

## Flow

```text
create -> notify -> accept -> link/create account -> join tenant -> assign role
```

## Rules

- Invite creation needs its own permission.
- Limit which roles the inviter can assign.
- Distinguish existing member, pending invite, expired invite, revoked invite.
- Canonicalize email before duplicate checks.
- Revalidate tenant, role, token, and inviter policy at accept time.
- Refresh session and permissions after accept.

## Do Not

- Do not accept an invite only because the token shape is valid; recheck tenant,
  invite status, expiration, revocation, target email, role assignability, and
  current membership.
- Do not let the inviter assign roles or permissions broader than their current
  authority unless an explicit owner/system policy allows it.
- Do not reveal whether private users, tenants, emails, or memberships exist
  through different error copy unless product policy allows it.
- Do not reuse invite tokens after accept, revoke, expiration, email change, or
  tenant deletion.
- Do not update membership without refreshing session, permission caches, open
  tabs, and audit state when immediate enforcement is expected.

## UI States

- success
- duplicate invite
- already member
- permission denied
- role not assignable
- expired or revoked token

## Audit

Record create, resend, revoke, accept with actor, tenant, target email, and role.

## Tests

Cover create, resend, revoke, expire, accept existing-user, accept new-user,
wrong email, wrong tenant, duplicate invite, already-member, role-not-assignable,
revoked inviter permission, stale session, token replay, and audit record paths
when applicable.
