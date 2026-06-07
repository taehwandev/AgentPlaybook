---
keyflow_id: sys_component_api_design
status: review
type: human-reviewed-needed
---

# Component API Design

Use when designing reusable UI components, view components, hooks, widgets,
controls, SDK helpers, or any caller-facing component-like API.

A component API should make valid use easy, invalid use hard, and product policy
visible in the caller rather than hidden inside the component.

## API Shape

Prefer:

- Plain values, immutable view models, or small parameter objects.
- Explicit callbacks for user intent or command output.
- Slots/children/render callbacks when the structure is reusable but content
  belongs to the caller.
- Typed states for loading, empty, error, disabled, selected, and permission
  states.
- Stable defaults that do not perform side effects.
- One root customization hook such as `modifier`, `className`, `style`, or
  equivalent, following the platform idiom.

Avoid:

- Passing repositories, routers, activities, controllers, stores, or service
  locators into reusable components.
- Boolean flag APIs that encode caller names, modes, or product variants.
- Components that fetch data, decide navigation, log analytics, enforce product
  permissions, and render UI at the same time.
- Hidden global config reads or environment-dependent behavior.
- Copying a whole screen state into a leaf component when a smaller model works.

## Controlled State

Make ownership explicit:

- Caller-owned state: pass value plus change callback.
- Component-local state: keep only transient interaction state such as focus,
  hover, expanded, drag, animation, or draft text when persistence is not needed.
- External state: expose callbacks or commands; do not mutate remote data inside
  the component without a documented owner boundary.

If a component can be both controlled and uncontrolled, document the precedence
or avoid supporting both until there is a real caller need.

## View And Block Components

Screen, view, section, and block components do not need to be reusable across
features to be valuable. Their first responsibility is to keep rendering
boundaries readable and policy-free.

Use a feature-local view or block when:

- a screen is too large to review as one unit
- a section has a clear visual or interaction responsibility
- the section needs a small view model slice rather than the whole screen state
- the section emits a few user intents but does not own data fetching or
  product policy

Keep the block local when its copy, route decisions, permissions, tenant rules,
billing rules, analytics names, or data shape are specific to one workflow.

Promote a block into a reusable component only when the caller contract is
stable: at least two real callers exist or a design-system contract is intended,
the caller still owns product policy, and the API can be expressed without
caller-specific booleans or nullable feature flags.

## Naming

- Name the component by its reusable role: `SearchField`, `MetricTile`,
  `PlacePreviewSheet`.
- Name callbacks by user intent: `onRetryClick`, `onQueryChange`, `onDismiss`.
- Name slots by position or responsibility: `leadingIcon`, `trailingContent`,
  `media`, `actions`.
- Avoid names tied to the first screen unless the component is feature-local.

## Product Boundary

Reusable components should not own:

- product-specific copy
- route decisions
- analytics event names
- permission policy
- billing or entitlement policy
- tenant/user data filtering
- network/cache/persistence behavior

Those decisions stay in the caller, state holder, domain policy, or integration
adapter. The component exposes enough callback/state surface for the caller to
make the decision.

## Examples And States

Every reusable component should have at least one example, preview, fixture, or
focused test covering the common state. Add edge examples when affected:

- loading and disabled
- empty and error
- selected and unselected
- long text and localization
- missing media or icon
- permission denied or read-only
- small screen or constrained container

## Review Checklist

- Can this component be used by a second caller without feature flags?
- Does the caller still own product policy and navigation?
- Are inputs minimal but complete?
- Are outputs explicit and typed?
- Is accessibility part of the API contract?
- Can the component be tested or previewed in isolation?
