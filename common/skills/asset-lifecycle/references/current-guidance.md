---
keyflow_id: sys_asset_lifecycle
status: stable
type: human-reviewed-needed
---

# Asset Lifecycle

Use when touching uploads, downloads, generated files, media, attachments,
signed or temporary URLs, public/private asset movement, asset cleanup, or asset
references embedded in persisted content.

Provider setup belongs in repo-local docs. This card defines reusable asset
safety rules only.

## Lifecycle

Model assets as a lifecycle, not as a URL string:

```text
select/create -> validate -> upload/stage -> reference -> publish/promote
-> serve/sign -> update -> unreference -> cleanup/delete
```

Each phase needs an owner and a verification point.

## Rules

- Asset visibility must follow the owning resource's visibility and permission
  policy.
- Temporary, draft, private, generated, public, and external assets must be
  distinguishable by metadata, storage key, or owning record.
- Signed, transformed, proxied, and unsigned URLs can refer to the same asset.
  Compare normalized owned asset keys for cleanup, not raw URL strings.
- Public or external URLs are not deletion targets unless the repo explicitly
  owns that storage key.
- Client-provided filenames, content types, paths, dimensions, and URLs are
  untrusted input.
- Asset references embedded in markdown, HTML, rich text, JSON, or serialized
  blocks need parser-aware handling; avoid broad regex rewrites when a parser or
  schema exists.
- Promote or publish assets only after the owning resource status and visibility
  are known.
- Cleanup should be idempotent and should tolerate already-missing assets.

## Do Not

- Do not infer authorization from possession of a URL.
- Do not expose private storage keys, long-lived signed URLs, credentials, or raw
  provider error payloads in public responses.
- Do not delete an asset only because a visible URL changed; first prove current
  references and ownership.
- Do not make persistence success depend on best-effort cleanup.
- Do not move private or draft assets into public locations during preview,
  autosave, import, or failed publish paths.
- Do not treat generated previews, thumbnails, and source files as the same
  asset unless the repo defines that relationship.

## Checks

- What resource owns this asset?
- Which users or clients can read, update, publish, or delete it?
- Is the asset temporary, draft, private, public, generated, or external?
- What is the canonical owned key for comparison and cleanup?
- What references must be updated when content changes?
- What happens when upload, promotion, signing, transformation, or cleanup fails?
- Can cleanup run twice without deleting unrelated assets?

## Verification

Verify the lifecycle phase that changed:

- upload validation rejects malformed type, size, path, and unauthorized actor
- publish/promotion respects resource visibility and status
- serving/signing denies unauthorized readers
- update diff compares canonical owned keys
- cleanup ignores external/unowned assets and is idempotent
- persisted content and rendered output reference the same intended asset
