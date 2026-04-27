# Quality Scorecard

Use this document to keep quality visible to future Codex runs.

## Current Score

| Area | Status | Notes |
| --- | --- | --- |
| Product definition | Green | IntentOS brief, behavior taxonomy, YouTube slice, and multi-app `ActivityEvent` foundation are specified. |
| Architecture | Yellow | Local-first Python CLI/UI stack, MVP boundaries, and capture adapter boundaries are documented and linted. |
| Verification | Green | `make verify` runs harness checks, harness linting, repository audit, unit tests, CLI smoke evaluation, capture replay, UI validation, and labeled fixture evaluation. |
| Security | Yellow | Local-only defaults, live-capture privacy rules, background timeline visibility, and manual macOS permission handling are documented; browser permission UX is pending. |
| Reliability | Yellow | CLI verification, UI validation, screenshot evidence, and artifact runtime exist; richer observability is pending. |
| UX | Yellow | A local UI shell exists for current reports with checked-in screenshot evidence; richer interaction design is pending. |

## Known Gaps

- Architecture lints cover the current Python layer map but need expansion as
  new layers appear.
- Browser screenshot evidence is checked in and guarded by a source manifest;
  richer DOM automation is still pending.
- Packaged always-on browser/app capture is not implemented; current live
  capture is limited to explicit manual commands and the visible `make dev`
  background timeline, with deterministic fixture coverage for replay/session
  behavior.
- Session timeline fixtures, merge tests, replay checks, and UI timeline
  validation are covered for the current bounded session slice.
- Classifier quality is only local-fixture-tested; real evaluation data is
  pending.
- Manual import is no longer the preferred user-facing path because it adds
  friction; keep any import work fixture-oriented unless product direction
  changes.
- Next-feature harness contracts now exist for automated sources, parser
  fixtures, daily narratives, fallback capture, local models, and richer UI
  automation; implementation of those slices is still pending.
- On-device model inference is specified but not implemented.

## Cleanup Process

When Codex finds repeated friction, stale docs, confusing structure, or missing
checks, it should update this scorecard and add a small follow-up plan or fix.
`make cleanup-check` runs both structural linting and the repository audit for
stale plans, stale docs, fixture drift, and quality scorecard gaps.
