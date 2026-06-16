---
keyflow_id: sys_kmp_compose_ui
status: review
type: human-reviewed-needed
---

# KMP Compose UI

Use when creating, changing, moving, or reviewing Compose Multiplatform screens,
state holders, reusable UI components, previews, resources, or UI tests.

For reusable UI extraction, also read `common/reusable-code-design.md`,
`common/component-api-design.md`, and `common/design-system.md`.
For shared Compose module placement, source-set ownership, and feature/shared UI
splits, also read `kmp-module-structure.md`.

## Compose Layers

Use this shape unless the repo has a stricter local pattern:

```text
Route/Host Composable -> Screen Composable -> Section Composable
-> Feature Component -> Design-System Primitive
```

- Route/host composables wire state owners, effects, navigation callbacks,
  platform launchers, focus/window hooks, and dependency entry points.
- Screen composables are stateless. They receive immutable UI state and explicit
  callbacks, then render the whole screen.
- Section composables receive only the state they need.
- Feature components may know product UI models, but not repositories, target
  entry points, permission APIs, windows, activities, controllers, or DI.
- Design-system primitives know visual and interaction contracts, not product
  routes, analytics labels, storage, shell commands, or fake data.

## Shared UI Rules

- Keep shared composables free of Android-only lifecycle, `Context`, resource
  ids, permissions, and Activity APIs unless the file is in an Android source
  set.
- Keep desktop-only window, menu, pointer, keyboard shortcut, file, and process
  behavior in desktop source sets or platform adapters.
- Use immutable UI models and explicit callbacks. Keep one-off effects separate
  from persistent render state.
- Apply `modifier: Modifier = Modifier` to the root layout exactly once for
  public reusable composables.
- Keep user-facing copy and resources aligned with the repo's localization and
  Compose Multiplatform resource strategy.
- Model desktop and mobile ergonomics intentionally: keyboard/focus, pointer
  hover, window resizing, touch targets, scroll behavior, and text scaling may
  differ by target.

## State Holder And MVI Shape

For non-trivial shared Compose screens, use an explicit state/action/effect
contract:

```text
<Screen>Root     state owner, lifecycle collection, effects, navigation callbacks
<Screen>         stateless rendering from state and callbacks
<Screen>State    persistent visible state
<Screen>Action   user intents
<Screen>Effect   one-off navigation, snackbar, permission, file, or external launch
```

Rules:

- Keep route/root composables thin. They collect state, handle effects, and
  delegate rendering to stateless screens.
- Stateless screens receive immutable state and one action callback or
  role-sized callbacks. They do not resolve DI, read repositories, start network
  calls, or parse navigation arguments.
- Model loading, content, empty, error, permission denied, offline,
  unsupported, submitting, and sync states when reachable.
- Effects should be consumed once and should not replay after navigation,
  window recreation, rotation, refresh, or target lifecycle changes.
- Use typed route values for navigation arguments when the navigation framework
  supports it; do not pass raw string route paths through screen components.

## Performance And Resources

- Use lazy lists/grids with stable keys for large or updating collections.
  Avoid rendering large collections with eager layout containers.
- Move heavy filtering, sorting, formatting, or mapping out of composable bodies
  and into state owners, mappers, or stable derived state.
- Keep shared strings, images, and plural/localized resources in the repo's
  Compose Multiplatform resource strategy. Do not hard-code user-facing strings
  in reusable screens when localization is in scope.
- Keep Android-only preview tooling, iOS bridge code, desktop window APIs, and
  browser APIs in their target source sets.
- Use design-system primitives first. Promote feature components only when they
  have a stable caller contract and no feature policy, route, analytics, or data
  dependency.

## Preview And Fixture Rule

Every new or meaningfully changed screen, section, or reusable component needs a
preview, screenshot, or equivalent visual check for the target that can support
it.

Preview fixtures should:

- target stateless composables rather than DI-backed route holders
- use deterministic sample state from a `preview`, `sample`, or `fixture` owner
- cover changed states such as content, loading, empty, error, permission
  denied, offline, disabled, long text, narrow window, and high text scale
- avoid network, database, platform services, real credentials, random data, or
  current time

If a preview cannot run for a target, name the replacement verification, such as
a screenshot test, Compose UI test, desktop smoke, or manual target check.

## Verification

- Compile the changed Compose source set and affected app target.
- Test state owner transitions when events, effects, loading, errors, or
  permissions changed.
- Use Compose UI, screenshot, preview validation, or a smoke check for visual
  and interaction changes.
- Review for target-only APIs in shared composables and for product behavior
  moved into design-system components.
