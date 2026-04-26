# Next Steps

This document lists the next useful slices for IntentOS. Prefer turning one item
at a time into an execution plan under `docs/plans/active/`.

## Recommended Next Slice

Metadata-only browser tab capture adapter.

Goal: enrich the current frontmost macOS app/window capture with one browser's
active tab URL/title metadata; normalize that data into local `ActivityEvent`
JSONL; and replay it through the existing classifier.

Why this is next:

- The first real macOS app/window adapter already exists, but browser tab
  metadata is still fixture-only.
- It moves IntentOS from app/window metadata toward semantic browsing behavior.
- It gives the product a real capture loop without screenshots, OCR, or model
  complexity.
- It validates the `ActivityEvent` abstraction against live app/window/browser
  data.
- It keeps privacy local by default.

Acceptance criteria:

- Add a metadata-only browser adapter for one supported browser.
- Write local JSONL `ActivityEvent` records.
- Replay captured JSONL through the existing classifier and reports.
- Add fixture or fake-based tests so CI does not require macOS permissions.
- Preserve No keylogging and no raw screenshot retention.
- Update `make verify` and `make observe-live` documentation if the live
  diagnostic starts reporting browser permission state.

## Harness Upgrades To Keep Current

- Add a local app shell when we build the UI. It should run per worktree,
  publish URL/process/log state through `.harness/runtime/app.env`, and be
  validated by `make validate-ui`.
- Add deterministic capture fixtures for every real adapter. The macOS
  frontmost adapter now has `data/capture/macos_frontmost_snapshot.json`; future
  browser, ScreenCaptureKit, OCR, and model adapters need equivalent fixtures.
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

1. Manual CSV/JSON import for real `ActivityEvent` data.
2. Browser history import for local Chrome/Safari/Arc exports or copied DBs.
3. ChatGPT export parser for classifying conversation intent.
4. UI for daily behavior narratives once data import and evaluation stabilize.
5. ScreenCaptureKit fallback plus Vision OCR for low-confidence events.
6. Local model second-pass classifier through Foundation Models, Core ML, or
   MLX once fixture evaluation justifies it.
7. Browser/UI validation harness once a frontend exists.

## Not Yet

- Cloud inference.
- Cloud storage of personal activity.
- Blocking or scheduling actions.
- Always-on background capture.
