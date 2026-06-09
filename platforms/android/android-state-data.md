---
keyflow_id: sys_aea75f7837ca
status: review
type: ai-generated
---

# Android State And Data

Use when touching Compose state, ViewModel, Flow, repository, persistence, or permissions.

For detailed ViewModel, `UiState`, Flow, repository, use case, persistence, and
one-off event implementation rules, also use `android-viewmodel-state.md`.

For repository module splits, API/implementation boundaries, and DTO/entity
package ownership, also use `android-module-structure.md`.

## Defaults

- Composable renders state and sends events.
- ViewModel owns durable UI state and lifecycle-aware work.
- Use sealed/state models for loading, empty, error, permission denied.
- Separate one-off events from persistent state.
- Repository owns data source coordination and error mapping.
- Room, DataStore, files, permissions, notifications stay behind adapters.
- Platform or heavy resources created by ViewModels, repositories, workers, or
  adapters need an owner and cleanup path for success, failure, cancellation,
  logout, account switch, or permission revoke when relevant.
- Inject dispatchers or schedulers for coroutine tests.
- Use lifecycle-aware collection for UI-observed Flow.
- Version persisted data that can survive app upgrades.

## Repository Boundaries

- Repository `api` modules expose interfaces and stable entities only.
- Repository implementation modules own Retrofit APIs, Room DAOs, DataStore,
  files, SDK clients, request/response DTOs, cache records, and mappers.
- HTTP client response handles, error-body parsing, conversion failures, and
  transport exceptions should be normalized at the API or data-source boundary
  instead of repeated in every feature or ViewModel.
- Feature modules depend on repository APIs or domain use cases, not repository
  implementation packages.
- Map DTO/cache/database models into repository entities before data crosses the
  module boundary.
- Put flavor, dev, fake, or assertion implementations in explicit
  flavor/dev/testing/assertion modules instead of branching through production
  repository contracts.
- Use a domain use case when multiple repositories or product policy must be
  orchestrated; do not add pass-through use cases for one repository call.

## Check

- Does collection respect lifecycle?
- Can process recreation restore needed state?
- Are navigation args parsed away from business rules?
- Does logout, account switch, or permission change clear cached state?
- Are Room migrations, DataStore changes, and offline cache invalidation covered?
- Are StateFlow, SharedFlow, Channel, and one-off events chosen intentionally?
- Are repository entities separate from DTOs, database rows, SDK models, and UI
  display models?
- Does any feature import a repository implementation package instead of the API
  contract?
