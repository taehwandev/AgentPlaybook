---
keyflow_id: sys_public_discovery
status: review
type: human-reviewed-needed
---

# Public Discovery

Use when touching SEO, generative AI search visibility, AEO/GEO claims,
sitemap, robots, metadata, Open Graph previews, short links, public indexes,
search/discovery feeds, share previews, canonical URLs, localized alternates, or
structured data.

Public discovery is a data exposure surface. Treat it with the same care as a
public API response.

## Source Posture

Google Search guidance treats visibility in generative AI search experiences as
an extension of core SEO, not as a separate set of tricks. When a task mentions
AI search, AEO, GEO, AI Overviews, AI Mode, answer engines, or `llms.txt`, start
from normal search eligibility: useful public content, crawlable/indexable
technical structure, accurate metadata, and a safe public data boundary.

Reference the current Google Search Central guide when the task needs precise or
recent AI search policy:
`https://developers.google.com/search/docs/fundamentals/ai-optimization-guide`.

Routing aliases for this card include `seo`, `discovery`, `ai-search`, `aeo`,
`geo`, `generative-ai-search`, `llms-txt`, `sitemap`, `robots`, `canonical`,
`open-graph`, and `structured-data`. The workflow router may also infer `seo`
from these terms in the request text.

## Discovery Surfaces

Common public discovery outputs include:

- sitemap and robots policy
- canonical URLs and localized alternates
- metadata title and description
- Open Graph, social cards, link unfurls, and preview images
- public search indexes and discovery feeds
- share links, short links, and redirects
- structured data and public manifests
- public HTML rendered for crawlers and link preview bots
- machine-readable files intended for named agentic integrations

## AI Search Optimization

For Google Search, optimize the public search experience before optimizing for
AI-only terminology:

- Treat "AEO" and "GEO" as SEO framing unless a repo-local document names a
  different search surface, owner, and verification path.
- Prioritize helpful, reliable, people-first content with a clear topic,
  original viewpoint, practical experience, and enough detail to be useful
  without context from private systems.
- Prefer non-commodity content: implementation notes, tradeoffs, failures,
  measurements, screenshots, examples, procedures, or original analysis.
- Organize pages for human readers with clear titles, opening context,
  meaningful headings, concise sections, and relevant high-quality images or
  video when they help explain the content.
- Keep public pages crawlable, indexable, and eligible for snippets before
  expecting AI search visibility.
- Follow JavaScript SEO and server-rendering expectations for the framework in
  use; do not hide critical public content behind blocked scripts or client-only
  state without a documented crawler path.
- Provide a good page experience: mobile layout, latency, main-content clarity,
  accessible semantic structure, and no intrusive interstitials around the
  content users came for.

Do not add AI-search-only artifacts such as `llms.txt`, AI-only markdown mirrors,
forced chunking, query-variant page farms, or inauthentic external mentions for
Google Search visibility. If another agentic browser, partner, or internal
consumer needs a machine-readable file, document that consumer and verification
path; do not present it as required Google SEO work.

## Rules

- Only include resources that are meant to be discoverable by unauthenticated
  readers, crawlers, link preview bots, or public clients.
- Apply status, visibility, permission, tenant, locale, region, feature flag, and
  release-channel rules before generating discovery output.
- Public route does not mean public discovery. Some public routes are login,
  support, account, debug, test, or callback surfaces that should not be indexed.
- Metadata and previews must use sanitized, minimized fields. Do not leak private
  body content, internal identifiers, tokens, private URLs, draft titles, or
  deleted resource existence.
- Canonical URLs, localized alternates, short links, and redirects must agree
  with repo-local routing policy.
- Discovery caches can outlive normal UI state. Use conservative TTLs and
  invalidation when visibility, slug, title, deletion, or locale changes.
- Search-friendly URLs should not create duplicate canonical surfaces. Short
  links should redirect to the canonical URL with stable redirect semantics, and
  UTM parameters should be analytics data rather than alternate canonical pages.
- Structured data must match visible public content. Do not put private fields,
  draft-only claims, internal IDs, or hidden product assertions into JSON-LD.
- Open Graph and social preview images must be public, stable, and cache-safe.
  Do not use signed, one-time, viewer-specific, or permission-dependent image
  URLs in indexable metadata.
- AI-generated summaries, excerpts, or metadata may help discovery, but they
  must not overwrite the author's source content, change the page's claims, or
  expose text the page itself should not reveal.

## Do Not

- Do not build sitemap or preview data from raw admin/database objects without a
  public DTO or visibility filter.
- Do not include admin, management, debug, test, API, callback, migration, or
  internal utility routes in public discovery outputs.
- Do not use signed, private, one-time, or viewer-specific URLs in indexable
  metadata or previews.
- Do not reveal private resource existence through distinct preview, metadata,
  redirect, or 404 behavior unless the product explicitly allows it.
- Do not treat link preview bots as trusted users.
- Do not claim structured data, metadata, `llms.txt`, or prompt-shaped copy
  fixes search quality when the underlying public content is thin, duplicated,
  inaccessible, or not meant to be indexed.

## Checks

- Who is allowed to discover this resource without logging in?
- Which fields are safe for crawlers, previews, and public search?
- What happens after deletion, unpublish, privacy change, slug change, or locale
  change?
- Are canonical and alternate URLs consistent with routing?
- Are non-content routes excluded from discovery?
- Can cached preview or sitemap output outlive a permission change?
- Is the page eligible for normal search indexing and snippets before AI search
  visibility is discussed?
- Does the content provide original value beyond a generic summary?
- Do AI-generated summaries, teasers, or metadata stay subordinate to the
  public source content and author intent?
- Does structured data describe what an unauthenticated reader can actually see?
- Are locale alternates, canonical URLs, redirects, and short links mutually
  consistent?

## Verification

Verify public discovery as output data:

- generated sitemap/robots/search output excludes private and internal routes
- metadata/preview output is minimized and sanitized
- deleted, draft, private, permission-denied, and not-found resources do not leak
  existence through different public details
- canonical, locale alternate, short link, and redirect behavior agree with
  repo-local routing policy
- public pages render crawlable, useful content without relying on blocked
  scripts or private client state
- structured data validates and matches visible public content
- Open Graph previews use the intended public image fallback chain
- Search Console, Rich Results Test, PageSpeed Insights, framework metadata
  output, or local route snapshots are used when those tools are practical for
  the change
