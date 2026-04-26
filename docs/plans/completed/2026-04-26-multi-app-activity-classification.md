# Execution Plan: multi-app-activity-classification

Date: 2026-04-26
Status: Completed

## Goal

Generalize IntentOS from YouTube-only classification to multi-app
`ActivityEvent` behavior classification without adding live capture.

## Context

IntentOS needs to understand behavior across surfaces such as YouTube,
LinkedIn, Twitter/X, Instagram, WhatsApp, ChatGPT, coding tools, and admin
websites. The next product layer should establish the shared taxonomy, event
shape, classifier, report output, and evaluation harness before adding sensors.

## Scope

- Add a durable product taxonomy.
- Add a generic `ActivityEvent` model and boundary validation.
- Add a multi-app classifier that can label activity across behavior categories.
- Preserve the existing YouTube MVP path.
- Add a multi-app fixture evaluation set.
- Add report output for aggregate behavior time and item-level reasons.
- Add architecture checks for the new layer map.
- Wire the new evaluation into `make verify`.

## Non-Goals

- Live capture from browsers, macOS APIs, or app APIs.
- Browser extension work.
- UI/browser automation.
- Cloud inference or cloud storage.
- Agentic blocking, scheduling, or workflow execution.

## Acceptance Criteria

- `make verify` passes.
- A local multi-app fixture set includes ChatGPT, coding, communication, admin
  work, social scrolling, YouTube learning, and entertainment examples.
- Each event is classified with label, confidence, and reason.
- The report includes aggregate duration by behavior label.
- Unknown/ambiguous events remain visible.
- Architecture linting enforces the new layer map.

## Verification

- `make verify`
- `python3 -m intentos.activity_cli data/activity/multi_app_events.json`
- `python3 -m intentos.activity_evaluate data/activity/evaluation_set.json --min-accuracy 85`

## Implementation Notes

- Keep the implementation deterministic and inspectable.
- Use fixtures before live capture to stabilize the taxonomy and evaluation
  loop.
- Do not replace the YouTube MVP CLI; add generic activity behavior alongside
  it.

## Progress Log

- 2026-04-26: Plan created.
- 2026-04-26: Added product taxonomy and domain specs.
- 2026-04-26: Added generic `ActivityEvent` model, classifier, reporting CLI,
  multi-app fixtures, evaluation runner, tests, and architecture lint rules.
- 2026-04-26: `make verify` passed.

## Handoff Notes

Completed as a fixture-based local CLI slice. Live capture remains out of scope;
future work should add adapters after the generic classifier and evaluation
loop receive more real-world examples.
