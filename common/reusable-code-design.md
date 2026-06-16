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

Avoid reusable APIs that accept repositories, activities, routers, request
objects, raw environment variables, or feature-specific DTOs unless that is the
documented owner boundary.

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
