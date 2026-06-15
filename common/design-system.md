---
keyflow_id: sys_3ebdb5c993eb
status: review
type: ai-generated
---

# Design System

Use when creating or changing shared UI primitives, tokens, patterns, component
defaults, or reusable interaction rules.

For general reusable-code extraction rules, also use
`common/reusable-code-design.md`. For Android Compose UI, also use
`platforms/android/android-compose-ui.md`.
For reusable component API shape, controlled/uncontrolled state, slots, and
caller-owned product policy, also use `component-api-design.md`.

## Direction

Build a design system as product infrastructure, not decoration. Start from
repeated product needs, then extract stable primitives. Do not create generic
components before real usage proves the contract.

For UI work, do not bypass the design system. If a repo already has tokens,
primitives, component variants, previews, or stories, use or extend them before
adding one-off styling in a screen. If no design-system layer exists and the
task creates a reusable control, repeated visual rule, or new app/screen
surface, create the smallest useful design-system layer first: semantic tokens,
one primitive, and an example or preview when the platform supports it.

## Layers

```text
Tokens -> Primitives -> Composed Components -> Product Patterns -> Screens
```

Use the lowest layer that owns the decision:

- Tokens: semantic color, typography, shape, spacing, elevation, motion, density,
  and state values.
- Primitives: buttons, text, text fields, rows, icons, dividers, sheets,
  scaffold, navigation, loading indicators, and accessibility behavior.
- Composed components: reusable combinations with slots and typed state, but no
  product workflow.
- Product patterns: domain-aware reusable flows, cards, or sections owned by a
  feature/common layer rather than the primitive design system.
- Screens: route, product copy, data mapping, permissions, analytics, and
  workflow decisions.

## Rules

- Tokens are semantic: role, state, density, emphasis; not just color names.
- Primitives expose behavior and accessibility contracts, not product-specific copy.
- Components include loading, disabled, error, empty, focus, hover, pressed states.
- Product patterns may know domain workflow; primitives should not.
- Visual decisions must support scanning, comparison, repeated action, and accessibility.
- A new component needs usage examples and replacement guidance for old patterns.
- A reusable component needs a stable caller contract, examples or previews, and
  clear ownership of product-specific copy, routing, analytics, and policy.
- Component defaults should be stable, deterministic, and side-effect free. A
  theme-dependent default may read theme context through the platform idiom, but
  it should not read product state, globals, repositories, or runtime config.
- Prefer wrappers around platform UI libraries when the wrapper encodes a real
  product contract such as typography scale, touch target, loading behavior,
  accessibility semantics, or design tokens. Do not wrap only to rename an API.
- Keep design-system modules free of routes, feature ids, analytics names,
  permission policy, billing or entitlement rules, repository calls, fake data,
  and product-specific copy.
- Use slots for caller-owned icons, media, trailing actions, and rich content
  when the structure is reusable but content ownership belongs to the caller.
- Avoid boolean flag APIs that encode caller-specific variants. Split the
  component, keep it feature-local, or add a typed state when the modes represent
  real component states.
- Promotion from feature-local UI to the design system requires a stable name,
  at least two credible call sites or a foundational primitive need, examples or
  previews, and migration guidance for old usage.

## Do Not

- Do not add raw colors, fonts, spacing, radii, shadows, motion, z-index, or
  component variants in a repeated UI surface when an existing token, primitive,
  or component can express the need.
- Do not create a screen-only "design-system" component that embeds product
  copy, routing, analytics names, permission policy, billing rules, repository
  calls, or feature DTOs.
- Do not create reusable-looking components, hooks, style helpers, or functions
  without a stable caller contract. A design-system API must be reusable by a
  second caller or be a foundational primitive.
- Do not use boolean flags or nullable option bags to force unrelated product
  variants through one component. Split the component, keep it feature-local, or
  model the state explicitly.
- Do not replace multiple UI surfaces with a new primitive until the primitive
  has examples, previews, fixtures, stories, snapshots, or focused tests for the
  affected states.
- Do not leave a design-system change without adoption guidance when it replaces
  an existing pattern.

## Token Modeling

Prefer semantic tokens that describe role and state:

```text
surface/default, surface/raised, text/primary, text/secondary,
action/primary/enabled, action/primary/disabled, border/focus,
spacing/control-md, radius/card, motion/emphasis
```

Avoid exporting raw palette names as the main API when callers need semantic
meaning. Raw palette values can exist below the token layer, but components
should consume semantic roles.

For platform-specific design systems, keep token holders compatible with that
platform's stability model. For example, Compose token/default holders should be
immutable or stable; web token objects should avoid mutation during render.

## Component Contract

A reusable component API should define:

- required and optional state, including loading, disabled, selected, error,
  empty, read-only, and permission-denied states when relevant
- caller-owned actions and callbacks
- slot ownership for leading/trailing/media/action content
- accessibility labels, roles, focus behavior, and touch/click targets
- long text, localization, small screen, dark mode, and high-contrast behavior
- replacement guidance when it supersedes an older pattern

If the component needs a repository, route, whole screen state, feature-specific
DTO, or many caller flags, it is probably a product pattern or feature-local
component, not a design-system primitive.

## Previews And Examples

Every new or meaningfully changed token set, primitive, composed component, or
product pattern needs an example, preview, story, fixture, snapshot, or focused
test when the repo supports one.

Cover the states affected by the change:

- default, hover/pressed/focused, disabled, loading, error, empty, selected,
  expanded, destructive, and read-only when applicable
- light, dark, high-contrast, reduced-motion, density, and platform appearance
  variants when supported
- long localized text, missing icons/media, constrained containers, and small
  screens
- permission denied, unavailable, offline, or read-only states when the
  component displays product or platform capability

Do not use examples or previews that call network, persistence, credentials,
user-specific files, current time, randomness, or device-only services. Use
fixtures and deterministic state.

## Check

- Is this repeated in at least two places or clearly foundational?
- What is customizable, and what must stay fixed?
- Does it work with keyboard, screen readers, long text, localization, and small screens?
- Can product teams adopt it without rewriting feature logic?
- Are semantic tokens used instead of leaking one feature's exact visual
  decisions?
- Does the design-system boundary keep product policy in the caller?
- Are examples, previews, or focused tests covering common and edge states?
