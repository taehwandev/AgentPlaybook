---
keyflow_id: sys_3ebdb5c993eb
status: review
type: ai-generated
---

# Design System

Use when creating or changing shared UI primitives, tokens, patterns, or reusable interaction rules.

For general reusable-code extraction rules, also use
`common/reusable-code-design.md`. For Android Compose UI, also use
`platforms/android/android-compose-ui.md`.

## Direction

Build a design system as product infrastructure, not decoration. Start from repeated product needs, then extract stable primitives. Do not create generic components before real usage proves the contract.

## Layers

```text
Tokens -> Primitives -> Composed Components -> Product Patterns -> Screens
```

## Rules

- Tokens are semantic: role, state, density, emphasis; not just color names.
- Primitives expose behavior and accessibility contracts, not product-specific copy.
- Components include loading, disabled, error, empty, focus, hover, pressed states.
- Product patterns may know domain workflow; primitives should not.
- Visual decisions must support scanning, comparison, repeated action, and accessibility.
- A new component needs usage examples and replacement guidance for old patterns.
- A reusable component needs a stable caller contract, examples or previews, and
  clear ownership of product-specific copy, routing, analytics, and policy.

## Check

- Is this repeated in at least two places or clearly foundational?
- What is customizable, and what must stay fixed?
- Does it work with keyboard, screen readers, long text, localization, and small screens?
- Can product teams adopt it without rewriting feature logic?
