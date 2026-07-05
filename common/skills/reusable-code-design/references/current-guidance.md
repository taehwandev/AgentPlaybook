---
keyflow_id: sys_reusable_code_design
status: review
type: human-reviewed-needed
---

# Reusable Code Design

Use when creating, moving, extracting, or reviewing code that should be reused
across screens, features, modules, packages, services, or apps.

For file/module ownership and `api`/`impl` split choices, also use
`code-structure-ownership.md`. For SOLID, Interface Segregation, Dependency
Inversion, and DDD/domain-modeling fit, also use
`solid-design-principles.md`. For reusable UI, hook, widget, control, or
component-like API design, also use `component-api-design.md`.

Reusable code is an ownership decision, not only a DRY decision. Extract only
when the caller contract is stable enough to make future changes easier.

## Reuse Ladder

Move code upward only as the contract becomes clearer:

```text
local helper -> file-private unit -> feature component -> feature common
-> platform/design-system primitive -> shared package/module -> public API
```

Prefer the lowest level that removes real duplication while keeping ownership
obvious. Do not promote code to a shared module just because two call sites look
similar for one sprint.

## Extraction Criteria

Extract when most of these are true:

- At least two real call sites need the same behavior or UI contract.
- The shared part can be named without product-specific or caller-specific words.
- Inputs, outputs, errors, loading states, and side effects are explicit.
- The unit can be tested or previewed without booting unrelated systems.
- The caller keeps product policy, copy, routing, permissions, and analytics.
- The shared unit can change internally without changing caller behavior.
- The new boundary reduces coupling, diff size, or repeated bug fixes.

Keep code local when reuse would require flags for every caller, nullable knobs,
hidden global state, or product-specific branches.

## Contract Shape

Reusable units should prefer:

- Plain input models or parameters instead of whole state holders.
- Explicit callbacks, commands, or return values instead of hidden side effects.
- Typed result/error/state models instead of string matching or scattered flags.
- Dependency interfaces or adapters instead of direct framework/global access.
- Role-sized interfaces, props, callbacks, and exports so each caller depends
  only on the behavior it needs.
- Stable names that describe the reusable role, not the first feature that used it.
- Examples, previews, fixtures, or focused tests that show normal and edge states.
- Export surfaces grouped by contract family, so callers can import routes,
  events, schemas, DTOs, commands, adapters, fixtures, or assertions without
  unrelated runtime dependencies.

Avoid reusable APIs that accept repositories, activities, routers, request
objects, raw environment variables, or feature-specific DTOs unless that is the
documented owner boundary.

## Cross-Platform Reuse

Reusable code that may apply across apps or platforms must separate the stable
capability from the platform runtime that executes it:

- Put pure contracts, value types, typed errors, route/event descriptions,
  mappers, policies, and deterministic helpers in the shared/core layer.
- Put Android, iOS, web, server, desktop, Compose, SwiftUI, React, browser,
  filesystem, process, SDK, and database details behind platform adapters.
- Keep UI runtime commonization separate from pure core contracts. A helper that
  needs a UI lifecycle, toast host, alert presenter, Activity launcher, browser
  window, or platform navigation stack belongs in the platform app/UI boundary.
- Prefer suspend APIs, typed commands, callbacks, ports, or small interfaces for
  side-effect ownership. Do not store caller-owned coroutine scopes,
  lifecycle owners, controllers, routers, or platform contexts in generic
  shared code unless that is the explicit adapter contract.
- Provide fixtures, recording fakes, assertion subjects, and contract tests that
  depend on the API surface only. Test support is part of the reusable contract,
  not a reason to import production implementation modules.
- Use narrow value types for important identifiers and policy inputs when the
  language supports them. Avoid passing primitive strings or maps through a
  shared API when the meaning carries a product or security invariant.

Do not promote code to a common package if the shared API still needs
caller-specific flags, product copy, route decisions, analytics labels,
permission policy, billing rules, or platform-specific fallback branches.

Do not make a cross-platform package look reusable by exporting every contract
family from one file or namespace. A shared package should make pure contract
families obvious, then put platform runtimes behind adapters owned by Android,
iOS, web, server, desktop, or the repo's equivalent platform boundary.

