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

## Storage Choice

Choose storage by data shape, lifetime, sensitivity, and query contract before
choosing a library.

| Storage Shape | Use When | Avoid When |
| --- | --- | --- |
| Relational or queryable store | Data has relationships, partial updates, filtering, sorting, joins, history, offline domain behavior, or referential integrity. | The data is only a few settings keys or can be recomputed from the server cheaply. |
| Typed persistent model or object store | The app owns stable typed models and a platform framework can handle the query/migration needs. | Callers would need raw persistence objects, framework annotations, or hidden context lifetimes. |
| Key-value preferences | Small non-sensitive settings, toggles, enum preferences, onboarding flags, display preferences, or simple feature settings. | Entity lists, relationship data, histories, partial updates, search, sync records, or secrets. |
| Secure platform storage | Credentials, refresh tokens, private keys, session secrets, or small sensitive auth material. | Queryable product data, large blobs, cache records, or values that need broad sharing. |
| Plain files or documents | User documents, imports/exports, media, attachments, snapshots, or interoperable formats with validation. | Secrets, silent cache records without invalidation, or structured app data that needs transactions. |
| Derived cache | Data can be recomputed or refetched and has a clear invalidation owner, TTL, or version. | The cache becomes the only copy of user work or permission-sensitive data without cleanup rules. |

Before adding persistence, name the source of truth, write owner, read owner,
cleanup trigger, migration owner, corruption behavior, and smallest test that
proves the boundary.

## Rules

- Define ownership before adding a second copy of data.
- Persist only stable state, not transient UI state.
- Version data that can outlive one app release.
- Make stale writes and conflict behavior explicit.
- Keep migration and backward compatibility near the storage boundary.
- Treat import/export as contracts with validation and failure states.
- Keep database rows, stored snapshots, serialized preferences, and secure
  storage payloads behind repository, data-source, or platform-adapter
  boundaries before they reach UI, domain policy, or public contracts.
- Map missing, unknown, deprecated, corrupted, and future-version stored values
  into typed defaults or typed failures at the storage boundary.
- Treat key-value storage as an interface for preferences, not as a small
  database. Promote to a typed object, relational store, or cache model when
  the data needs schema, relationships, partial updates, history, or queries.
- Store credentials and refresh tokens in secure platform storage, not in
  preference stores, plain files, logs, analytics, crash reports, or broad
  shared containers.

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
- Do not let UI or state owners call raw database, key-value, secure-storage,
  file, or cache APIs directly when repository or adapter boundaries already
  exist.
- Do not use a secure key-value store as the primary application database.
  Secure storage is for small sensitive secrets, not product collections.
- Do not store personal, credential, tenant, billing, entitlement, or permission
  state locally unless retention, revocation, cleanup, and sync behavior are
  explicit.

## Sync Questions

- Is this local-first, server-first, or offline-capable?
- What happens on stale save?
- Can two clients edit the same resource?
- What data is safe to cache?
- What must be cleared on logout, org switch, revoke, or downgrade?
- Does the chosen storage support the required query, transaction, migration,
  and corruption recovery behavior without leaking implementation types?
- Is the value preference-like, model-like, relational, secret, document-like,
  or only a cache?

## Tests

Cover load, save, update, delete, migration, corrupted data, quota/storage
failure, stale version, duplicate event, partial sync, conflict, retry,
rollback, import/export validation, secure-storage read/write failure,
preference defaulting, and logout/account-switch cleanup where relevant.
