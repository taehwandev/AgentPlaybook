---
keyflow_id: sys_solid_design_principles
status: review
type: human-reviewed-needed
---

# SOLID Design Principles

Use when writing, refactoring, or reviewing production code that creates or
changes functions, classes, components, hooks, services, repositories, adapters,
interfaces, protocols, public contracts, or module boundaries.

Repo-local architecture, platform idioms, language constraints, and established
import rules win over this common baseline.

## Default

Use SOLID as the default design baseline for production code. SOLID is a
responsibility and dependency rule, not a reason to add ceremony. Prefer the
smallest unit that protects a real owner, caller contract, test boundary, or
dependency edge.

Load these related cards when the change touches their surface:

- `common/code-structure-ownership.md` for file, package, module, and
  `api`/`impl` splits.
- `common/reusable-code-design.md` for shared code extraction and caller
  contracts.
- `common/component-api-design.md` for reusable component, hook, widget, and
  view API surfaces.
- `common/architecture-design.md` and `common/app-architecture.md` for state,
  use case, repository, adapter, and dependency-direction decisions.

## Inspect First

Before applying SOLID, identify:

- the unit's current owner and reason to change
- its real callers and consumers
- the data, state, side effects, and platform details it touches
- the public contract callers compile against or depend on
- the smallest test, preview, contract check, or smoke path that proves the
  boundary
- whether domain pressure is real enough to justify domain modeling or DDD

Do not start by creating interfaces, abstract classes, dependency injection, or
layer folders. Start by naming the responsibility and dependency that need
protection.

## Principles

### Single Responsibility

Each function, class, component, hook, service, repository, adapter, package, or
module should have one primary reason to change.

Split before adding behavior when one unit owns several of these concerns:

```text
parse, validate, authorize, fetch, cache, map, render, mutate, persist,
schedule, retry, log, navigate, recover, format, configure
```

Keep one-off code local when extraction would only rename an obvious line or
move instability elsewhere.

### Open / Closed

Code should be open for new variants through explicit contracts, policies,
composition, or adapters, and closed to unrelated caller rewrites.

Use extension points only when variation is real:

- a second implementation or platform exists
- a product rule has multiple named policies
- an external provider can change behind an adapter
- callers need stable behavior while implementation changes

Do not create plugin systems, strategy objects, or generic option bags for one
unstable caller.

### Liskov Substitution

Every implementation of a contract must preserve the caller's expectations.

Substitutable implementations must keep:

- input and output meaning
- nullability and optional behavior
- error and retry contracts
- ordering, idempotency, and caching promises when documented
- permission, tenant, billing, and data-visibility rules

Do not satisfy a type checker by throwing unsupported-operation errors, silently
ignoring required behavior, narrowing accepted inputs, or returning partial
fake data that violates the contract.

### Interface Segregation

Caller-facing contracts must expose only what each caller needs.

Treat these as ISP failure signals:

- a caller receives a large service, repository, store, context, component prop
  object, or SDK client but uses only one or two operations
- tests or fakes must implement no-op methods, dummy callbacks, placeholder
  properties, fake lifecycle methods, or unrelated dependencies
- a UI component requires navigation, analytics, auth, persistence, or product
  policy props when it only needs display state and user-intent callbacks
- a hook, ViewModel, controller, or use case exposes both read queries and write
  commands to callers that need only one side
- an interface mixes lifecycle, data access, configuration, rendering, logging,
  and mutation responsibilities
- one implementation dependency forces all callers to import a heavy platform,
  SDK, database, network, paid, or optional package

Prefer role-sized contracts:

```text
reader vs writer
query vs command
state view vs mutation sink
formatter vs parser
repository need vs raw data source
component props vs feature policy
platform port vs platform adapter
```

Place the smaller contract near the caller or domain owner that defines the
need. Do not make callers depend on an implementation-owned "everything"
interface only because it already exists.

### Dependency Inversion

High-level policy should depend on stable contracts, not concrete UI,
transport, persistence, SDK, filesystem, browser, OS, or framework details.

Use dependency inversion when it isolates real risk:

- product rules need focused tests
- adapters can change without caller rewrites
- platform or external dependencies are heavy, optional, paid, or hard to boot
- implementation details would leak through public contracts
- import direction or module coupling would otherwise become cyclic

Do not introduce dependency injection containers, service locators, global
registries, or abstract factories only to satisfy the acronym. A small function
parameter, protocol, interface, adapter, or package-internal constructor is
often enough.

## Module-Level SOLID

Apply SOLID to modules, packages, targets, source sets, namespaces, and public
exports the same way it applies to classes or interfaces. A module is a
caller-facing contract when another module can import it.

### Module Single Responsibility

A module should have one primary owner and one responsibility cluster. Split or
reshape the module when one module owns unrelated UI, domain rules, persistence,
SDK integration, platform APIs, fixtures, generated clients, and app-shell
wiring.

