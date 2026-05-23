---
keyflow_id: sys_e01bf7495d2e
status: review
type: ai-generated
---

# Architecture Design

Use when planning architecture for a feature, module, service, or app surface.

## Method

Design from change pressure, not diagrams. First identify what changes together, what must be protected, and what needs independent testing. Then choose boundaries.

## Steps

1. Name the user or system behavior.
2. Identify state owners and data sources.
3. Separate UI, domain, data, platform, and integration responsibilities.
4. Mark risky boundaries: auth, tenant, billing, persistence, sync, jobs, external APIs.
5. Pick the smallest architecture that keeps those risks visible.
6. Define verification before implementation.

## Rules

- Keep architecture local until reuse or risk justifies shared layers.
- Prefer explicit contracts over implicit global state.
- Use adapters for platform and external systems.
- Avoid architecture that requires touching many unrelated files for one product change.
- Record tradeoffs when choosing speed over structure or structure over simplicity.

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

## Output

For non-trivial work, leave a short decision note: chosen shape, rejected alternative, risk, verification.
