---
keyflow_id: sys_code_structure_ownership
status: review
type: human-reviewed-needed
---

# Code Structure And Ownership

Use when deciding file layout, package layout, module boundaries, public
contracts, `api`/`impl` splits, or where new code should live.

Structure should make ownership, dependency direction, and review scope obvious.
Do not create modules or packages just because a pattern exists elsewhere.

The default choice is local or single-module code. Split only when the split
protects a real caller-facing boundary, extension point, dependency edge, or
ownership line.

For SOLID, Interface Segregation, Dependency Inversion, and DDD/domain-modeling
fit, also use `common/solid-design-principles.md`. In structure decisions,
SOLID means narrow caller contracts and dependency direction; it does not mean
creating layers or interfaces before a real boundary exists.

## Unit Size And Split Criteria

Use code size as review pressure, not an automatic split command. Long code is
acceptable when it has one owner, one reason to change, and a clear verification
path. Short code still needs extraction when it mixes owners, side effects, or
contracts.

Apply the same ownership criteria to web, mobile, desktop, server, scripts, CSS,
styles, tests, and generated-adjacent glue. Apply strict runtime size gates to
production/runtime source and style files; tests, specs, mocks, fixtures, and
docs are reviewable but exempt from the hard size gates unless a repo-local rule
opts them in:

- Functions, methods, components, hooks, reducers, handlers, jobs, and scripts
  should be small enough to scan in one pass. About 40 to 80 lines is a normal
  review budget for orchestration code; over about 120 lines in runtime code is
  a hard review failure unless repo-local policy explicitly sets a different
  limit.
- Source files should have one primary owner and one responsibility cluster.
  A new runtime source/style file over about 400 lines fails review, and an
  existing runtime source/style file already over about 400 lines must not grow.
  More than about 200 added lines in one runtime file fails review because it is
  usually a "dump it all here" signal.
- CSS and style files follow the same ownership rule. Do not group tokens,
  primitives, component variants, page layout overrides, and one-off fixes in
  one file only because they are all styles.
- Packages, folders, namespaces, targets, or modules are ownership boundaries,
  not storage bins. Create them only when they make allowed imports, dependency
  direction, tests, or review ownership clearer.

### Responsibility-Based File Split

Do not pack separate roles into one source file only because they belong to the
same module, package, feature, or test-support area. A file should usually have
one responsibility cluster and one reason to change.

Split by role when a file starts mixing these categories:

- public contracts and implementation details
- fixtures/sample data and assertion logic
- recording fakes/spies and matcher or subject DSLs
- builders/factories and platform adapters
- parsing/normalization and execution/side effects
- route contracts, route resolution, and route rendering
- read-only helpers and mutating commands

This applies to `assertions`, `testing`, `fixtures`, and `dev` modules as much
as production modules. Test-support code is reusable code: callers should be
able to import a fixture, a recording fake, or an assertion subject without
pulling unrelated helpers or production implementation dependencies.

Keep a small one-file helper only when the roles are inseparable, have one real
caller, and can be reviewed in one pass. Once callers, responsibilities, or
verification paths differ, split the file before adding more behavior.

### Contract Family Split

Apply contract-family splits across every language and platform. A Kotlin
package, TypeScript module or barrel file, Swift target, Dart library, Python
package, server folder, CSS module, or test-support package is still a public
interface when another caller imports it.

Do not keep unrelated caller-facing contract families in one catch-all file,
module, namespace, or export surface. Split when the same API area starts mixing
families such as:

- routes, route events, deep-link matchers, and rendering or execution adapters
- request/response DTOs, validation schemas, generated clients, and route
  handlers
- read queries, write commands, mutation policies, and background jobs
- component props, feature policy, analytics names, and platform launchers
- fixtures, builders, recording fakes, assertion subjects, and contract tests

Use names that describe the import boundary. Examples: `route`, `event`,
`schema`, `dto`, `command`, `query`, `adapter`, `fixture`, `assertion`,
`activity`, `platform`, or the repo's established equivalents. Keep a single
contract file only when it contains one small contract family, has the same
caller set, and has one reason to change. Do not split mechanically into one
folder per type when the caller-facing import boundary is identical.

Barrel or index files are allowed only as narrow compatibility surfaces. They
must not hide a grab bag of unrelated route, schema, event, UI, data, platform,
and testing exports behind one convenient import.

