# Domain Spec: Multi-App Activity

## Status

Draft for fixture-based classification.

## Goal

Classify normalized activity from multiple apps and websites into the IntentOS
behavior taxonomy.

## Inputs

Local fixture data only for this slice. Each event should include:

- `source_app`
- `surface`
- `title`
- `started_at`
- `duration_seconds`
- optional `url`
- optional `metadata`
- optional `expected_label` for evaluation fixtures

## Outputs

- Per-event behavior label, confidence, and reason.
- Aggregate duration by label.
- A daily narrative suitable for CLI output.

## Non-Goals

- Live app capture.
- Browser history import.
- Screen recording.
- Cloud inference.

## Acceptance Criteria

- Multi-app fixtures cover work, communication, admin, learning, passive
  consumption, entertainment, and unknown.
- Evaluation runs locally and is wired into `make verify`.
- The existing YouTube MVP remains working.
