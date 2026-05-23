---
keyflow_id: sys_8c200d3027b7
status: draft
type: ai-generated
---

# Architecture Selection

Use when choosing or changing architecture for an app, service, or major feature.

## Default

Prefer the repo's existing architecture. For new work, start with shared common rules, then choose one execution track: Android, iOS, Web, Server, or Application.

## Fit By Shape

- SaaS/admin UI: feature modules, route/data boundaries, server-state cache, reusable form/table patterns.
- Real-time/collab: event model, sync boundary, optimistic updates, conflict rules.
- iOS/Android: MVVM or unidirectional state, repositories, platform adapters.
- Application: commands/use cases, window/menu state, local persistence, system adapters.
- Backend API: route/controller, use case/service, repository/client, explicit auth/tenant boundary.

## Escalate When

Permissions, billing, offline sync, background jobs, multi-client reuse, or complex domain rules make simple feature structure hard to reason about.

## Check

What changes together? Who owns state? Where do platform APIs live? What boundary should tests target?
