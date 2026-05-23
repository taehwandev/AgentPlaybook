---
keyflow_id: sys_3457cd5aad44
status: draft
type: ai-generated
---

# App Architecture Principles

Use for new features, boundary cleanup, or structure decisions.

## Shape

```text
UI -> State -> Domain -> Data / Platform
```

Keep files simple, but keep responsibilities named.

## Rules

- UI renders state and sends user intent.
- State layer owns loading, empty, error, success.
- Domain owns product rules and user actions.
- Data layer owns API, DB, cache, file, SDK calls.
- Platform layer owns OS permissions, lifecycle, windows, notifications.

## Check

- Who owns this state?
- Is this UI logic, product logic, or server contract?
- Where are failure and permission states handled?
- What is the smallest useful test boundary?
