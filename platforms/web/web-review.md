---
keyflow_id: sys_0678d6c5f03c
status: review
type: ai-generated
---

# Web Review

Use for React/web UI, browser behavior, and frontend PR review.

## Review

- Check route/data boundaries, cache invalidation, form validation, and error states.
- Check route/file ownership and import direction against
  `web-code-structure.md` when files moved or a feature was split.
- Check route/page, container/screen, hook, and component boundaries against
  `web-react-ui.md` when React UI changed.
- Check design-system tokens, primitives, variants, and visual states against
  `web-design-system.md` when shared UI or styling changed.
- Check server-to-client payloads, server actions, API responses, browser
  storage, and cache headers against `web-state-data.md` and `web-security.md`
  when data crosses into browser-visible code.
- Confirm typed UI state represents loading, content, empty, error, permission
  denied, offline, disabled, and submitted states when applicable.
- Verify accessibility: labels, roles, focus order, keyboard use, contrast.
- Check responsive layout for mobile, tablet, desktop.
- Ensure permission and entitlement checks are not UI-only.
- Look for duplicated fetch/error/permission logic in components.
- Check whether mock data, demo toggles, and localStorage state are clearly separated from real service behavior.

## React Checks

- Component state ownership is local unless multiple screens actually need it.
- Effects have dependencies, cleanup, and abort behavior where relevant.
- Derived state is not stored unnecessarily.
- Context/provider additions have cross-route ownership, not one-screen convenience.
- Hooks expose intent and state, not hidden product policy.
- Form submit paths handle pending, success, validation error, permission denied, and network error.
- Server/client boundaries do not leak secrets, server SDKs, raw database rows,
  or trusted mutations into client components.
- Server-rendered props, loader data, server action results, and API responses
  use allowlisted public DTOs instead of recursive serialization of raw records.
- Memoization is used for performance or identity, not to compensate for
  missing state ownership or effect dependencies.

## Next.js App Router Checks

- App Router special files stay role-sized and do not absorb full feature
  implementations.
- Internal reads use Server Components where practical; UI mutations use Server
  Actions; Route Handlers are reserved for external/public HTTP contracts,
  webhooks, REST endpoints, streams, uploads, or GET cache semantics.
- Client components are not async components, and server-to-client props are
  serializable public display models.
- `params`, `searchParams`, `cookies()`, and `headers()` follow the installed
  Next.js version's async API contract.
- `redirect`, `permanentRedirect`, `notFound`, `forbidden`, and `unauthorized`
  are not swallowed by broad error handling.
- Edge runtime is used only with an explicit latency or deployment need and
  compatible dependencies.
- `useSearchParams()` and dynamic-route `usePathname()` have the Suspense
  boundary required by the framework version.
- `next/image`, `next/font`, metadata, scripts, cache/revalidation, and
  self-hosting behavior are checked when those files or public routes change.

## Structure Checks

- Framework route files are thin composition boundaries, not oversized feature
  implementations.
- Feature folders contain cohesive workflow code: container, screen,
  feature-local components, model/mappers/policy, hooks, API/client, and tests
  when needed.
- Shared UI does not import feature modules, routers, analytics event names,
  permission policy, API clients, or DTOs.
- Shared utilities have a clear owner and do not become a mixed `common` dump.
- Import direction matches route -> feature -> shared/design-system, with
  server-only and client-only modules separated.

## Design-System Checks

- Tokens are semantic and cover light/dark, disabled, focus, error, selected,
  and responsive states when applicable.
- Primitives define accessibility, keyboard, focus-visible, loading, disabled,
  invalid, selected, and expanded behavior.
- Reusable component APIs use explicit callbacks, slots, controlled state, and
  semantic variants instead of page-specific boolean flags.
- Long text, localization, constrained containers, and theme changes do not
  break control size, card layout, tables, dialogs, or toolbars.
- Product-specific copy, route decisions, analytics, auth, tenant, and billing
  policy remain in callers or feature policy modules.

## Service Checks

- Invite, share, billing, auth, and role UI do not promise server enforcement that does not exist.
- Buttons hidden by permission are also blocked at action/API boundary.
- Role and plan checks use named helpers or policy functions instead of repeated JSX booleans.
- Browser storage is not the source of truth for protected access.
- Server actions and API routes re-derive user, tenant, role, ownership,
  visibility, quota, and entitlement from trusted server state rather than
  client-provided fields.
- Browser-visible payloads omit encrypted PII, hashes, internal role data,
  permission graphs, billing internals, audit metadata, private tokens, storage
  keys, and raw provider responses unless an explicit product contract requires
  them.
- Live, token-backed, personalized, draft, follower-only, admin, or private
  responses are not sent with public cache headers.
- CORS, redirect, upload signing, embed rendering, and revalidation endpoints are
  scoped and validated before accepting client input.
- Environment-specific API origins, callback URLs, redirect hosts,
  WebSocket/EventSource endpoints, CORS origins, and asset hosts are supplied
  through framework/deployment config, with client-visible values treated as
  public and credentials kept server-side.

## SEO And AI Search Checks

When a public route, marketing page, content page, profile, article, docs page,
or share surface changed, load `common/public-discovery.md` and review it as a
public output contract.

- Metadata title, description, canonical URL, locale alternates, robots policy,
  Open Graph, and social preview output match the intended public page.
- Sitemap and robots behavior include only pages that unauthenticated readers
  and crawlers should discover.
- Public content is crawlable/indexable and not hidden behind blocked scripts,
  private client state, or login-only fetches.
- Structured data, when present, describes visible public content and excludes
  private fields, draft state, internal IDs, and hidden claims.
- Generative AI search work improves normal SEO fundamentals: useful
  non-commodity content, clear headings, technical crawlability, page
  experience, media quality, and duplicate-content reduction.
- Font-loading or third-party-resource claims are verified against the actual
  implementation path: `next/font` or bundler plugins, CSS imports, HTML
  stylesheets, client-injected stylesheet links, icon font loaders, route-specific
  components, server-only OG image font fetches, and browser network traces when
  practical.
- Do not add `llms.txt`, AI-only mirrors, forced chunking, query-variant page
  farms, or inauthentic mentions as a Google Search optimization unless
  repo-local policy names another consumer and verification path.

## Tools

- Static: TypeScript, ESLint, framework lint.
- Structure: import-boundary lint, route snapshots, or final import inspection
  when the repo lacks automated boundary checks.
- Unit: Vitest or Jest for policy, mapper, hook, reducer.
- Component: Testing Library by role, label, visible text, interaction.
- UI/E2E: Playwright for navigation, auth, forms, permissions, critical flows.
- A11y: axe or Playwright accessibility checks when available.
- Discovery: framework metadata output, sitemap/robots snapshots, Rich Results
  Test, Search Console, PageSpeed Insights, route snapshots, or network/resource
  inspection when practical.

## UI Test Focus

- User can complete the main flow.
- Loading, empty, error, and permission-denied states render correctly.
- Container/screen split or equivalent keeps data/effects out of presentational
  components.
- Keyboard-only path works for forms, dialogs, menus, tables.
- No text overflow or layout break across key viewport sizes.
- Denied users cannot trigger the protected command, not only fail to see the button.