### Capability Naming And Boundary Inference

Names are part of the architecture contract. A future agent or maintainer should
be able to infer the owner, allowed imports, and reusable capability from the
module, package, namespace, target, or folder name before opening every file.

Do not create or keep a broad boundary named `app`, `core-app`, `core-ui`,
`runtime`, `base`, `common`, `shared`, `platform`, `manager`, `helper`,
`service`, `utils`, or a similarly vague word unless the repo already defines
that name as a stable capability family and the next package level makes the
capability precise.

Do not name a reusable module after:

- the first app, feature, screen, or caller that happened to need it
- the current implementation surface when the reusable capability is narrower
- a broad user reaction such as "feedback" when the code actually owns notices,
  toasts, snackbars, dialogs, alerts, error presentation, permission prompts, or
  another concrete capability
- an inheritance shape such as "base" when the boundary really owns lifecycle
  setup, routing handoff, environment creation, or platform adapters

Before adding, keeping, or renaming a broad boundary, write the boundary note in
terms of the concrete capability. If the note cannot say what callers may import
without using words such as "misc", "common things", "app stuff", "shared
helpers", or "feedback", the name is not ready.

Keep pure contracts, platform runtimes, app-shell orchestration, design-system
primitives, test assertions, and feature policy in separate boundaries unless
one explicit owner and import rule covers them all. A module that mixes Activity
templates, route execution, notification/toast rendering, visual tokens,
repositories, and product policy is a catch-all module even when it compiles.

## Non-Negotiable Structure Stops

Do not continue implementation when any of these are true:

- The new change would add another unrelated responsibility to a file that
  already owns routing, rendering, state, data access, styling, and side effects.
- A single function, component, hook, handler, job, reducer, or script step would
  own more than one of these concerns: parse, validate, authorize, fetch, cache,
  map, render, mutate, persist, log, navigate, schedule, retry, or recover.
- The code needs separate tests, fixtures, previews, or manual checks for
  separate branches, but those branches are still hidden inside one unit.
- The proposed new file is a grab bag named `utils`, `helpers`, `common`,
  `misc`, `shared`, `manager`, `service`, `base`, `runtime`, `app`, or
  `platform` without a precise owner and contract.
- The proposed module, package, or folder name does not tell a caller what it
  can import, what it must not import, and which capability owns the code.
- The proposed function exists only to move an obvious line elsewhere, or it
  needs caller-specific flags to be useful.
- The split would create many tiny files with no stable owner, no testable
  contract, and no review benefit.

When a stop signal appears, make the smallest ownership split before adding more
behavior. The split can be file-private, package/internal, feature-local, or a
new source file; choose the lowest level that makes responsibility, dependency
direction, and verification obvious.

### Function Or Block Split

Split a function, component, hook, reducer, handler, job, style block, or script
step when one of these is true:

- The unit combines multiple responsibilities such as parse, validate,
  authorize, fetch, cache, map, render, mutate, log, navigate, or persist.
- Branches describe different business cases, UI states, data sources, platform
  capabilities, or failure modes that can be named and tested separately.
- A pure calculation can be separated from IO, time, randomness, process state,
  global state, framework calls, or platform calls.
- The same rule, mapper, formatter, selector, style pattern, or error handling
  repeats in more than one real caller.
- A test, preview, fixture, or smoke path cannot exercise the behavior without
  booting unrelated systems.
- The best name for the unit contains "and", "or", "with", "misc", "common",
  "helper", or a caller-specific mode flag.

Keep the code local when the extracted helper would only rename an obvious line,
hide a necessary branch, require many caller-specific parameters, or have no
stable responsibility name.

### File Or Class Creation

Create a new source file, class file, CSS file, style module, or test fixture
when most of these are true:

- The new unit has a clear owner and can be named by responsibility, not by a
  vague bucket such as `utils`, `helpers`, `common`, or `misc`.
- It has a stable input/output, state, side-effect, rendering, styling, or
  contract surface.
- It can be tested, previewed, mocked, or reviewed without reading the whole
  caller.
- It isolates a real boundary: domain policy, state model, mapper, adapter,
  platform API, component contract, style primitive, fixture, or integration
  edge.
