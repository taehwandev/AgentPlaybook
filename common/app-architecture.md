---
keyflow_id: sys_app_architecture
status: review
type: human-reviewed-needed
---

# Application Boundary Principles

Use for new features, boundary cleanup, or structure decisions.

## Shape

```text
UI -> State -> Domain -> Data / Platform
```

Keep files simple, but keep responsibilities named.

## Choose The Boundary

- Use a local UI boundary for display-only or one-screen interaction.
- Add a state owner when the screen has loading, empty, error, permission,
  submit, navigation, or async lifecycle states.
- Add a domain/use-case boundary when product rules, permissions, billing,
  tenant behavior, sync, or mutations need focused tests.
- Add repository/client boundaries when API, persistence, cache, filesystem, OS,
  browser, SDK, or external service calls need isolation.
- Promote to shared modules only when `common/reusable-code-design.md` says the
  caller contract is stable enough.

## Rules

- UI renders state and sends user intent.
- State layer owns loading, empty, error, success.
- Domain owns product rules and user actions.
- Data layer owns API, DB, cache, file, SDK calls.
- Platform layer owns OS permissions, lifecycle, windows, notifications.
- One-off effects such as navigation, toast, focus, file download, permission
  prompts, and external launch should not be mixed with persistent UI state.

## Check

- Who owns this state?
- Is this UI logic, product logic, or server contract?
- Where are failure and permission states handled?
- What is the smallest useful test boundary?
- Which layer owns side effects and cancellation?
