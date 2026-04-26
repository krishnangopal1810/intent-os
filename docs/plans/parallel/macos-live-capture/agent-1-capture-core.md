# Agent 1: Capture Core and JSONL Writer

## Objective

Build the core capture package for metadata-only macOS activity observations.
This agent owns the domain objects and fake sensor path that let CI exercise
capture behavior without macOS permissions.

## Owned Files

- `intentos/capture/__init__.py`
- `intentos/capture/core.py`
- `intentos/capture/jsonl.py`
- `data/capture/fake_macos_observations.json`
- `tests/test_capture_core.py`

## Inputs

- Read [TRACKER.md](TRACKER.md) first.
- Read [../../../product/live-capture.md](../../../product/live-capture.md).
- Read [../../../product/TAXONOMY.md](../../../product/TAXONOMY.md).
- Reuse `ActivityEvent` from `intentos/activity.py`.
- Do not modify classifier behavior.

## Required Implementation

- Create an `intentos.capture` package.
- Define a raw observation object for app/window metadata with fields for:
  start time, end time, app name, bundle ID, process ID, window title, source,
  and optional metadata.
- Add validation that rejects missing app names, invalid timestamps, negative
  durations, and non-dictionary metadata.
- Add conversion from raw observation to `ActivityEvent`.
- Add a JSONL writer and reader for normalized `ActivityEvent` dictionaries.
- Add a fake fixture under `data/capture/fake_macos_observations.json` with at
  least six examples covering coding, ChatGPT learning, admin, communication,
  passive consumption, and unknown.
- Add tests for validation, conversion, JSONL round trip, and preservation of
  sparse/unknown events.

## Out of Scope

- Browser active-tab URL/title capture.
- Redaction or exclusion policy.
- Replay CLI.
- Runtime harness commands.
- `scripts/harness/lint.py` layer updates unless the coordinator assigns them.
- Any live macOS API calls.
- ScreenCaptureKit, Vision OCR, model inference, or cloud calls.

## Verification

Run:

```sh
python3 -m unittest tests.test_capture_core
make verify
```

If `make verify` fails because new files are not yet known to harness lint,
report that in the handoff instead of editing another agent's files.

## Handoff

Return:

- files changed
- public functions/classes added
- sample JSONL shape
- verification output
- any interface assumptions Agent 2 or Agent 3 must honor