- The caller becomes smaller without losing the product policy, route decision,
  permission check, copy ownership, analytics ownership, or error ownership it
  should keep.

Do not create a new file or class only because a file is getting long. First map
the responsibilities, callers, state owners, side effects, and nearest checks.
If the new unit has one caller and no real boundary, prefer file-private or
package/internal code.

### Package Or Folder Creation

Create a new package, folder, namespace, target, or module when it protects an
import or ownership rule:

- Multiple files share one owner and are expected to evolve together.
- Callers should import a stable contract without seeing implementation details.
- A platform, SDK, database, filesystem, network, browser, shell, or paid
  dependency must stay behind an adapter boundary.
- Tests need a smaller unit than the app shell, server process, route tree, or
  renderer to verify behavior.
- The split prevents circular dependencies, broad manifest churn, or unrelated
  owners editing the same area.

Keep the current package when the proposed folder would contain one or two
small unstable files, duplicate an architecture diagram without enforcing an
import rule, or become a grab bag for unrelated helpers.

### Package Boundary Note

Before creating or moving a package, folder, namespace, target, or module, write
a short boundary note in the implementation plan, task doc, PR description, or
review summary. The note must name:

- the owner and single responsibility of the new boundary
- allowed imports and explicitly forbidden imports
- the caller-facing exports, if any
- the callers or tests that benefit from the boundary
- the focused verification command or import-direction check

A new package is justified only when the boundary changes ownership,
dependency direction, review scope, testing scope, or replaceability. It is not
justified by "one file per type", "this architecture usually has folders", or
"the package looks cleaner".

For `api`, `impl`, and `assertions` layouts, split by contract surface and
consumer need, not by mechanical file count:

- `api` can group route contracts, events, commands, models, provider
  contracts, and small value types together while they share one import rule.
  Add subpackages, source files, or export modules when consumers should import
  one contract family, such as routes, events, schemas, DTOs, commands,
  provider ports, activity/launcher keys, or test fixtures, without the others.
- `impl` can group route mapping, rendering, registration, adapters, mappers,
  and state holders by behavior owner. Do not mirror every `api` file with an
  `impl` package unless the implementation dependency differs.
- `assertions` should split fixtures, builders, recording fakes, subjects,
  matchers, and contract tests by testing role. Do not create a package only to
  mirror each production type.

If the package boundary note cannot explain the allowed imports and who
benefits, keep the code in the existing package and split only files or
file-private helpers as needed.

### Module-Level SOLID / ISP

Treat a module's public exports as an interface. Module-level ISP means callers
depend only on the module contract they actually need, not on a broad
implementation package.

Create or reshape modules around narrow contracts when:

- consumers need route contracts, events, commands, policies, models, factories,
  or repository ports without implementation dependencies
- read-only consumers should not import write commands, migrations, debug
  tools, lifecycle wiring, or registration code
- feature callers need stable API types without UI, data, SDK, database,
  platform, paid, optional, or test dependencies leaking into their graph
- tests need fakes, fixtures, or assertions without depending on production
  implementation modules
- a public barrel/export file is becoming a grab bag of unrelated symbols

Do not publish a module API that forces every caller to import all UI, domain,
data, platform, fixture, generated, and implementation details. A module split
is justified only when the narrower contract changes dependency direction,
build coupling, testability, or ownership.

### Assertions And Test-Support ISP

Treat a reusable assertions module as a public testing API. Keep its exported
roles narrow:

- fixtures create stable sample inputs
- recording fakes capture calls or events
- subjects/matchers assert one contract surface
- builders construct complex values without execution side effects
- contract tests verify substitutable implementations

Do not put all of these in one catch-all file or one broad fake when callers
need only one role. A test fake that requires unrelated no-op methods or
production implementation imports is an Interface Segregation failure, even if
it lives outside runtime source.

### Shared Code Promotion

Promote code to `common`, `shared`, `core`, a design-system package, or a public
package only when the caller contract is stable:

- At least two real callers or one explicit platform/public contract need it.
- Product copy, routing, permissions, analytics, tenant rules, billing rules,
  and workflow decisions remain in the caller.
- Inputs, outputs, errors, loading states, side effects, and customization points
  are explicit.
- The shared unit can change internally without forcing caller behavior changes.
- Tests, examples, previews, fixtures, or compatibility notes cover the shared
  contract.

