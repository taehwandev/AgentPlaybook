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

## State Decision

```text
Need URL/share/back button? -> URL state
Need server refresh/cache? -> server state
Need user draft before submit? -> form/local state
Need many routes to know it? -> session provider/store
Need reload persistence? -> browser storage with migration
Need document/business mutation? -> domain/store/use-case boundary
```

## UiState

- Use discriminated unions or typed state objects for screen states instead of
  unrelated booleans and nullable fields.
- Keep one-off effects such as toast, navigation, focus, file download, and
  permission prompt separate from persistent state.
- Convert DTOs to UI models before JSX renders them.
- Keep protected access policy in named helpers or server/API boundaries; UI
  visibility is not authorization.

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
- Is failure visible to the user and testable?
