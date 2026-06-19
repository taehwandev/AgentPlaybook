---
keyflow_id: sys_accessibility_i18n
status: review
type: human-reviewed-needed
---

# Accessibility I18n

Use when changing UI text, forms, controls, navigation, media, keyboard/focus
behavior, dates, numbers, currency, localization, or user-facing error states.

## Accessibility Rules

- Interactive controls need an accessible name, role, state, and clear target.
- Do not rely on color, icon shape, motion, or position alone to communicate
  state or errors.
- Preserve keyboard, switch control, screen reader, and touch navigation paths
  when the platform supports them.
- Keep focus order predictable after navigation, dialog, menu, validation, and
  async state changes.
- Support text scaling, long labels, small screens, and high contrast modes where
  the platform provides them.
- Media, image, chart, map, and canvas surfaces need text alternatives or a
  product-approved fallback path.
- Motion and animation should respect reduced-motion settings when the platform
  exposes them.

## Internationalization Rules

- Keep user-facing strings out of low-level logic when the repo has a localization
  boundary.
- Do not concatenate translated fragments when grammar, plurality, gender, or word
  order can vary.
- Format dates, times, time zones, numbers, currency, addresses, and names with
  locale-aware APIs when shown to users.
- Store stable machine values separately from localized display values.
- Design layouts for long text, missing translations, and mixed-language content.
- Avoid hard-coded region, calendar, currency, measurement, or address assumptions
  unless the product is intentionally scoped that way.

## Visible Number Formatting

All user-visible finite numbers should use the product's locale-aware number
formatter. Thousands grouping is required for visible numeric values when the
locale supports grouping; for Korean and English locales this normally renders
as comma grouping, such as `1,234` or `12,345,678`. Do not hand-build grouped
numbers with string replacement when the platform provides a formatter.

Choose decimal precision by the value's meaning:

- Counts, quantities, seats, pages, ranks, inventory, attempts, notifications,
  and other discrete values: use grouped integers with no decimal places.
- Currency and accounting values: use the currency formatter and the product's
  currency policy. Use fixed two decimals only when the currency or product
  surface needs minor-unit precision, comparison, or reconciliation.
- Percentages, rates, averages, scores, measurements, storage sizes, durations,
  and calculated metrics: allow up to two decimals when precision affects the
  user's decision. Prefer no decimals or trimmed decimals when the extra
  precision is noise.
- Tables, dashboards, financial summaries, and side-by-side comparisons may use
  fixed two decimals for alignment when the metric is inherently decimal and
  the unit is clear.
- Identifiers such as years, order numbers, phone numbers, postal codes,
  versions, ticket ids, card endings, and opaque codes are not numeric display
  values. Do not add grouping or decimals to them.

Keep raw values separate from display strings. Round only for display, never for
stored values, calculations, sorting, filtering, billing, quotas, or API
contracts. Define how `0`, negative values, missing values, very large values,
`NaN`, and infinity render before shipping a numeric UI.

Do not:

- Render user-visible numbers with raw `toString`, implicit string
  interpolation, JSON output, or database values when a locale-aware formatter
  should own grouping and decimals.
- Show mixed precision for the same metric in one table, chart, comparison
  group, or repeated card list unless the difference communicates a real state.
- Add `.00` to counts, ranks, or other discrete values.
- Drop grouping separators only because a number is inside a badge, chip, chart
  label, tooltip, axis, table cell, toast, notification, or accessibility label.
- Hard-code comma grouping when the surface supports multiple locales. Use the
  locale formatter; document a product-scoped exception only when the product
  intentionally uses one fixed locale.

## Check

- Can the user complete the main path with keyboard or assistive technology?
- Does the UI still work with long text, text scaling, and small screens?
- Are validation and permission errors announced or visible in context?
- Are user-facing dates, numbers, and currencies formatted for the user's locale,
  including required grouping and the intended decimal precision?
- Is any text embedded in images, generated assets, placeholders, logs, or
  low-level constants where localization cannot reach it?

## Tests

Use platform-appropriate checks such as role/name queries, keyboard navigation,
screen reader labels, screenshot or layout checks with long text, and locale,
number-format, currency, or timezone-specific unit tests when relevant.