Do not promote code only to reduce apparent duplication. Duplication is cheaper
than a shared API that needs flags, nullable options, hidden globals, or
caller-specific branches.

### Cross-Platform Commonization Gate

Promote code into a shared, core, common, multiplatform, or SDK-like boundary
only when the reusable contract is semantic rather than platform-shaped:

- Public names describe the domain or reusable capability, not one platform,
  framework, screen, or first caller.
- Platform objects stay behind adapters: `Activity`, `Context`, `Intent`,
  `NavController`, `View`, `Composable`, `UIViewController`, `URLSession`,
  browser globals, process APIs, database handles, and SDK clients do not leak
  into pure shared contracts.
- Side effects are explicit through suspend functions, commands, callbacks,
  ports, or adapters. Shared code should not hide lifecycle, thread, scheduler,
  filesystem, network, billing, credential, or analytics ownership.
- Runtime UI helpers live in a platform app/UI boundary. Pure core modules own
  models, policies, value types, ports, mappers, and route/event contracts.
- Assertions, fixtures, and fakes compile against the shared API contract, not
  the production implementation.
- Feature copy, route policy, analytics policy, permission prompts, and
  repository orchestration remain in the app or feature owner.

Cross-platform commonization fails when a common package exists only to avoid
duplication but still needs platform flags, nullable platform knobs, global
state, or caller-specific branches.

## Ownership Levels

Choose the lowest level that gives the code a clear owner:

```text
file-private -> package/internal -> feature/module -> feature-api contract
-> shared/core module -> public package/API
```

- File-private code is best for one caller and unstable details.
- Package/internal code is best for nearby collaborators with the same owner.
- Feature/module code is best for a cohesive behavior surface.
- Shared/core code is best for stable contracts used by multiple owners.
- Public package/API code needs compatibility, versioning, migration notes, and
  stronger tests.

## Module Split Choices

Most multi-module designs choose between two shapes.

## Decision Rule

Choose a single module unless the answer to at least one of these questions is
yes:

- Does another module need to compile against this contract without depending on
  the implementation?
- Does navigation, deep linking, plugin loading, dependency injection, or feature
  registration cross this boundary?
- Is this an extension point where another implementation can reasonably replace
  the current one?
- Would implementation dependencies leak heavy, platform-specific, paid, test,
  or optional dependencies to callers?
- Does the split remove a circular dependency, reduce build coupling, or let
  different owners change contract and implementation independently?

If all answers are no, keep the code local or in one module and revisit the
boundary when pressure appears.

## Modernization Drill

When modernizing an old or oversized codebase, separate structure moves from
behavior changes:

1. Inventory current imports, public exports, target/module membership,
   generated files, resources, tests, and runtime entry points.
2. Name the current owner and the intended owner before moving files.
3. Extract the smallest stable contract first: route data, component API,
   repository interface, platform adapter, use case, or typed model.
4. Compile or typecheck the contract boundary before moving implementation.
5. Move one feature, package, module, or source set at a time.
6. Keep compatibility shims only with an owner, removal condition, and test.
7. Remove old imports, duplicate exports, and dead target membership after the
   new boundary is verified.

Avoid combining broad moves with product behavior changes. If behavior must
change to make the split correct, call it out as a separate acceptance point.

### Single Module

Use one module or package when:

- The feature has one implementation and one owner.
- No other module needs to compile against its contract.
- Navigation, routing, or integration is local to the feature.
- The implementation dependencies are acceptable for all callers.
- The boundary is still changing and an interface would mostly duplicate files.
- Tests can cover behavior without isolating a public contract module.

This is the default for small or early features.

### API / Impl Pair

Use an `api` / `impl` split when at least one of these is true:

- Another module must depend on route contracts, events, interfaces, DTOs, or
  factories without depending on UI/data/framework implementation.
- Navigation, deep links, plugin loading, dependency injection, or feature
  registration needs a stable contract surface.
- Multiple implementations exist or are likely: fake/real, platform-specific,
  paid/free, local/remote, test/prod, or replaceable provider.
- The implementation has heavy dependencies that should not leak to callers.
- The split prevents circular dependencies or reduces build coupling.
- Different teams or agents can own contract and implementation independently.
- Contract compatibility matters for generated clients, SDKs, plugins, or public
  packages.

