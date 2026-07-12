---
keyflow_id: sys_ui_visual_verification
status: stable
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
- Grouped and decimal numeric text, unit labels, measurements, and value+unit
  pairs in compact labels, badges, tables, charts, summary cards, tooltips,
  notifications, and accessibility labels.
- Small and large viewports or containers relevant to the product.
- Touch and coarse-pointer input: any menu, dropdown, tooltip, popover, or
  control that is revealed or triggered only on `:hover`/`group-hover`/
  `focus-within` must also open and be fully operable by tap/click. Touch
  devices have no hover, so verify at a touch/mobile viewport, not only desktop
  hover.
- Light mode, dark mode, increased system font size, reduced motion, and high
  contrast when the platform supports them and the change can be affected.
- Keyboard focus, screen reader labels, hit targets, and visible focus state.
- Whether text, icons, badges, menus, or overlays overlap or resize the layout
  unexpectedly.
- Whether multiple entry points for the same command produce the same result.
- Whether visual state updates after actions, retries, refreshes, or navigation.

## Tools By Platform

Use repo-local tooling first. Common evidence sources include:

- Web: Playwright, Testing Library, axe, browser screenshots, geometry checks.
- Android: Compose UI Test, Espresso, screenshot or layout inspection.
- iOS: XCUITest, accessibility inspector, previews, screenshot checks.
- Desktop/application: platform smoke tests, WebDriver/Playwright when
  applicable, screenshot checks, menu/tray/window interaction smoke.

Also load `common/skills/accessibility-i18n/SKILL.md` for user-facing text, forms, labels,
dates, numbers, units, measurements, localization, focus, or screen-reader behavior. Load the
matching platform review card when platform UI tooling or conventions matter.

## Evidence

Use the strongest practical evidence available:

- component, view, or interaction tests for deterministic behavior
- accessibility-tree or semantic assertions for labels, roles, and states
- screenshot, pixel, geometry, or layout smoke checks for visual regressions
- manual smoke when automation cannot observe the affected surface

State what the check can and cannot prove. Geometry does not prove contrast or
copy quality. A screenshot does not prove that the command executed. A visible
button does not prove that the trusted boundary behind it was reached.

## Do Not Accept

- Do not treat a build, typecheck, or unit test as proof that a UI is readable,
  reachable, responsive, or accessible.
- Do not verify only the happy path when the changed surface has loading,
  empty, disabled, error, permission, offline, or long-text states.
- Do not approve a UI change from a cropped screenshot that hides the command
  entry point, overflow area, modal/sheet boundary, or next section.
- Do not ignore keyboard, focus, screen-reader labels, hit target, reduced
  motion, or high-contrast behavior when the change touches interaction.
- Do not accept hover-only reveal (`:hover`/`group-hover`/`focus-within`) as the
  sole way to open an actionable menu, dropdown, or control. Touch users cannot
  hover, so require an explicit tap/click toggle (with an outside-tap/escape
  close) and verify it on a touch/mobile viewport.
- Do not claim visual verification when the assets, icons, fonts, or remote
  data failed to load in the checked environment.

## Report

Name the scenario, environment, action, expected result, observed result, and
remaining risk when verification is manual or partial.
