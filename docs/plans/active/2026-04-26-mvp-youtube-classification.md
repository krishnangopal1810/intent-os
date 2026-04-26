# Execution Plan: mvp-youtube-classification

Date: 2026-04-26
Status: Active

## Goal

Build the first complete IntentOS product slice: local YouTube activity
classification into learning, entertainment, or unknown, with aggregate time
insights and an executable verification path.

## Context

IntentOS is a personal behavior intelligence system. The Week 1 MVP focuses on
YouTube because it contains both high-value learning and passive consumption,
and app-level time tracking cannot distinguish those behaviors.

Relevant docs:

- `docs/product/BRIEF.md`
- `docs/product/mvp-youtube-classification.md`
- `docs/APP_RUNTIME.md`
- `docs/SECURITY.md`

## Scope

- Choose a small local-first product stack.
- Add deterministic sample YouTube activity fixtures.
- Implement ingestion for local sample activity data.
- Implement classification into `learning`, `entertainment`, or `unknown`.
- Include confidence and a short reason per item.
- Implement aggregation of total watched time and percentage split.
- Provide an interface suitable for the first slice, such as CLI output or a
  minimal local UI.
- Wire product checks into `make verify`.
- Wire runtime commands into the harness if the slice includes a UI.
- Update architecture, reliability, security, and quality docs with actual
  decisions.

## Non-Goals

- Live browser history capture.
- Browser extension distribution.
- Cloud inference or cloud storage.
- Full macOS activity tracking.
- Blocking, scheduling, or automated behavior changes.

## Acceptance Criteria

- Runs locally from a fresh checkout.
- `make verify` passes after implementation.
- A sample input produces per-video classifications with label, confidence, and
  reason.
- Output includes total YouTube time, learning percentage, entertainment or
  passive consumption percentage, and unknown percentage when applicable.
- The default path keeps data local.
- The result includes language close to: "You spent 2h on YouTube. 68% was
  passive consumption."

## Verification

- `make verify`
- Product-specific unit tests for classification and aggregation.
- Fixture-based evaluation over sample YouTube activity.
- Runtime validation evidence if a UI is added.

## Implementation Notes

- Prefer deterministic, inspectable rules or a local model abstraction for the
  first version. Do not require cloud inference for the default path.
- Preserve uncertainty. Use `unknown` rather than forcing a label when metadata
  is insufficient.
- Keep the first slice narrow but complete enough for Codex to test end to end.

## Progress Log

- 2026-04-26: Plan created.
- 2026-04-26: Product brief, MVP spec, and harness requirements captured.

## Handoff Notes

Product implementation has not started. `make verify` is expected to fail until
this plan adds a product verification path.