An `api` module should contain only stable contracts:

```text
interfaces, route/event contracts, public models, typed commands,
factory/provider contracts, small value types, compatibility docs
```

An `impl` module should contain implementation details:

```text
screens, adapters, repositories, framework code, internal mappers,
real/fake providers, DI bindings, platform integrations
```

Do not create an `api` module only to mirror architecture. If no caller can use
the API without the implementation, the split is probably too early.

### API / Impl / Assertions Trio

Use an `api` / `impl` / `assertions` split when tests need reusable support
without depending on production implementation details.

An `assertions` module or source set should contain:

```text
fake implementations, recording adapters, fixture builders, assertion DSLs,
test subjects, contract test helpers, deterministic clocks or dispatchers
```

Keep the dependency direction narrow:

```text
assertions -> api
tests -> assertions
impl tests -> impl plus assertions only when testing implementation behavior
```

Do not let `assertions` depend on production `impl` by default. Pulling in
production implementation code from a reusable test-support module usually
means the contract is not stable enough, the test belongs in the implementation
module, or the fake should be local to one test.

Create `assertions` only when at least one of these is true:

- two or more test boundaries need the same fake, fixture, recording sink, or
  assertion helper
- a contract module needs reusable conformance tests
- a route, repository, adapter, or platform boundary needs a deterministic
  test double that callers can share without booting the app shell
- the helper prevents tests from importing a heavy framework, platform, paid,
  or production implementation dependency

Keep one-off test data, previews, and test-only setup local until reuse is
real. Use plural `assertions` for module names so paths stay consistent across
repositories.

## Boundary Pressure Signals

Split or introduce a stronger boundary when these signals repeat:

- feature files import data-source, SDK, or platform implementation packages
- UI code reaches raw transport, database, file, or channel payloads
- shared packages need feature-specific flags, copy, analytics, or route
  decisions
- tests must boot unrelated app shells to exercise one state transition
- one implementation dependency forces all callers to carry a heavy optional SDK
- build changes require touching many unrelated target or package manifests
- a "common" folder has several unrelated owners and no stable public contract

When only one signal appears once, prefer a local cleanup before a module split.

## Package Layout

Prefer package names that express responsibility, not technical noise. Common
top-level groups include:

```text
api/ or contract/     public caller-facing contracts
impl/ or internal/    implementation details
route/                route keys, paths, navigation commands, or link contracts
event/                caller-emitted events and intent-like messages
schema/ or dto/       request/response shapes, validation schemas, generated contracts
command/ or query/    write commands and read queries when callers differ
model/                plain values owned by this boundary
state/                UI/application state and effects
component/            reusable UI or interaction pieces
data/                 persistence, network, cache, external data sources
domain/               product rules, use cases, policies
platform/             OS, runtime, SDK, filesystem, shell, browser adapters
testing/ or fixture/  test doubles, samples, deterministic fixtures
```

Use the repo's existing names first. Do not rename established packages unless
the rename itself is the task. Existing names still need review when a new
caller cannot infer the capability without reading implementation files.

## Boundary Rules

- Dependencies point inward or downward; implementation does not leak upward.
- Public contracts avoid framework-heavy types unless the platform is the
  contract.
- Domain and model layers avoid UI, persistence, transport, and platform types.
- UI layers do not own data source details or long-lived external side effects.
- Shared modules do not depend on feature implementation modules.
- Generated code, fixtures, and examples have explicit ownership.

## Review Checklist

- Who owns this file or module?
- Which callers are allowed to import it?
- Is the public surface smaller than the implementation?
- Does the split remove coupling or only add ceremony?
- Can the contract be tested without the implementation?
- Will a future implementation swap require changing callers?
- Are package names stable enough to keep?
- Can a new caller infer the boundary from the module/package name without
  opening implementation files?
- Did any broad name such as `app`, `common`, `shared`, `base`, `runtime`,
  `manager`, `helper`, or "feedback" pass a concrete capability note?

## Verification

For structure changes, verify the boundary, not only formatting:

- compile/typecheck all affected modules
- run focused tests for contract mappers, route resolution, or provider wiring
- inspect import direction for forbidden dependencies
- check generated clients, fixtures, or public exports when the API changed
- report whether the change chose single module or `api`/`impl`, and why
