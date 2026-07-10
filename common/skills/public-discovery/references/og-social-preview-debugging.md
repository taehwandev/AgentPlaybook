---
keyflow_id: sys_public_discovery_og_social_preview_debugging
status: stable
type: human-reviewed-needed
---

# Open Graph And Social Preview Debugging

Use this guide when a public page's Open Graph, social card, or link unfurl
preview looks stale, missing, or different from the deployed metadata.

Social preview debugging has two separate layers:

- the deployed page and image assets that crawlers can fetch
- the social platform's cached preview for the shared page URL

Changing only `og:image` may not update the preview immediately. Many platforms
cache the preview by the shared page URL, not only by the image URL.

## Verify The Deployed Output

Check the public URL, not only local source or build output.

```bash
curl -sL https://example.com/ | rg -n "og:image|og:title|og:description|twitter:image"
curl -I https://example.com/path/to/og-image.jpg
```

Confirm:

- `og:title`, `og:description`, `og:type`, `og:url`, and `og:image` are present.
- `twitter:card`, `twitter:title`, `twitter:description`, and `twitter:image`
  are present when the product expects X/Twitter cards.
- `og:image` and `twitter:image` use absolute HTTPS URLs.
- The image returns `200`, the expected `Content-Type`, and public cacheable
  bytes without authentication, cookies, signed URLs, or viewer-specific state.
- `og:image:width` and `og:image:height` match the actual image dimensions.
- The deployed HTML points to the new image URL after a deployment.
- Old image URLs are not still referenced by the current HTML, framework
  metadata layer, or tests.

When replacing a preview image, prefer a versioned asset URL such as
`/og-image-v2.jpg`, `/share-card-26.07.1.png`, or a content-hashed filename.
Keeping the same image URL can leave platform caches unchanged for a long time.

## Platform Debuggers And Cache Refresh

Use platform tools after verifying the deployed output. Enter the shared page
URL, not only the image URL.

| Platform | Tool | Cache behavior to remember |
| --- | --- | --- |
| Facebook / Meta | `https://developers.facebook.com/tools/debug/` | Use the Sharing Debugger to inspect the page URL and request a fresh scrape. |
| KakaoTalk | `https://developers.kakao.com/tool/debugger/sharing` | Requires Kakao developer login. Use the Sharing Debugger to clear or refresh the page URL cache; changing the image filename alone may not update the cached KakaoTalk card. |
| LinkedIn | `https://www.linkedin.com/post-inspector/` | Inspect the page URL and refresh LinkedIn's cached preview. |
| X / Twitter | `https://cards-dev.twitter.com/validator` | Requires login. Validate the card output for the page URL when X card rendering matters. |

KakaoTalk-specific notes:

- KakaoTalk frequently keeps a cached card for the shared page URL.
- A new `og:image` URL can still show the old preview until the page URL cache
  is refreshed in Kakao's Sharing Debugger.
- Existing messages in a chat usually keep the preview that was rendered when
  the message was sent. Test with a newly sent message after refreshing.
- If the debugger still shows stale data, confirm the public page URL itself is
  not redirected to an older canonical URL and that the deployed HTML is fresh.

## Debugging Sequence

1. Fetch the deployed page HTML and confirm the intended meta tags.
2. Fetch the image URL headers and confirm public `200` image response,
   `Content-Type`, and dimensions.
3. Check redirects and canonical URLs. Make sure the URL being shared is the
   same URL being refreshed in platform tools.
4. If the image changed, use a new versioned image URL.
5. Run platform debuggers for the shared page URL and request a refresh or
   re-scrape when the platform supports it.
6. Send a new message/post/share after refreshing. Do not judge from an already
   rendered chat message.
7. If the platform still shows stale data, test a temporary query-string page
   URL only as a diagnostic. Do not introduce duplicate canonical URLs as the
   product fix unless repo-local routing policy explicitly allows it.

## Common Failure Modes

- The source file changed but the production deployment still serves old HTML.
- The HTML changed but the platform cached the page URL preview.
- The image file changed in place with the same URL.
- The page redirects to a canonical URL that has different metadata.
- The preview image is blocked by auth, CSP, robots, hotlink rules, or private
  storage settings.
- The image dimensions in metadata no longer match the asset.
- The page has multiple `og:image` tags and the platform chooses the first one.
- Existing chat messages are being used as the verification surface instead of
  a newly shared message.

## Finish Criteria

A social preview fix is ready only when:

- deployed HTML contains the intended metadata
- preview image URL is public, stable, absolute, and cache-safe
- image headers and dimensions match the metadata
- relevant platform debugger shows the intended preview or a fresh scrape was
  requested
- KakaoTalk or other platform-specific cache refresh was performed when that
  platform is the failing surface
- tests or snapshots cover the expected public metadata when the repo has
  metadata contract tests
