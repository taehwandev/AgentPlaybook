---
keyflow_id: sys_d3516f7590e2
status: review
type: ai-generated
---

# Web Architecture

Use for React web UI work: routing, pages, components, hooks, forms, data fetching, browser storage, and browser UX.

Also use:
- `web-react-ui.md` for route/page, container/screen, hook, `UiState`, reusable
  component, and clean-architecture implementation details.
- `web-state-data.md` for state, cache, forms, API clients, mocks, and browser persistence.
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
