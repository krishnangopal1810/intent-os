# Security

The current product processes local fixture data and local macOS metadata when
manual live commands or the UI harness background timeline are running. It does
not use cloud storage, cloud inference, raw screenshot capture, keylogging, page
bodies, cookies, or external network calls. The dogfood beta adds a Chrome
extension bridge that posts bounded tab metadata only to a local
`127.0.0.1:58917` service, but the native macOS recorder is the default beta
capture source.

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
  and `data/activity/`, plus deterministic capture/session fixtures under
  `data/capture/`.
- Runtime artifacts are written under `.harness/runtime/`, which is ignored by
  git.
- Manual bounded live capture is explicit through `make observe-live`,
  `make observe-session`, or `make dev-live`; the `make dev` UI harness also
  starts a visible automated background timeline after deterministic artifacts
  are built.
- Dogfood beta data is stored locally in SQLite at
  `.harness/runtime/beta/intentos.sqlite` with a 30-day default retention
  setting. Users can pause/resume capture and delete all local user data.
- The beta native recorder samples only frontmost app/window metadata and
  best-effort browser title/URL fallback through existing local capture
  adapters. It writes normalized, privacy-filtered `ActivityEvent` rows to the
  local SQLite database.
- First-run onboarding and permission checks store only local readiness
  timestamps and permission health strings in SQLite settings/runtime status.
- Chrome extension bridge events are limited to URL, title, domain, tab/window
  IDs, active state, timestamp, source, and optional bounded page-kind metadata
  for YouTube/document pages. The service rejects page bodies, cookies, tokens,
  unsupported URLs, and privacy-excluded surfaces before persistence.
- No secrets, tokens, accounts, personal browser history databases, retained
  screenshots, page bodies, transcripts, or clipboard contents are required for
  verification.

## Import Policy

Manual CSV/JSON imports are no longer the preferred user-facing path because
they add friction, but any fixture or parser import work must stay local-only.
Browser history fixtures and ChatGPT parser fixtures must validate records at
the boundary, apply privacy exclusions and redaction before persistence, and
avoid writing cookies, tokens, full page bodies, full conversations, or browser
profile databases into runtime artifacts. CI must use deterministic fixtures or
copied test databases, never live user profiles.

## Live Capture Policy

The shipped live capture path is metadata-first. It may request Accessibility
permission for focused-window metadata and browser Automation permission for
active-tab title/URL. Screen Recording is not required for the current live
slice.
When started through `make dev`, background timeline capture is explicit in
`.harness/runtime/app.env`, `make app-status`, and
`.harness/runtime/logs/live-capture.log`, and it stops with `make app-stop`.
When started through `make beta-dev`, beta service, native recorder, and bridge
state are explicit in `.harness/runtime/beta/app.env`, `make beta-status`, and
`.harness/runtime/logs/beta-service.log`, and they stop with
`make beta-stop`.
When started through `make dogfood-smoke`, fake bridge rows are disabled; the
smoke preserves the dogfood database and records a blocked result if live
permissions or the native recorder are missing. A missing Chrome bridge is a
warning when native recorder events are increasing.

If future work adds ScreenCaptureKit, it must use Screen Recording permission
only for low-confidence fallback capture. Raw screenshots are disabled by
default and must not be retained unless an explicit local debug mode is enabled.

Sensitive surfaces must support exclusion by app, domain, URL pattern, and
window title. Private/incognito browser contexts should be ignored or reduced to
coarse app-level events. Password fields, authentication pages, banking, tax,
health, and payment forms should default to metadata-only capture or exclusion.
Map and directions URLs are also excluded by default because they can contain
precise location coordinates inside otherwise ordinary browser metadata.

## Trusted Beta Boundary

The current repo can be shared with trusted Mac friends as a source beta when
they understand that it runs a local recorder, writes local SQLite data under
`.harness/runtime/beta/`, and may need Accessibility and browser Automation
permissions. Testers should share `make beta-status`, permission-check output,
or generated smoke evidence for debugging instead of sharing raw SQLite data.

## Required Before Public Users

- Public authentication and authorization model
- User-facing retention controls beyond the dogfood 30-day default
- Secret management approach
- Backup and recovery approach
- Abuse and rate-limit strategy for public endpoints
- Permission UX for Accessibility permission, browser automation, and future
  Screen Recording.
