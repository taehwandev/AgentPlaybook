---
keyflow_id: sys_app_architecture
status: stable
type: human-reviewed-needed
---

# Application Boundary Principles

Use for new features, boundary cleanup, or structure decisions.

For explicit UI/application/domain/cache state design, also use
`state-modeling.md`. For file/module ownership and `api`/`impl` splits, also
use `code-structure-ownership.md`. For SOLID, Interface Segregation, Dependency
Inversion, and DDD/domain-modeling fit, also use
`solid-design-principles.md`. For failure contracts, retry/recovery, and
user-visible failure states, also use `error-modeling.md`.
For API origins, callback URLs, redirect URIs, webhook endpoints, CORS origins,
deep link hosts, or asset hosts that vary by environment, also use
`runtime-url-configuration.md`.

## Shape

```text
UI -> State -> Domain -> Data / Platform
```

Keep files simple, but keep responsibilities named.

Before code crosses more than one file, folder, package, target, or module,
turn this shape into a concrete structure packet: which boundary owns UI,
state, domain policy, data, platform adapters, public contracts, and reusable
test support; where each role lives; what imports are allowed; what imports are
forbidden; and which test or check proves the boundary.

## Choose The Boundary

- Use a local UI boundary for display-only or one-screen interaction.
- Add a state owner when the screen has loading, empty, error, permission,
  submit, navigation, or async lifecycle states.
- Add a domain/use-case boundary when product rules, permissions, billing,
  tenant behavior, sync, or mutations need focused tests.
- Add repository/client boundaries when API, persistence, cache, filesystem, OS,
  browser, SDK, or external service calls need isolation.
- Promote to shared modules only when `common/skills/reusable-code-design/SKILL.md` says the
  caller contract is stable enough.
- Split into `api` and `impl` only when callers need a stable contract without
  implementation dependencies, navigation/registration crosses the boundary, an
  implementation can be swapped, or the split removes cycle/build coupling.

## Rules

- UI renders state and sends user intent.
- State layer owns loading, empty, error, success.
- Domain owns product rules and user actions.
- Data layer owns API, DB, cache, file, SDK calls.
- Platform layer owns OS permissions, lifecycle, windows, notifications.
- Caller-facing contracts stay role-sized: read-only callers do not receive
  write commands, display components do not receive feature policy, and domain
  rules do not depend on concrete transport, persistence, SDK, or UI types.
- Runtime configuration owns environment-specific API origins, callback URLs,
  redirect hosts, webhook endpoints, CORS origins, and asset hosts through the
  platform's normal config mechanism, not scattered source literals.
- One-off effects such as navigation, toast, focus, file download, permission
  prompts, and external launch should not be mixed with persistent UI state.

## Do Not

- Do not let UI own raw API clients, database rows, SDK objects, filesystem
  handles, shell calls, or platform permission payloads.
- Do not put UI rendering, state owner, domain policy, repository/client,
  platform adapter, DTO/schema, mapper, fixtures, and assertions into one
  folder or package without role boundaries and import rules.
- Do not add state, domain, repository, or adapter layers that only forward one
  method and add no rule, mapping, test boundary, or risk isolation.
- Do not expose fat services, repositories, contexts, component props, hook
  return objects, or module exports when a caller needs only a small role
  contract.
- Do not keep the same source of truth in UI state, cache, persistence, and
  server state without naming invalidation and conflict behavior.
- Do not hide product policy in reusable components, generic helpers, or shared
  data modules.
- Do not hard-code production, staging, preview, development, callback,
  redirect, webhook, CORS, or asset-host URLs in business logic, UI, generated
  clients, or platform adapters when they change by environment.

## Check

- Who owns this state?
- Is this UI logic, product logic, or server contract?
- Where are failure and permission states handled?
- What is the smallest useful test boundary?
- Which layer owns side effects and cancellation?
- Which platform config path supplies environment-specific runtime URLs?

## Verification

Verify the owner, not only the changed file:

- state owner transition test for loading, content, empty, error, permission,
  retry, refresh, and one-off effects when reachable
- mapper or adapter test for external, persisted, cached, or platform values
- contract or integration check when API, route, storage, event, or public
  package behavior changed
- UI or manual smoke path only after the state/data/side-effect boundary is
  covered or explicitly reported as residual risk
