---
keyflow_id: sys_web_code_structure
status: review
type: human-reviewed-needed
---

# Web Code Structure

Use when deciding where React/web files live, how feature folders are shaped,
how route files compose data and UI, or how imports should flow across a web
application.

Also use:
- `../../common/code-structure-ownership.md` for ownership level and `api`/`impl`
  decisions.
- `../../common/reusable-code-design.md` before promoting feature code into a
  shared package or reusable module.
- `../../common/component-api-design.md` before extracting reusable components
  or hooks.
- `web-react-ui.md` for container/screen, hook, `UiState`, and React
  implementation details.
- `web-state-data.md` for query/cache, API clients, forms, mocks, and browser
  persistence.

## Default Boundary

Prefer feature-local structure until a real caller or design-system contract
needs a shared boundary.

```text
route/page -> feature container -> screen/view -> feature components
-> design-system primitives -> platform/shared utilities
```

- Route/page files own URL, route params, metadata, loader/action composition,
  layout shell, and route-level error/loading boundaries.
- Feature containers own one workflow and compose session, permission, server
  state, form state, mutations, and analytics intent.
- Screens/views render explicit state and callbacks without importing routers,
  API clients, storage, or product policy.
- Feature components are local by default. They may know display models for the
  feature, but not raw DTOs or transport details.
- Design-system primitives are shared UI contracts. They do not know routes,
  products, analytics event names, tenant policy, billing, or auth rules.
- Platform/shared utilities are dependency-light helpers with stable ownership.

## Recommended Feature Shape

Adapt names to the framework, but keep ownership clear:

```text
features/billing/
  BillingSettingsContainer.tsx
  BillingSettingsScreen.tsx
  components/
    PlanSummaryCard.tsx
    SeatLimitNotice.tsx
  model/
    billingSettingsTypes.ts
    billingSettingsMappers.ts
    billingSettingsPolicy.ts
  api/
    billingSettingsClient.ts
  hooks/
    useBillingSettings.ts
  __tests__/
```

Framework route files stay in the framework route tree when required:

```text
app/account/billing/page.tsx
app/account/billing/loading.tsx
app/account/billing/error.tsx
```

Keep those files thin. They should compose the feature, not become the feature.

## Import Direction

Use repo-local aliases and folder names first, but protect these dependency
directions:

```text
routes import features and shared
features import their own model/api/hooks/components and shared
feature components import design-system primitives
shared utilities do not import features
design-system primitives do not import features
server-only modules do not import client-only modules
client components do not import server-only modules
```

Do not create a `common`, `shared`, or `utils` folder for unrelated code with no
single owner. If a shared folder has many unrelated reasons to change, split it
by responsibility or keep code feature-local.

## Server And Client Boundaries

For frameworks with server/client components, server actions, loaders, or edge
routes:

- Keep server-only data fetching, secret-bearing SDKs, and trusted mutations in
  server boundaries.
- Keep interactive state, browser APIs, focus, drag/drop, media queries, and
  event listeners in client boundaries.
- Pass explicit public DTOs or display models from server to client components.
  Serialization is required for transport, but it is not enough to decide which
  fields are safe for browser-visible code.
- Do not pass raw database rows, secrets, request objects, SDK clients, or
  framework server types into client UI.
- Keep DTO mappers near the feature/server boundary when fields depend on
  viewer, tenant, visibility, or role. Shared serializers may convert dates and
  transport shapes, but they must not replace field allowlists.
- Do not make a component client-only just because one small child needs
  interactivity. Isolate the interactive child.
- Treat hydration mismatch as a boundary issue: time, locale, random values,
  browser-only data, and persisted preferences need deterministic defaults.

## Shared Extraction

Move code upward only when the contract is stable enough:

- `components/ui` or equivalent: reusable primitives and composed controls with
  accessibility and visual-state contracts.
- `components/<domain>`: reusable product patterns that intentionally know a
  domain workflow.
- `lib` or `shared`: pure helpers, formatters, mappers, and platform adapters
  with clear ownership.
- `features/<name>`: workflow-local UI, state, policy, and data wiring.

Before extraction, check:

- Are there at least two real call sites or a stable platform/design-system
  contract?
- Can the extracted code be named without the first feature's name?
- Are copy, routes, analytics, auth, tenant, billing, and product policy still
  owned by callers or feature policy modules?
- Can the extracted unit be tested or previewed without booting the whole app?

## Refactor Recipe

When restructuring an oversized web feature:

1. Inventory route files, data sources, raw DTOs, browser storage, providers,
   mutations, and tests.
2. Name the workflow owner and the public entry points.
3. Extract display models and mappers before moving JSX.
4. Split route/page composition from feature container behavior.
5. Split screen rendering from data/effect wiring.
6. Move feature-local components under the feature before promoting anything to
   shared UI.
7. Replace repeated inline permission or billing booleans with named policy
   helpers.
8. Typecheck or run focused tests after each boundary move.

Do not mix broad moves with product behavior changes unless the behavior change
is an explicit acceptance point.

## Verification

For web structure changes, verify the boundary:

- typecheck or build the affected workspace
- lint import direction and hooks rules when configured
- run focused tests for mappers, policy helpers, reducers, and hooks
- run component or route tests for loading, content, empty, error, and
  permission-denied states
- inspect final imports for raw API clients, SDKs, DTOs, or product policy
  leaking into screens and primitives

Report which structure was chosen and why: feature-local, shared component,
shared utility, route boundary, or `api`/`impl` split.
