# Next Steps

This document lists the next useful slices for IntentOS. Prefer turning one item
at a time into an execution plan under `docs/plans/active/`.

## Recommended Next Slice

Manual real-activity import.

Goal: let a user provide local CSV or JSON activity events, normalize them into
`ActivityEvent`, classify them, and compare output against the fixture-based
pipeline.

Why this is next:

- It moves IntentOS from synthetic fixtures toward real user behavior.
- It avoids browser permissions and macOS capture complexity.
- It expands evaluation data before adding sensors.
- It keeps privacy local by default.

Acceptance criteria:

- Add a documented CSV/JSON import format.
- Normalize imported rows into `ActivityEvent`.
- Reject malformed rows with clear errors.
- Add real-ish fixture examples and tests.
- Update `make verify`.

## Then

1. Browser history import for local Chrome/Safari/Arc exports or copied DBs.
2. ChatGPT export parser for classifying conversation intent.
3. macOS active app/window capture.
4. UI for daily behavior narratives once data import and evaluation stabilize.
5. Browser/UI validation harness once a frontend exists.

## Not Yet

- Cloud inference.
- Cloud storage of personal activity.
- Blocking or scheduling actions.
- Always-on background capture.
