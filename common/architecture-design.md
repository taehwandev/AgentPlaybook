---
keyflow_id: sys_e01bf7495d2e
status: review
type: ai-generated
---

# Architecture Design

Use when planning architecture for a feature, module, service, or app surface.

For architecture track selection, also use `architecture-selection.md`. For
module/file ownership and `api`/`impl` split decisions, also use
`code-structure-ownership.md`. For SOLID, Interface Segregation, Dependency
Inversion, and DDD/domain-modeling fit, also use
`solid-design-principles.md`. For state owner design, also use
`state-modeling.md`. For failure contracts, also use `error-modeling.md`.
For external, persisted, generated, cached, platform, or user-provided values,
also use `defensive-boundaries.md`. For environment-specific API origins,
callback URLs, redirect URIs, webhook endpoints, CORS origins, deep link hosts,
or asset hosts, also use `runtime-url-configuration.md`.

## Method

Design from change pressure, not diagrams. First identify what changes together, what must be protected, and what needs independent testing. Then choose boundaries.

## Steps

1. Name the user or system behavior.
2. Identify state owners and data sources.
3. Separate UI, domain, data, platform, and integration responsibilities.
4. Mark risky boundaries: auth, tenant, billing, persistence, sync, jobs, external APIs.
5. Identify contracts that callers compile against, persist, send over the
   network, cache, generate, or expose publicly.
6. Check SOLID pressure: one responsibility per unit, narrow caller contracts,
   substitutable implementations, and dependency direction toward stable policy
   or contracts.
7. Pick the smallest architecture that keeps those risks visible.
8. Define verification before implementation.

## Rules

- Keep architecture local until reuse or risk justifies shared layers.
- Prefer explicit contracts over implicit global state.
- Keep caller-facing contracts narrow enough for each caller to depend only on
  the operations, state, callbacks, or exports it actually needs.
- Use adapters for platform and external systems.
- Avoid architecture that requires touching many unrelated files for one product change.
- Record tradeoffs when choosing speed over structure or structure over simplicity.

## Decision Frame

Every non-trivial architecture design should name these owners before
implementation:

| Decision | Owner To Name |
| --- | --- |
| Visible state | screen, route, ViewModel, hook, store, reducer, controller, or command owner |
| Durable state | database, file, cache, settings, server, sync engine, or external system |
| Product rules | domain policy, use case, service, reducer, permission policy, or server contract |
| External data | validator, mapper, DTO boundary, generated client, adapter, or repository |
| Side effects | command, effect handler, repository/client, background job, platform adapter, or shell bridge |
| Failure handling | typed boundary error, domain failure, UI state, response envelope, log/metric/audit owner |
| Public contract | route, API, event, DTO, schema, deep link, command, package export, or plugin contract |
| Runtime URL config | config module, environment variable, deployment setting, build flavor, app scheme, provider registration, or platform adapter |
| Verification | unit, component, contract, integration, migration, smoke, screenshot, or manual scenario |

If an owner cannot be named, keep the work local or clarify the behavior before
adding another layer.

## Implementation Tracks

Choose one track explicitly before code for non-trivial work. Prefer the
simplest track that keeps state, side effects, and risk visible.

| Track | Use When | Boundary |
| --- | --- | --- |
| Local feature | UI-only or one small workflow with no shared domain rule. | UI owns local state; no new shared layer. |
| State owner / MVVM | Loading, form submit, async work, navigation, or screen-level user intents need a named owner. | UI renders state; ViewModel/hook/store owns transitions. |
| Use case boundary | Product rule, permission, billing, tenant, sync, or mutation logic needs focused tests. | State owner calls use cases; use cases call repositories/clients. |
| Clean architecture | Domain rules must survive UI/framework changes or be reused by multiple apps/features. | UI -> state -> use case/domain -> repository protocol -> adapter/client. |
| Reducer/state machine | Many events, replayable transitions, optimistic rollback, wizard steps, or concurrency races. | UI dispatches actions; reducer/machine owns transitions; effects own side effects. |
| Shared package/API | Multiple repos/apps depend on the contract. | Versioned public interface with compatibility and migration notes. |

Do not add layers because a template says so. Add a boundary only when it gives
one of these benefits:

- a state owner becomes testable without rendering UI
- a product rule stops being duplicated in screens
- a platform/external API is isolated behind an adapter
- a risky contract gets one place for validation and error handling
- a reusable caller contract is clearer than local duplication

Avoid boundaries that only rename a call, hide an obvious branch, or force every
caller through flags, nullable options, global state, service locators, or
framework-specific plumbing.

## State Model

For user-visible workflows, define the state shape before implementation.

- List the reachable states: loading, content, empty, error, permission denied,
  offline, disabled, submitting, success, and stale when applicable.
- Prefer typed state models over unrelated booleans and nullable fields.
- Keep one-off effects such as navigation, toast, focus, file download, and
  permission prompt separate from persistent screen state.
- Define who invalidates, refreshes, clears, or persists the state.
- Define what happens on logout, account switch, permission change, plan change,
  process restart, backgrounding, and network loss when applicable.

## Clean Architecture Rule

Use clean architecture only when there is real domain or integration pressure.

When used, keep the dependency direction strict:

```text
UI -> State Owner -> Use Case / Domain Policy -> Repository Interface
-> Adapter / Client / Platform API
```

- UI owns rendering and user intent only.
- State owner owns UI state transitions and invokes use cases.
- Use cases own product rules and orchestration, not framework rendering.
- Repository interfaces express domain needs, not raw HTTP or database details.
- Adapters own SDK, HTTP, database, filesystem, keychain, browser storage, or OS
  API details.

Stop if a "clean" layer only forwards one method without adding ownership,
testing value, or risk isolation. Keep that work local until pressure appears.

## Contract And Boundary Integrity

For any architecture that crosses files, packages, modules, services, or apps:

- Keep public contracts smaller and more stable than implementations.
- Keep DTOs, database rows, SDK objects, file records, shell output, and raw
  platform payloads out of UI and domain code unless they are the documented
  contract.
- Normalize external values at the boundary before product logic sees them.
- Preserve dependency direction with imports, target membership, package
  visibility, or lint rules where the repo supports them.
- Keep compatibility notes for routes, APIs, events, schemas, persisted fields,
  cache keys, generated clients, package exports, and plugin contracts.
- Plan removal conditions for temporary shims, duplicate paths, or migration
  adapters.

Architecture is not complete until the boundary can be verified. Pick checks
that exercise the owner, not only the file that changed.

## Output

For non-trivial work, leave a short decision note:

```text
behavior:
chosen shape:
state owner:
data/platform boundary:
failure boundary:
public contracts touched:
rejected alternative:
risk:
verification:
rollback or removal plan when needed:
```