Do not create a module only because a folder is large. Create or split a module
when the boundary protects allowed imports, ownership, test scope, build
coupling, dependency weight, or a public contract.

### Module Open / Closed

Callers should be able to add a new implementation, platform adapter, provider,
screen registration, policy, or feature variant without editing unrelated
modules. Use module contracts, registration points, factories, or adapters only
when that variation is real.

Do not make every module editable for every feature by routing all behavior
through a central "core", "shared", or "manager" module.

### Module Substitution

If a module exposes replaceable implementations such as real/fake, local/remote,
free/paid, platform-specific, or test/prod, each implementation must satisfy the
same contract. Substitution includes behavior, errors, lifecycle, threading or
async expectations, persistence semantics, and permission/tenant visibility.

Do not publish a fake or alternate module that compiles but changes the caller's
contract in tests or previews.

### Module Interface Segregation

Module exports are interfaces. Keep them role-sized.

Treat these as module ISP failures:

- a consumer imports a whole implementation module only to use one type,
  function, route, event, or factory
- a public barrel/export file re-exports unrelated UI, domain, data, platform,
  test, fixture, and generated symbols
- callers must depend on heavy SDK, database, framework, paid, optional, or
  platform packages because the module contract leaks implementation details
- read-only consumers must import write commands, lifecycle wiring, migration
  code, debug tools, or feature registration
- tests need production implementation modules only to get fakes, fixtures, or
  assertion helpers
- one module's public API contains caller-specific flags or nullable option bags
  for unrelated features

Prefer smaller module contracts:

```text
feature-api -> feature-impl
domain-api -> data/platform adapters
read-api -> write-api
component contract -> feature policy
testing/assertions -> api
provider contract -> provider implementation
```

Callers should depend on the narrowest module that contains the contract they
actually need. Implementation modules may depend on contracts; contracts should
not depend on implementation modules.

### Module Dependency Inversion

High-level modules define the contract they need, and lower-level modules
provide implementations. In practice:

```text
app/feature -> api contract -> impl adapter
domain/use case -> repository port -> data source adapter
component caller -> component contract -> component implementation
```

Do not place interfaces in an implementation module when that forces callers to
depend on implementation dependencies. Prefer defining the contract in the
caller, domain, feature-api, or shared-api boundary that owns the need.

## DDD And Domain Modeling

DDD is not the default for every feature. Use DDD-style domain modeling only
when domain pressure is real:

- core product rules are complex, reused, or high-risk
- invariants must hold across multiple use cases or data sources
- teams or modules need a shared domain language
- bounded contexts, aggregates, entities, value objects, policies, or domain
  events make change safer
- tests need to exercise product rules without UI, transport, persistence, or
  platform bootstrapping

Do not force DDD on simple CRUD, display-only UI, thin admin screens, one-off
adapters, or workflows whose rules are still unstable. Start with a named use
case, policy, reducer, mapper, or state owner first; promote to richer domain
modeling only when the pressure repeats.

When DDD is used, keep it SOLID:

- domain code owns product invariants and avoids UI, transport, persistence,
  SDK, and platform types
- interfaces express domain needs, not raw implementation details
- bounded contexts keep language and contracts narrow
- repositories and adapters protect external systems from domain logic
- domain tests prove invariants and substitution behavior

## Do Not

- Do not write a fat service, repository, context, interface, component prop
  object, hook return type, or module export that every caller must depend on.
- Do not split interfaces only by technical layer when callers still receive
  unrelated behavior.
- Do not add inheritance when composition, a function parameter, or a small
  port would keep the dependency clearer.
- Do not create layers that only forward one method and add no rule, mapping,
  test boundary, or dependency isolation.
- Do not hide product policy behind generic flags, nullable options,
  caller-specific modes, or catch-all configuration objects.
- Do not call a design "SOLID" when tests need broad no-op fakes or callers must
  import implementation details to use a narrow behavior.

## Verification

Choose the smallest check that proves the SOLID boundary:

- compile/typecheck import direction and public exports
- unit or policy tests for extracted responsibility
- contract tests for each implementation of an interface, protocol, adapter, or
  repository
- caller tests proving smaller interfaces still satisfy the real workflow
- component previews or focused UI tests for reusable component contracts
- fake/test-double review that confirms no unrelated no-op methods are required

For architecture or module changes, also verify that high-level code no longer
imports concrete implementation packages and that public contracts are smaller
than implementations.

## Review Questions

- Can the responsibility be named in one sentence?
- Which caller owns this contract?
- Is the public surface smaller than the implementation?
- Can each caller depend only on the methods, props, callbacks, or exports it
  actually needs?
- Can a fake implementation be written without unrelated no-op behavior?
- Does the dependency point toward policy and contracts rather than concrete
  platform or data details?
- Is DDD justified by repeated domain pressure, or would a smaller use case,
  policy, mapper, or state owner be enough?

## Report

When SOLID governs a change or review, report:

```text
SOLID boundary:
ISP contract shape:
dependency direction:
DDD used or not used:
verification:
```
