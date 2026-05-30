---
keyflow_id: sys_0678d6c5f03c
status: review
type: ai-generated
---

# Web Review

Use for React/web UI, browser behavior, and frontend PR review.

## Review

- Check route/data boundaries, cache invalidation, form validation, and error states.
- Check route/page, container/screen, hook, and component boundaries against
  `web-react-ui.md` when React UI changed.
- Confirm typed UI state represents loading, content, empty, error, permission
  denied, offline, disabled, and submitted states when applicable.
- Verify accessibility: labels, roles, focus order, keyboard use, contrast.
- Check responsive layout for mobile, tablet, desktop.
- Ensure permission and entitlement checks are not UI-only.
- Look for duplicated fetch/error/permission logic in components.
- Check whether mock data, demo toggles, and localStorage state are clearly separated from real service behavior.

## React Checks

- Component state ownership is local unless multiple screens actually need it.
- Effects have dependencies, cleanup, and abort behavior where relevant.
- Derived state is not stored unnecessarily.
- Context/provider additions have cross-route ownership, not one-screen convenience.
- Hooks expose intent and state, not hidden product policy.
- Form submit paths handle pending, success, validation error, permission denied, and network error.

## Service Checks

- Invite, share, billing, auth, and role UI do not promise server enforcement that does not exist.
- Buttons hidden by permission are also blocked at action/API boundary.
- Role and plan checks use named helpers or policy functions instead of repeated JSX booleans.
- Browser storage is not the source of truth for protected access.

## SEO And AI Search Checks

When a public route, marketing page, content page, profile, article, docs page,
or share surface changed, load `common/public-discovery.md` and review it as a
public output contract.

- Metadata title, description, canonical URL, locale alternates, robots policy,
  Open Graph, and social preview output match the intended public page.
- Sitemap and robots behavior include only pages that unauthenticated readers
  and crawlers should discover.
- Public content is crawlable/indexable and not hidden behind blocked scripts,
  private client state, or login-only fetches.
- Structured data, when present, describes visible public content and excludes
  private fields, draft state, internal IDs, and hidden claims.
- Generative AI search work improves normal SEO fundamentals: useful
  non-commodity content, clear headings, technical crawlability, page
  experience, media quality, and duplicate-content reduction.
- Do not add `llms.txt`, AI-only mirrors, forced chunking, query-variant page
  farms, or inauthentic mentions as a Google Search optimization unless
  repo-local policy names another consumer and verification path.

## Tools

- Static: TypeScript, ESLint, framework lint.
- Unit: Vitest or Jest for policy, mapper, hook, reducer.
- Component: Testing Library by role, label, visible text, interaction.
- UI/E2E: Playwright for navigation, auth, forms, permissions, critical flows.
- A11y: axe or Playwright accessibility checks when available.
- Discovery: framework metadata output, sitemap/robots snapshots, Rich Results
  Test, Search Console, or PageSpeed Insights when practical.

## UI Test Focus

- User can complete the main flow.
- Loading, empty, error, and permission-denied states render correctly.
- Container/screen split or equivalent keeps data/effects out of presentational
  components.
- Keyboard-only path works for forms, dialogs, menus, tables.
- No text overflow or layout break across key viewport sizes.
- Denied users cannot trigger the protected command, not only fail to see the button.
