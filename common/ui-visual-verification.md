---
keyflow_id: sys_ui_visual_verification
status: review
type: human-reviewed-needed
---

# UI Visual Verification

Use when changing UI layout, interaction, visible text, controls, navigation,
responsive behavior, accessibility labels, or state presentation.

## Default

A build or typecheck proves that UI code compiles. It does not prove that the UI
is usable, visible, readable, or wired to the intended action.

Verify the user path, not only the component in isolation, when the change
affects navigation, commands, permissions, persistence, or cross-surface state.

## Check

- Main success path.
- Empty, loading, disabled, error, unavailable, and permission-denied states.
- Long text, localized text, missing images, missing icons, and slow data.
- Small and large viewports or containers relevant to the product.
- Keyboard focus, screen reader labels, hit targets, and visible focus state.
- Whether text, icons, badges, menus, or overlays overlap or resize the layout
  unexpectedly.
- Whether multiple entry points for the same command produce the same result.
- Whether visual state updates after actions, retries, refreshes, or navigation.

## Evidence

Use the strongest practical evidence available:

- component, view, or interaction tests for deterministic behavior
- accessibility-tree or semantic assertions for labels, roles, and states
- screenshot, pixel, geometry, or layout smoke checks for visual regressions
- manual smoke when automation cannot observe the affected surface

State what the check can and cannot prove. Geometry does not prove contrast or
copy quality. A screenshot does not prove that the command executed. A visible
button does not prove that the trusted boundary behind it was reached.

## Report

Name the scenario, environment, action, expected result, observed result, and
remaining risk when verification is manual or partial.
