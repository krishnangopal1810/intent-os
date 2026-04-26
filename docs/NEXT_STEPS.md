# Next Steps

This document lists the next useful slices for IntentOS. Prefer turning one item
at a time into an execution plan under `docs/plans/active/`.

## Recently Completed Slice

Live capture session timeline.

Goal: sample real app/window/browser metadata repeatedly over a short manual
session, merge adjacent samples, normalize them into local `ActivityEvent`
JSONL, and show the resulting timeline in the UI.

Why this mattered:

- The first real macOS app/window adapter and best-effort browser tab
  enrichment now exist for one-shot manual capture.
- A short timeline is the next step toward behavior summaries that feel real.
- It gives the product a real capture loop without screenshots, OCR, or model
  complexity.
- It validates the `ActivityEvent` abstraction against live app/window/browser
  data.
- It keeps privacy local by default.

Completed acceptance criteria:

- Add a manual short-session capture command that samples every few seconds.
- Merge adjacent samples with the same app/surface/title.
- Replay the session JSONL through the existing classifier and reports.
- Add fixture or fake-based tests so CI does not require macOS permissions.
- Preserve no keylogging and no raw screenshot retention.
- Update the UI to show the session timeline.
- Refresh checked-in UI screenshot evidence with `make update-ui-screenshot`.

Harness self-sufficiency for this slice:

- Sufficient now: `ActivityEvent` boundary, one-shot macOS/browser capture,
  privacy exclusions, JSONL replay, UI artifact loading, live replay preference,
  checked-in screenshot evidence, `make observe-live`, `make validate-ui`, and
  `make verify`.
- Added with the slice: deterministic session fixtures, session merge tests, a
  documented session diagnostic command, structured runtime events for session
  capture, UI timeline validation, and updated screenshot evidence.

## Recommended Next Slice

Manual real-data import.

Goal: let a user import local CSV/JSON activity data into the existing
`ActivityEvent` boundary, classify it through the current report path, and show
the resulting daily behavior summary in the UI.

Why this is next:

- The session timeline proves the event/report/UI path for real time windows.
- Import gives the product enough historical data to produce meaningful daily
  behavior narratives without requiring always-on capture.
- It expands evaluation fixtures with more realistic user examples before
  adding OCR or local models.

Acceptance criteria:

- Document a small CSV/JSON import schema that maps into `ActivityEvent`.
- Add an import command that validates input and writes local JSONL or report
  artifacts under `.harness/runtime/artifacts/`.
- Add deterministic import fixtures and tests for validation errors,
  classification, and replay.
- Update the UI only if imported report artifacts add user-visible behavior.
- Preserve local-only processing and privacy exclusions.

## Harness Upgrades To Keep Current

- Keep the local UI shell current as product slices land. New user-visible
  behavior should appear in `web/` and pass `make validate-ui`.
- Refresh `docs/assets/screenshots/intent-os-ui.png` with
  `make update-ui-screenshot` whenever UI source, fixture inputs, or report
  output changes.
- Keep structured runtime events current when new capture, classification,
  reporting, or UI paths are added.
- Add richer DOM automation to `make validate-ui` when UI workflows become
  interactive enough that static HTML checks and checked-in screenshots are no
  longer sufficient.
- Add deterministic capture fixtures for every real adapter. The macOS
  frontmost adapter now has `data/capture/macos_frontmost_snapshot.json`, and
  browser active-tab enrichment has
  `data/capture/browser_active_tab_snapshot.json`; session behavior now has
  `data/capture/fake_session_observations.json`. Future ScreenCaptureKit, OCR,
  and model adapters need equivalent fixtures.
- Add structured runtime logs for capture, classification, and reporting before
  adding a persistent service. Stable fields should include `component`,
  `event`, `mode`, `artifact_path`, `duration_ms`, `event_count`, and `status`.
- Keep `make observe-live` as the manual local sensor diagnostic and expand it
  when browser metadata capture lands.
- Add stricter architecture rules as modules grow. Promote repeated review
  comments into `scripts/harness/lint.py`.
- Add cleanup/audit scripts that scan stale plans, stale docs, fixture drift,
  and quality scorecard gaps.

## Then

1. Browser history import for local Chrome/Safari/Arc exports or copied DBs.
2. ChatGPT export parser for classifying conversation intent.
3. UI for daily behavior narratives once data import and evaluation stabilize.
4. ScreenCaptureKit fallback plus Vision OCR for low-confidence events.
5. Local model second-pass classifier through Foundation Models, Core ML, or
   MLX once fixture evaluation justifies it.
6. Richer DOM automation for the local UI shell once interactions exist.

## Not Yet

- Cloud inference.
- Cloud storage of personal activity.
- Blocking or scheduling actions.
- Always-on background capture.
