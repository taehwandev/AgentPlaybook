---
keyflow_id: sys_d3516f7590e2
status: review
type: ai-generated
---

# Web Architecture

Use for React web UI work: routing, pages, components, hooks, forms, data fetching, browser storage, and browser UX.

Also use:
- `web-code-structure.md` for route/file ownership, feature folder shape,
  import direction, and server/client code boundaries.
- `web-react-ui.md` for route/page, container/screen, hook, `UiState`, reusable
  component, and clean-architecture implementation details.
- `web-state-data.md` for state, cache, forms, API clients, mocks, and browser persistence.
- `web-design-system.md` for web tokens, primitives, component variants,
  styling ownership, and visual adoption/migration.
- `web-accessibility-i18n.md` for text, focus, keyboard, dialogs, responsive copy, and localization.
- `web-security.md` for auth, browser storage, tokens, redirects, embeds, uploads, and client-visible config.
- product-pattern docs for auth, invite, billing, entitlement, or tenant work.

## Boundaries

```text
Route/Page -> Feature -> Component -> Hook -> Service/Client
```

- Route/Page owns URL params, route loaders, shell layout, and data boundary composition.
- Feature owns one user workflow, such as member management, document creation, invite, checkout, or settings.
- Component renders UI and emits intent. It should not own product policy.
- Hook owns reusable state/effect wiring, not hidden business rules.
- Service/Client owns HTTP, SDK, storage, and DTO conversion boundaries.
- Split containers that wire state/effects from screens/components that render
  explicit `UiState` and callbacks.

## Web Structure Defaults

- Keep framework route files thin. They compose metadata, layout, route
  parameters, server/client boundaries, and feature containers.
- Keep workflow behavior in feature-local containers, hooks, model, policy,
  mapper, and client modules before promoting it to shared code.
- Keep screens render-only where practical: explicit state in, callbacks out.
- Keep design-system primitives policy-free and importable without feature data,
  routers, analytics, or API clients.
- Keep server-only modules, secrets, SDK clients, database access, and trusted
  mutations out of client components.
- Use a shared module only when the caller contract is stable. Otherwise keep
  code local to the route or feature.

## Next.js App Router Defaults

When the repo uses Next.js App Router, keep the framework-specific choices
explicit:

- Prefer Server Components for internal server-side reads. Do not add an API
  route only to let a page read data that can be fetched safely on the server.
- Use Server Actions for UI-triggered mutations and form submissions. Use Route
  Handlers for external HTTP contracts, public or mobile APIs, webhooks, and
  cacheable GET semantics.
- Keep `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`,
  `not-found.tsx`, `route.ts`, and parallel route fallbacks as composition or
  boundary files, not feature implementations.
- Default to the Node.js runtime. Add Edge runtime only when there is a real
  edge-latency requirement and every dependency is Edge-compatible.
- Follow the repo's installed Next.js version for async request APIs. In Next.js
  15 and newer, `params`, `searchParams`, `cookies()`, and `headers()` are
  async boundaries and must be awaited or consumed with the supported React
  pattern.
- Treat `redirect`, `permanentRedirect`, `notFound`, `forbidden`, and
  `unauthorized` as framework control flow. Do not swallow them in broad
  `catch` blocks.
- Avoid server data waterfalls. Start independent reads in parallel, stream
  independent regions with Suspense, or use a preload pattern when the repo
  already has one.

## React State Placement

- Local UI state: modal open, menu open, selection, draft input.
- URL state: filters, selected tab, shareable navigation state.
- Form state: validation, dirty state, submit status, field errors.
- Session state: current user, org/workspace, permission, entitlement.
- Server state: query/cache layer when the repo has one.
- Browser storage: only with explicit persistence, migration, default, and cleanup rules.

## Rules

- Keep server state separate from local UI state.
- Keep form, modal, and selection state near the interaction owner.
- Model loading, content, empty, error, permission denied, offline, disabled,
  and submitted states explicitly when the flow can reach them.
- Do not repeat raw fetch calls inside components.
- Convert DTOs before they leak into JSX.
- Use existing design system primitives first.
- Do not add a global provider for one screen's temporary state.
- Do not use `useEffect` to store derived state that can be calculated during render.
- Cleanup subscriptions, timers, abortable requests, and event listeners.

## Service-Ready UI

- Mock data belongs behind a clear fixture or client boundary.
- Local role, billing, or auth toggles must be named and treated as demo-only.
- UI gating is not authorization; command/API boundaries must also block.
- Invite/share UI must not imply real access control unless backend enforcement exists.
- Prefer typed roles, permissions, and entitlements over scattered booleans such as `isAdmin`.

## Refactor Signals

- One component owns fetch, permission, form, modal, table, and rendering.
- Permission checks repeat inside JSX instead of named policy helpers.
- API errors are mapped differently across screens.
- Server state is copied into local state without a sync reason.
- Hardcoded mock members, plans, projects, or invites are mixed with real UI workflow.
