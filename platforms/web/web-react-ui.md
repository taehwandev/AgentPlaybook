---
keyflow_id: sys_web_react_ui
status: review
type: human-reviewed-needed
---

# Web React UI

Use when creating, changing, moving, or reviewing React routes, pages, feature
components, hooks, forms, UI state, server-state wiring, reusable components, or
frontend tests.

For architecture choice, also read `../../common/architecture-design.md`. For
data ownership, cache, forms, mocks, and browser persistence, also read
`web-state-data.md`. For reusable UI extraction, also read
`../../common/reusable-code-design.md` and `../../common/design-system.md`.

## React Layers

Use this shape unless the repo has a stricter local pattern:

```text
Route/Page -> Feature Container -> Screen/View -> Section Component
-> Feature Component -> Design-System Primitive
```

- Route/page owns URL params, route loaders/actions, layout shell, auth/session
  boundary composition, and top-level data dependencies.
- Feature container owns one user workflow and wires server state, form state,
  permission checks, and mutations.
- Screen/view renders the whole workflow from explicit state and callbacks.
- Section components receive only the state and callbacks they need.
- Feature components may know display models but not raw DTOs, API clients,
  routers, storage, or analytics dispatch.
- Design-system primitives own visual and interaction contracts, not product
  policy or business workflows.

## Architecture Tracks

Choose the smallest track that protects the real risk:

| Track | Use When | Shape |
| --- | --- | --- |
| Simple Page | Static or local interaction only. | `Page -> component state` |
| Feature MVVM | Async data, form submit, permission state, or multi-state UI. | `Page/Container -> view model hook -> Screen` |
| Query/Mutation Boundary | Server state, cache invalidation, optimistic updates, or retries. | `Container -> query/mutation hooks -> client/mapper` |
| Clean Architecture | Domain policy, auth/tenant/billing, offline/sync, multiple clients, or reusable business rules. | `Screen -> feature hook/store -> use case -> repository/client` |
| Reducer/State Machine | Many events, explicit transitions, optimistic rollback, or complex form wizard. | `Component -> reducer/machine -> effects/use cases` |

Do not create a global store, use case layer, repository folder, or generic hook
only for ceremony. Add a layer when it isolates a real state owner, product
rule, side effect, or test boundary.

## Feature Folder Shape

A feature can use:

```text
features/members/
  routes/MemberSettingsPage.tsx     URL and route boundary
  MemberSettingsContainer.tsx       data, permissions, mutations
  MemberSettingsScreen.tsx          pure screen rendering
  components/                       feature-local components
  model/
    memberSettingsTypes.ts          UiState, actions, display models
    memberSettingsMappers.ts        DTO/domain -> UI models
    memberSettingsPolicy.ts         named product rules
  api/
    memberSettingsClient.ts         HTTP/SDK boundary
  hooks/
    useMemberSettings.ts            state/effect wiring
  __tests__/
```

Adapt names to the repo's framework. Next.js, Remix, React Router, Expo Web,
and custom routers may place route files differently; keep the same ownership
boundaries.

## UiState Shape

Represent UI states explicitly. Prefer discriminated unions for mutually
exclusive screen states:

```ts
type ProfileUiState =
  | { kind: "loading" }
  | { kind: "content"; profile: ProfileViewData }
  | { kind: "empty" }
  | { kind: "permissionDenied" }
  | { kind: "offline"; cached?: ProfileViewData }
  | { kind: "error"; error: ErrorViewData };
```

Use structs with typed sub-states when content can have independent regions:

```ts
type CheckoutUiState = {
  form: CheckoutFormState;
  submit: "idle" | "submitting" | "succeeded" | "failed";
  entitlement: EntitlementState;
  banner?: BannerState;
};
```

Rules:

- Loading, empty, error, permission denied, offline, disabled, and submitted
  states must be representable when the flow can reach them.
- Avoid impossible boolean combinations such as `isLoading && error && data`.
- Convert DTOs before rendering. JSX should consume display models or UI models,
  not transport details.
- Keep protected access rules in named helpers or policy functions. UI hiding is
  not authorization.
- Keep one-off effects such as toast, navigation, focus, and file download
  separate from persistent state.

## Container And Screen Split

Containers may:

- Read URL params, route data, session, feature flags, permissions, and query
  results.
- Call framework query/mutation hooks or feature hooks.
- Map server state and mutation state into `UiState`.
- Pass callbacks such as `onRetry`, `onSubmit`, `onInvite`, or `onClose`.

Screens should:

- Receive `state`, callbacks, optional slots, and simple display models.
- Render states and emit intent.
- Avoid direct fetch calls, storage reads, router mutation, analytics dispatch,
  and permission policy evaluation.
- Keep local state only for presentation details such as menu open, dialog open,
  focus, draft text before commit, selected tab, hover, or transient animation.

Leaf components should receive the smallest data shape they need. Do not pass a
whole `UiState` into a button, row, badge, or card when a smaller model works.

## Hooks

Use hooks for reusable state/effect wiring, not hidden product policy.

Good hook contracts:

```ts
const { state, submit, retry } = useCheckoutSession(orderId);
const policy = usePermissionPolicy(session);
```

Rules:

- Hook names should describe the state owner or integration boundary.
- Hooks that fetch or mutate server state should delegate HTTP/SDK details to a
  client and map DTOs at the boundary.
- Effects must have dependencies, cleanup, and abort behavior when relevant.
- Do not use `useEffect` to store derived state that can be calculated during
  render.
- Do not add context/provider state for one route's temporary interaction.

## Server State, Forms, And Mutations

- Use the repo's query/cache tool for server state when one exists. Do not copy
  server state into local state without a sync reason.
- Define invalidation after create, update, delete, invite, role, permission,
  billing, or tenant changes.
- Put optimistic updates behind explicit rollback behavior.
- Forms should model validation errors, dirty state, submit pending, success,
  permission denied, and network error.
- Do not put secrets or protected tokens in `localStorage`, `sessionStorage`,
  query params, logs, or client-visible config.

## Component Reuse

Before extracting a component or hook:

- Are there at least two real call sites or a stable design-system contract?
- Can it be named without the original feature name?
- Are copy, routes, analytics, permissions, and business rules owned by callers?
- Can Storybook, examples, component tests, or fixtures show the important
  states without feature setup?
- Will extraction remove duplicated fixes without creating a flag-heavy API?

Keep sections local when reuse would require `variant`, `mode`, `source`, and
many nullable options just to support unrelated screens.

## Verification

Choose the closest checks configured in the repo:

- TypeScript/typecheck for changed files.
- Unit tests for policy, mapper, reducer, state machine, and hook behavior.
- Component tests with Testing Library using role, label, visible text, and
  user interaction.
- E2E tests with Playwright/Cypress for critical flows, routing, auth,
  permissions, forms, and mutation paths.
- Accessibility checks for labels, roles, focus order, keyboard operation,
  contrast, text scaling, and dialog/menu behavior.
- Visual checks or screenshots for layout, responsive states, long text, empty
  state, error state, loading state, and dark mode when affected.

Review the final diff for raw fetch calls inside components, DTOs leaking into
JSX, duplicated permission checks, global providers for local state, missing
failure states, and reusable components that absorbed product-specific policy.
