# Next Steps

This document lists the next useful slices for IntentOS. Prefer turning one item
at a time into an execution plan under `docs/plans/active/`.

## Recommended Next Slice

Metadata-only macOS live activity capture prototype.

Goal: sample the active macOS app, focused window, and one browser's active tab
metadata; normalize that data into local `ActivityEvent` JSONL; and replay it
through the existing classifier.

Why this is next:

- It moves IntentOS from synthetic fixtures toward real user behavior.
- It gives the product a real capture loop without screenshots, OCR, or model
  complexity.
- It validates the `ActivityEvent` abstraction against live app/window/browser
  data.
- It keeps privacy local by default.

Acceptance criteria:

- Add metadata-only macOS capture adapters for active app/window and one
  browser.
- Write local JSONL `ActivityEvent` records.
- Replay captured JSONL through the existing classifier and reports.
- Add fixture or fake-based tests so CI does not require macOS permissions.
- Preserve No keylogging and no raw screenshot retention.
- Update `make verify`.

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
