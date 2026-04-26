# Security

The current product processes local fixture data only. It does not use cloud
storage, cloud inference, browser APIs, live macOS capture, or external network
calls.

## Baseline Rules

- Do not commit secrets.
- Keep `.env` files local.
- Validate all external input at boundaries.
- Treat user data as private by default.
- Prefer least-privilege tokens and service permissions.
- Document new data stores, credentials, and external integrations.
- No keylogging.
- Raw screenshots are disabled by default.
- Keep personal activity data local-only unless a future explicit product and
  privacy review changes that default.

## Current Data Handling

- Input data is read from a local JSON file.
- Product verification uses deterministic fixture data under `data/youtube/`
  and `data/activity/`.
- Runtime artifacts are written under `.harness/runtime/`, which is ignored by
  git.
- No secrets, tokens, accounts, or personal browser history are required for the
  MVP.

## Live Capture Policy

The planned live capture slice is metadata-first. It may request Accessibility
permission for focused-window metadata and browser automation permission for
active-tab title/URL. Screen Recording is not required for the first live slice.
When started through `make dev`, background capture is explicit in
`.harness/runtime/app.env`, `make app-status`, and
`.harness/runtime/logs/live-capture.log`, and it stops with `make app-stop`.

If future work adds ScreenCaptureKit, it must use Screen Recording permission
only for low-confidence fallback capture. Raw screenshots are disabled by
default and must not be retained unless an explicit local debug mode is enabled.

Sensitive surfaces must support exclusion by app, domain, URL pattern, and
window title. Private/incognito browser contexts should be ignored or reduced to
coarse app-level events. Password fields, authentication pages, banking, tax,
health, and payment forms should default to metadata-only capture or exclusion.
Map and directions URLs are also excluded by default because they can contain
precise location coordinates inside otherwise ordinary browser metadata.

## Required Before Real Users

- Authentication and authorization model
- Data retention policy
- Secret management approach
- Backup and recovery approach
- Abuse and rate-limit strategy for public endpoints
- Permission UX for Accessibility permission, browser automation, and future
  Screen Recording.
