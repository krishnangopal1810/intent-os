# Agent 3: Replay CLI and Runtime Harness

## Objective

Build the replay and runtime integration path that consumes captured
`ActivityEvent` JSONL and produces classifier reports. This agent owns the CLI
surface and product harness integration, using fixtures until Agent 1 and Agent
2 branches are merged.

## Owned Files

- `intentos/capture_replay.py`
- `intentos/capture_cli.py`
- `tests/test_capture_replay.py`
- `scripts/product/dev.sh`
- `scripts/product/verify.sh`
- `docs/APP_RUNTIME.md`
- `docs/RELIABILITY.md`

## Inputs

- Read [TRACKER.md](TRACKER.md) first.
- Read [../../../APP_RUNTIME.md](../../../APP_RUNTIME.md).
- Read [../../../RELIABILITY.md](../../../RELIABILITY.md).
- Reuse `intentos.activity`, `intentos.classifier`, and `intentos.reporting`.
- Expect Agent 1 to provide JSONL `ActivityEvent` records.
- Expect Agent 2 to provide browser/redaction helpers before live capture.

## Required Implementation

- Add a replay command that reads JSONL `ActivityEvent` dictionaries and emits
  the existing aggregate behavior report.
- Add `--json` output for replay reports.
- Add clear errors for malformed JSONL rows, missing required fields, and empty
  files.
- Add tests using inline temporary JSONL fixtures so CI does not need macOS
  permissions.
- Update `scripts/product/verify.sh` to run replay tests or a replay smoke
  command once the replay fixture exists.
- Update `scripts/product/dev.sh` to write a capture replay summary artifact in
  fixture or replay mode, without requiring live sensors.
- Update runtime docs with the replay command and artifact names.

## Out of Scope

- Raw capture adapters.
- Browser metadata adapters.
- Redaction policy implementation.
- Live macOS permissions.
- ScreenCaptureKit, Vision OCR, local model inference, or cloud calls.
- Changing the behavior taxonomy unless a test proves a gap.

## Verification

Run:

```sh
python3 -m unittest tests.test_capture_replay
make verify
make dev
make app-status
make observe
```

If Agent 1's JSONL reader is not merged yet, implement replay with a small local
reader and note the expected consolidation in the handoff.

## Handoff

Return:

- files changed
- replay CLI command examples
- runtime artifacts produced
- verification output
- any integration assumptions the coordinator must resolve after Agent 1 and
  Agent 2 merge