## Ownership Boundaries

- `core`, `common`, `shared`, or package-level modules own reusable contracts,
  primitives, mappers, policies, and adapters.
- Feature modules own product copy, route decisions, analytics labels,
  permission prompts, and screen orchestration.
- Design-system modules own visual primitives and interaction contracts, not
  product workflows or domain policy.
- Data/platform modules own persistence, network, filesystem, OS, and external
  service integration behind adapters.
- Public packages or SDKs require compatibility, versioning, docs, and migration
  notes before exposing new APIs.

## Naming

Use names that match the abstraction level:

- Local: `formatDateLabel`, `PlaceRowContent`.
- Feature common: `PlacePreviewSheet`, `ChatComposer`.
- Design-system primitive: `AppButton`, `MetricTile`, `SearchField`.
- Domain policy: `PermissionPolicy`, `BillingEntitlement`, `RouteMatcher`.
- Platform adapter: `LocationProvider`, `SecureTokenStore`.

If the name needs a caller name plus many options, the boundary is probably too
generic or too early.

Reusable names must describe the capability a caller imports, not the place
where the code was first extracted. Avoid umbrella names such as `common`,
`shared`, `core`, `app`, `runtime`, `base`, `manager`, `helper`, or "feedback"
unless the repo has already defined that word as a capability family and the
public exports are still narrow.

When a shared module owns user-visible presentation side effects, name the
capability directly. For example, a module that renders toast, snackbar,
dialog, alert, or error presentation contracts should use a notice, alert,
message, error, permission, or equivalent repo-local capability name instead of
a vague reaction word. If the module also owns network error normalization,
route execution, or Activity lifecycle setup, split those capabilities before
making the module reusable.

Do not call an inheritance or template boundary "base" unless the boundary owns
a narrow lifecycle contract with clear extension points. A reusable base should
not become the place where routing policy, feature registration, repositories,
analytics, permission prompts, error copy, and visual components accumulate.

## Reuse Stop Signals

Stop promotion to a shared package, module, source set, or public API when any
of these are true:

- The only argument is "other projects might reuse this later."
- The proposed module name describes a bucket rather than a capability.
- Pure contracts, platform runtime, visual primitives, app-shell wiring,
  feature policy, and test assertions would ship from one export surface.
- Callers must import Activity, controller, browser, router, repository, SDK, or
  DI details just to use a value type, fixture, assertion, route key, or command.
- A shared "base" type would require most callers to override no-op hooks,
  pass flags, or inherit behavior they do not need.
- A shared notice/error/alert surface would also own transport retry, repository
  orchestration, route policy, or screen-specific recovery copy.
- Test support would depend on production implementation modules by default.

Choose a smaller boundary first: pure contract, platform adapter, runtime host,
design-system primitive, feature-local holder, or assertion helper. Revisit the
shared boundary only after the import rule and caller contract are obvious.

## Anti-Patterns

- Extracting a generic helper before the second real use exists.
- Sharing code by adding boolean flags such as `isFeed`, `isProfile`, or
  `showSpecialMode`.
- Moving product copy, analytics names, or route decisions into a shared UI unit.
- Making shared code read global config, environment variables, singletons, or
  mutable caches without an adapter contract.
- Creating a package that re-exports unrelated helpers as a grab bag.
- Sharing a fat interface, context, hook return object, or service API that
  forces callers or tests to provide unrelated no-op behavior.
- Naming a reusable module after a broad bucket when the actual capability is a
  route, notice, alert, permission, environment, launcher, adapter, fixture, or
  assertion contract.
- Putting app runtime setup, base lifecycle templates, platform launchers,
  design-system components, network errors, and feature policies behind one
  "core app" style import.
- Hiding breaking behavior changes behind a reuse refactor.

## Verification

For reusable code changes, verify both the shared unit and at least one caller:

- unit test, mapper test, policy test, or component test for the reusable unit
- compile/typecheck of affected callers
- preview/screenshot/UI check when a reusable UI component changes
- contract or fixture parity check when DTO/API/package behavior changes
- final diff review that confirms product-specific behavior stayed in callers

Report whether the change is a new reusable contract, a local extraction, or a
behavior-preserving move.
