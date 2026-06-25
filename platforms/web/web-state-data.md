---
keyflow_id: sys_f93ed83d32a3
status: review
type: ai-generated
---

# Web State And Data

Use when touching React client state, server state, forms, API clients, cache, mocks, or browser persistence.

For React container/screen boundaries, hook contracts, and typed `UiState`
examples, also use `web-react-ui.md`.

## Defaults

- Server state belongs in query/cache tools when the repo has one.
- UI state stays near the component that owns the interaction.
- Session state owns user, org/workspace, auth, permission, and entitlement.
- Form state owns validation, dirty state, submit status, and field errors.
- Browser storage needs an explicit reason, schema/default behavior, cleanup, and migration plan.
- Data that crosses from server to browser needs a named public DTO or display
  model. Serialization is not a privacy or authorization boundary.

## State Decision

```text
Need URL/share/back button? -> URL state
Need server refresh/cache? -> server state
Need user draft before submit? -> form/local state
Need many routes to know it? -> session provider/store
Need reload persistence? -> browser storage with migration
Need document/business mutation? -> domain/store/use-case boundary
```

## Server-To-Client Data Boundary

Server-rendered props, loader data, server action results, and API responses all
become browser-visible data. Treat them as the same boundary.

- Map raw database rows, ORM records, Firestore documents, session objects, auth
  claims, and service responses into explicit public DTOs before returning them.
- Prefer allowlisted DTO builders such as `toPublicProfileDto` or
  `toPostDetailViewModel` over recursive "serialize everything" helpers.
- Do not send encrypted PII, hashes, internal role bookkeeping, permission
  graphs, billing internals, invite tokens, signed secret material, moderation
  state, or audit metadata unless the UI has a documented user-visible need.
- Keep DTO fields stable and typed. If a field is not rendered or needed by a
  client interaction, remove it before crossing the boundary.
- Convert timestamps, URLs, rich-text HTML, and asset references in the mapper so
  JSX and hooks do not depend on transport-specific shapes.
- Redact or normalize errors before returning them to client code. Avoid
  revealing whether private resources exist.
- Use the same DTO review for server actions as for REST/GraphQL routes. A
  server action is callable from the browser and must not return raw trusted
  records.

## Next.js Data Pattern

When Next.js App Router is the framework:

- Use Server Components for internal reads that can run on the server without a
  browser round trip.
- Use Server Actions for UI-originated mutations. Keep returned values small,
  serializable, and public.
- Use Route Handlers for external clients, third-party webhooks, REST-style
  contracts, public endpoints, file or stream endpoints, and cacheable GET
  semantics.
- Do not use Server Actions as the default read path from client components.
  They are POST-based mutation boundaries and do not provide normal GET cache
  behavior.
- When a client component needs initial data, prefer passing a public display
  model from the server. Use client-side fetch only when browser-owned state,
  polling, live updates, or an existing query/cache layer requires it.

## API And Mutation State

- Client requests send user intent and stable resource identifiers. The server
  re-derives user, tenant, role, ownership, visibility, price, quota, and feature
  entitlement from trusted state.
- Never trust client-provided author IDs, tenant IDs, roles, plan names, prices,
  cache tags, or storage paths as authorization facts.
- Mutations return the smallest result that lets the UI update. Avoid returning a
  whole refreshed entity when a count, status, or new ID is enough.
- Keep optimistic state behind rollback paths and server conflict handling.
- Use schema validation at the boundary for request payloads and response DTOs
  when the repo has a validation tool.

## Cache And Invalidation

- Cache public DTOs, not raw records that may later be reused for private
  viewers.
- Cache keys and tags must include every access dimension that can change the
  output: viewer, tenant/workspace, role, locale, visibility, experiment, and
  content version.
- Do not put private, follower-only, draft, admin, or session-specific responses
  behind public CDN cache headers.
- Revalidate or bypass caches on auth change, logout, org switch, role or plan
  change, visibility change, publish/unpublish, deletion, and moderation action.
- Mark live, personalized, token-backed, or presence-style responses as private
  and no-store unless there is a documented safer cache model.

## UiState

- Use discriminated unions or typed state objects for screen states instead of
  unrelated booleans and nullable fields.
- Keep one-off effects such as toast, navigation, focus, file download, and
  permission prompt separate from persistent state.
- Convert DTOs to UI models before JSX renders them.
- Keep protected access policy in named helpers or server/API boundaries; UI
  visibility is not authorization.
- Split high-churn state, such as live messages, presence, typing, timers,
  progress, drag, focus, hover, animation, and list windows, from coarse screen
  `UiState` when it would cause unrelated React nodes to re-render.
- Keep state near the smallest component, hook, cache selector, or external
  subscription that owns its update cadence. Do not pass a whole screen
  `UiState` or query result through the tree when a section or row model works.

## Browser Storage

- Do not store secrets, service keys, or sensitive tokens in localStorage.
- Demo role/billing toggles must not be treated as real authorization.
- Clear session-derived state on logout, org switch, membership revoke, and role change.
- Store stable user preferences separately from server-owned permission or billing state.
- Define fallback behavior for missing, malformed, or old stored values.

## Mock To Real Boundary

- Keep fixture data close to tests, stories, demos, or a clearly named mock client.
- Avoid hardcoded production UI lists that look server-backed.
- Replace mock hooks with real clients through the same return shape where practical.
- Do not let mock status values become unreviewed product contracts.

## Check

- Who owns this state?
- What invalidates this data?
- Is optimistic update needed or risky?
- Does logout, org switch, permission change, or plan downgrade clear or refresh it?
- Are DTOs converted before rendering?
- Is the server-to-client payload an allowlisted public DTO rather than a raw
  record that was only serialized?
- Do cache keys, tags, and headers match the visibility and viewer dimensions?
- Is failure visible to the user and testable?

## Tests

- Unit test DTO mappers for sensitive-field omission, timestamp conversion, URL
  normalization, and malformed input.
- Add contract tests for server actions or API routes that verify unauthorized,
  cross-tenant, private, draft, and stale-permission paths.
- Snapshot or assert cache headers for public, private, live, and personalized
  responses.
