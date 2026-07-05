---
keyflow_id: sys_invitation_implementation
status: review
type: human-reviewed-needed
---

# Invitation Implementation

Use when implementing team, workspace, organization, tenant, project, or billing
invite creation, resend, revoke, accept, email delivery, role assignment, or
invite tests.

Also read `invitation-workflows.md`, `auth-rbac-implementation.md`, and the
matching server/client platform cards.

## Invite State Machine

Model invite lifecycle explicitly:

```text
draft -> pending -> accepted
                 -> expired
                 -> revoked
                 -> superseded
```

Useful command paths:

```text
create -> notify
resend -> notify
revoke
accept -> link or create account -> join tenant -> assign role -> refresh session
```

Do not model invite state only as `acceptedAt` plus nullable fields if the
product needs expired, revoked, duplicate, or superseded behavior.

## Invite Record

An invite usually needs:

- tenant/workspace/org id
- normalized target email
- display email as entered when product copy needs it
- role or permission bundle requested
- inviter actor id
- status
- token hash, not raw token
- expiration timestamp
- accepted actor id and accepted timestamp
- revoked actor id and revoked timestamp
- resend count and last sent timestamp when relevant
- audit/correlation id when relevant

Raw invite tokens should not be logged, stored in analytics, or returned after
creation except through the intended delivery path.

## Creation Rules

- Invite creation needs its own permission.
- Check the inviter can assign the requested role.
- Canonicalize email before duplicate checks.
- Distinguish already member, pending invite, revoked invite, expired invite,
  and role-not-assignable states.
- Rate-limit invite creation and resend paths.
- Avoid leaking membership existence across tenants unless product policy allows
  that disclosure.

## Acceptance Rules

At accept time, revalidate:

- token exists, is not expired, is not revoked, and has not been accepted
- tenant/workspace/org still exists and allows new members
- target email matches the signed-in identity or approved account-linking flow
- requested role is still assignable
- inviter policy or tenant policy has not invalidated the invite
- billing/seat/quota entitlement still allows another member

Accept should be idempotent. Duplicate clicks, email-link retries, and browser
refresh should not create duplicate memberships.

## UI States

Client and email flows should distinguish:

- pending invite sent
- duplicate pending invite
- already member
- permission denied
- role not assignable
- expired invite
- revoked invite
- accepted invite
- account mismatch
- seat/quota blocked
- email delivery failed or delayed

Invite UI must not imply access was granted until the server acceptance path has
completed.

## Side Effects And Audit

- Create, resend, revoke, accept, expire, and role assignment should be auditable
  when the product has audit requirements.
- Email delivery should be retriable and should not block the database state in
  a half-written condition.
- Webhooks, analytics, notifications, and billing seat changes should be
  idempotent or reconciled.

## Tests

Cover:

- create, resend, revoke, expire, accept
- duplicate pending invite
- already member
- wrong tenant
- role not assignable
- revoked or expired token
- token replay and duplicate accept click
- account email mismatch
- seat/quota blocked
- stale invite after role or tenant policy change
- email send failure and retry
- audit record contents without raw token leakage

Review the final diff for raw token storage, client-side-only role checks,
accept paths that skip revalidation, duplicate membership risk, and invite UI
that promises access before server acceptance.
