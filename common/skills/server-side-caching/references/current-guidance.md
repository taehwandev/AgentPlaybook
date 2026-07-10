---
keyflow_id: sys_server_side_caching
status: stable
type: human-reviewed-needed
---

# Server Side Caching

Use when touching server-rendered data, API response caching, framework data
cache, request memoization, edge/CDN cache, database query cache, materialized
read models, or cache invalidation.

Server-side cache safety is determined by the cache key and invalidation path,
not by where the cache lives.

## Cache Types

- Request-local memoization: deduplicates work inside one request or render.
- Process memory cache: shared inside one server process; unsafe for durable
  correctness unless the repo defines lifetime and invalidation.
- Framework/server data cache: framework-managed persistent or semi-persistent
  cache with keys, tags, TTL, or revalidation.
- Edge/CDN cache: shared across users and locations; safest for public,
  deterministic responses.
- Database/query result cache: stores expensive query results or read models.
- Materialized/denormalized read model: precomputed data that becomes a product
  contract and needs write-side maintenance.

## Cache Only When

- The response is deterministic for the full cache key.
- Data is public or safely shared across every viewer that can hit the key.
- Every personalization dimension is represented in the key or filtered after
  reading from a safe shared cache.
- Source writes, deletes, permission changes, and entitlement changes have a
  clear invalidation, bypass, or refresh path.
- The product accepts the possible stale-data window.
- The cache meaningfully reduces latency, cost, rate-limit pressure, or load.

Authenticated route does not automatically mean uncacheable data. Public route
does not automatically mean public cache.

## Do Not Cache When

- The response depends on the current viewer, session, role, tenant, locale,
  entitlement, feature flag, or permission but the key does not include that
  dimension.
- The response includes secrets, tokens, cookies, one-time codes, CSRF values,
  nonces, credentials, private URLs, or signed upload/download URLs.
- Write-after-read consistency is required for the user flow.
- Auth, role, membership, billing, entitlement, invite, or tenant state is
  changing and no cache bypass or invalidation path exists.
- Denied, empty, or not-found responses could reveal, hide, or persist private
  resource state incorrectly.
- The invalidation owner is unknown.
- The cache would make local development, tests, or incident recovery ambiguous
  without a documented bypass.

## Cache Key Rules

Include every dimension that can change output:

- tenant, organization, workspace, project, or account
- verified user, viewer, role, permission, or entitlement when output differs
- locale, timezone, currency, country, or region
- query, filter, sort, pagination cursor, search text, and page size
- feature flag, experiment, preview mode, or release channel
- schema, API, DTO, or read-model version when response shape changes

Never trust client-provided user id, role, tenant, price, quota, or entitlement
as a cache-key input without server verification.

## Invalidation Rules

- Writes must identify affected cache keys, tags, read models, or bypass paths.
- Permission, role, entitlement, invite accept/revoke, logout, account switch,
  tenant switch, downgrade, and account deletion must refresh, clear, bypass, or
  narrow relevant caches.
- TTL is not a substitute for invalidation when stale data can leak private data,
  corrupt billing/permission UX, or mislead a workflow after a write.
- Negative caching for denied, not-found, or empty results needs explicit TTL and
  privacy review.
- Stale-while-revalidate needs product acceptance for stale reads.
- Materialized read models need a repair, backfill, or reconciliation path.

## Verification

Verify the cache behavior, not only the uncached path:

- cache hit returns the correct shared data
- cache miss/fill includes the intended key dimensions
- create, update, delete, permission change, and entitlement change invalidate or
  bypass stale data as relevant
- user A cannot receive user B's viewer-specific result
- tenant, locale, query, sort, filter, and pagination variants do not collide
- private, denied, not-found, or empty responses are not cached into a broader
  public or shared path
- stale data window is documented or tested when it affects product behavior

For high-risk cache changes, report the cache type, key dimensions,
invalidation path, verification command or manual scenario, and residual stale
data risk.
