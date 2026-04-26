# Next Steps

This document lists the next useful slices for IntentOS. Prefer turning one item
at a time into an execution plan under `docs/plans/active/`.

## Recommended Next Slice

Live capture session timeline.

Goal: sample real app/window/browser metadata repeatedly over a short manual
session, merge adjacent samples, normalize them into local `ActivityEvent`
JSONL, and show the resulting timeline in the UI.

Why this is next:

- The first real macOS app/window adapter and best-effort browser tab
  enrichment now exist for one-shot manual capture.
- A short timeline is the next step toward behavior summaries that feel real.
- It gives the product a real capture loop without screenshots, OCR, or model
  complexity.
- It validates the `ActivityEvent` abstraction against live app/window/browser
  data.
- It keeps privacy local by default.

Acceptance criteria:

- Add a manual short-session capture command that samples every few seconds.
- Merge adjacent samples with the same app/surface/title.
- Replay the session JSONL through the existing classifier and reports.
- Add fixture or fake-based tests so CI does not require macOS permissions.
- Preserve No keylogging and no raw screenshot retention.
- Update the UI to show the session timeline.

## Harness Upgrades To Keep Current

- Keep the local UI shell current as product slices land. New user-visible
  behavior should appear in `web/` and pass `make validate-ui`.
- Keep structured runtime events current when new capture, classification,
  reporting, or UI paths are added.
- Add browser screenshot and DOM automation to `make validate-ui` once a browser
  automation dependency is introduced.
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
7. Browser screenshot validation harness for the existing local UI shell.

## Not Yet

- Cloud inference.
- Cloud storage of personal activity.
- Blocking or scheduling actions.
- Always-on background capture.
