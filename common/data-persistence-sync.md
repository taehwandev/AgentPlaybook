---
keyflow_id: sys_data_persistence_sync
status: review
type: ai-generated
---

# Data Persistence Sync

Use for local persistence, cloud sync, offline mode, migrations, import/export, cache invalidation, and conflict handling.

## Separate

- Draft/local UI state
- Durable local persistence
- Server source of truth
- Derived cache
- Exported or shared artifacts

## Rules

- Define ownership before adding a second copy of data.
- Persist only stable state, not transient UI state.
- Version data that can outlive one app release.
- Make stale writes and conflict behavior explicit.
- Keep migration and backward compatibility near the storage boundary.
- Treat import/export as contracts with validation and failure states.

## Do Not

- Do not add a cache, local store, export file, sync record, or derived read model
  without naming the source of truth and invalidation owner.
- Do not persist auth-, tenant-, role-, plan-, or permission-sensitive data
  without a cleanup rule for logout, account switch, revoke, downgrade, or
  membership change.
- Do not silently clamp, drop, merge, or overwrite malformed, stale, duplicated,
  partial, or conflicting data unless that behavior is product-correct and
  tested.
- Do not change persisted field names, import/export formats, cache keys, or
  migration behavior as part of a refactor without compatibility evidence.

## Sync Questions

- Is this local-first, server-first, or offline-capable?
- What happens on stale save?
- Can two clients edit the same resource?
- What data is safe to cache?
- What must be cleared on logout, org switch, revoke, or downgrade?

## Tests

Cover load, save, update, delete, migration, corrupted data, quota/storage
failure, stale version, duplicate event, partial sync, conflict, retry,
rollback, import/export validation, and logout/account-switch cleanup where
relevant.
