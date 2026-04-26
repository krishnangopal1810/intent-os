# macOS Live Capture Parallel Tracker

This tracker coordinates three Codex agents building the metadata-only macOS
live activity capture prototype from the completed plan:
[2026-04-26-macos-live-activity-capture-prototype.md](../../completed/2026-04-26-macos-live-activity-capture-prototype.md).

## Coordination Rules

- Each agent owns only the files listed in its task file.
- Agents must not edit another agent's owned files.
- Agents should read all three task files before starting so interfaces stay
  compatible.
- Agents should not update this tracker directly unless the coordinator grants
  them the tracker lock.
- Agents must keep `make verify` passing in their own branch.
- If an agent needs another owned file, it must stop and report the dependency
  instead of editing across ownership boundaries.
- Live capture must remain metadata-only in this phase: no keylogging, no raw
  screenshot retention, no ScreenCaptureKit capture, no Vision OCR, no cloud
  inference, and no always-on daemon.

## Agent Assignments

| Agent | Task File | Responsibility | Status |
| --- | --- | --- | --- |
| Agent 1 | [agent-1-capture-core.md](agent-1-capture-core.md) | Core capture domain, fake macOS observations, JSONL writer | Implemented |
| Agent 2 | [agent-2-browser-redaction.md](agent-2-browser-redaction.md) | Browser tab metadata model, redaction and exclusion policy | Implemented |
| Agent 3 | [agent-3-replay-runtime.md](agent-3-replay-runtime.md) | Replay CLI, reports, runtime harness integration | Implemented |

## Shared Interfaces

All agents should align on this event shape before implementation:

```json
{
  "start_time": "2026-04-26T10:00:00Z",
  "end_time": "2026-04-26T10:05:00Z",
  "app_name": "ChatGPT",
  "bundle_id": "com.openai.chat",
  "window_title": "IntentOS live capture prototype",
  "url": null,
  "domain": null,
  "visible_text_excerpt": "bounded and redacted text when allowed",
  "source": "fake_macos",
  "metadata": {
    "process_id": 12345,
    "capture_mode": "fake_sensor"
  }
}
```

The normalized output must become the existing `ActivityEvent` structure.
Agents should preserve `unknown` when metadata is sparse or conflicting.

## Integration Contract

- Agent 1 produces JSONL-compatible `ActivityEvent` records from fake macOS
  app/window observations.
- Agent 2 produces browser context and privacy helpers that can enrich or
  redact candidate event metadata before JSONL writing.
- Agent 3 consumes JSONL `ActivityEvent` records and reuses existing classifier
  and reporting code.
- The coordinator is responsible for resolving any final imports, linter layer
  updates, and docs status updates after the three branches return.

## Merge Order

1. Merge Agent 1 first because it defines the core capture package and JSONL
   event writer.
2. Merge Agent 2 second because it can plug browser/redaction helpers into the
   capture boundary without changing replay behavior.
3. Merge Agent 3 last because it integrates replay and runtime commands across
   the files produced by the first two agents.

## Coordinator Checklist

- Confirm each branch only changes its owned files.
- Run `make verify` on each branch before integration.
- After all branches are merged locally, update `scripts/harness/lint.py` layer
  rules for any new product modules.
- Run `make harness-check`, `make harness-lint`, `make cleanup-check`,
  `make verify`, `make dev`, `make app-status`, and `make observe`.
- Update the relevant plan progress log with final verification evidence.

## Integration Notes

- The three work packages were implemented together in one branch.
- The fake-sensor fixture loop, manual macOS frontmost app/window adapter, and
  browser active-tab enrichment have shipped.
- The next product step is a short live session timeline built on top of the
  one-shot adapter.
- Replay artifacts are produced by `make dev` under `.harness/runtime/artifacts/`.
