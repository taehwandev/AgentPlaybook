---
keyflow_id: sys_web_accessibility_i18n
status: review
type: ai-generated
---

# Web Accessibility I18n

Use for web-specific UI text, forms, menus, dialogs, keyboard flow, focus,
localization, and responsive text behavior. Also use
`common/accessibility-i18n.md` for platform-neutral accessibility and
internationalization rules.

## Web Accessibility

- Prefer semantic elements and accessible names.
- Dialogs need focus entry, focus trap or clear return behavior, and escape/close handling.
- Forms need labels, validation messages, and error association.
- Icon-only controls need accessible names or tooltips.
- Keyboard users must reach and operate critical actions.
- Disabled and permission-denied states should be understandable.

## Web I18n

- Use browser and framework locale APIs consistently with the repo's i18n boundary.
- Route titles, metadata, form errors, aria labels, and toast/dialog text need localization coverage when the repo supports it.
- Long translations must fit without overlap, clipping, or tiny unreadable controls.
- Product/domain terminology belongs in repo-local glossary when specific.

## Product Copy Boundaries

- UI copy must not imply real auth, invite, billing, or privacy guarantees before backend enforcement exists.
- Prototype/demo copy should be visibly scoped or kept out of production routes.
- Permission-denied copy should distinguish login required, role denied, plan limited, and unavailable feature.
- Avoid feature-explainer text inside the working UI when the state/action itself can communicate the workflow.

## Tests

- Query UI by role, label, and visible text.
- Test important keyboard flows.
- Check longest expected translation or pseudo-localized copy for compact UI.
- Verify dialogs restore focus or leave focus in a predictable place.
- Do not weaken accessible-name assertions without explaining the copy change.
