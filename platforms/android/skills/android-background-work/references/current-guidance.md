---
keyflow_id: sys_android_background_work
status: review
type: ai-generated
---

# Android Background Work

Use when Android work touches WorkManager, foreground services, alarms, push notifications, sync, uploads, downloads, or long-running jobs.

## Rules

- Use WorkManager for deferrable durable work that must survive process death.
- Use foreground services only when user-visible ongoing work requires it.
- Model retry, cancellation, duplicate prevention, and idempotency before implementation.
- Respect Doze, battery saver, metered network, notification permission, and app standby behavior.
- Keep background work behind a use case or worker boundary, not inside Composables.
- Persist enough progress to recover after process death, but avoid storing sensitive payloads unnecessarily.

## Check

- What starts, cancels, retries, and observes this work?
- Does the user see progress, failure, and recovery actions?
- Can the job run twice without duplicate server effects?
- What happens across rotation, process death, logout, account switch, and network loss?
- Are notifications clear, permission-aware, and not leaking private content?

## Do Not

- Do not start durable background work directly from a Composable, View, or
  screen callback without a worker/use-case boundary and duplicate policy.
- Do not use a foreground service for polling, sync, or upload work that can be
  modeled as deferrable WorkManager work.
- Do not enqueue jobs that can run twice without idempotency keys, unique work,
  dedupe state, or server-side duplicate handling.
- Do not store raw credentials, private payloads, or personal data in worker
  input, notifications, progress rows, or logs unless the repo has an accepted
  secure-storage design.
- Do not ignore notification permission, Doze, battery saver, metered network,
  app standby, logout, or account switch because the happy path worker test
  passes.

## Tests

Cover worker success, retryable failure, permanent failure, cancellation, duplicate enqueue policy, and auth/session changes during work when applicable.
