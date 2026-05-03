# Quality Scorecard

Use this document to keep quality visible to future Codex runs.

## Current Score

| Area | Status | Notes |
| --- | --- | --- |
| Product definition | Green | IntentOS brief, behavior taxonomy, YouTube slice, multi-app `ActivityEvent` foundation, and dogfood beta target are specified. |
| Architecture | Yellow | Local-first Python CLI/UI stack, beta service/SQLite boundaries, MVP boundaries, and capture adapter boundaries are documented and linted. |
| Verification | Green | `make verify` runs harness checks, harness linting, repository audit, unit tests, CLI smoke evaluation, capture replay, beta validation, UI validation, and labeled fixture evaluation. |
| Security | Yellow | Local-only defaults, live-capture privacy rules, beta SQLite retention, Chrome bridge filtering, background timeline visibility, and manual macOS permission handling are documented; permission actions now include local setup guidance. |
| Reliability | Yellow | CLI verification, beta API validation, UI validation, screenshot evidence, artifact runtime, local packaging, installed app smoke evidence, and a passing 30-minute native-recorder dogfood smoke exist; richer observability is pending. |
| UX | Yellow | The source beta is ready for trusted Mac friend testing with menu bar launch, service-backed daily review, correction controls, and permission setup guidance; public installer polish is still pending. |

## Known Gaps

- Architecture lints cover the current Python layer map but need expansion as
  new layers appear.
- Browser screenshot evidence is checked in and guarded by a source manifest;
  richer DOM automation is still pending.
- Dogfood beta packaging exists as a local ad-hoc signed menu bar app with
  install/open smoke evidence and target-specific setup guidance, but
  notarization and public distribution are out of scope.
- Fresh dogfood smoke evidence exists for native recorder row growth and pause
  privacy; the Chrome extension bridge still needs an installed-extension smoke
  that reaches connected or posting-events state.
- Browser/app capture for beta v1 is Chrome-first and metadata-only; richer
  cross-browser adapters are pending.
- Session timeline fixtures, merge tests, replay checks, and UI timeline
  validation are covered for the current bounded session slice.
- Classifier quality is only local-fixture-tested; real evaluation data is
  pending.
- Manual import is no longer the preferred user-facing path because it adds
  friction; keep any import work fixture-oriented unless product direction
  changes.
- Next-feature harness contracts now exist for automated sources, parser
  fixtures, daily narratives, fallback capture, local models, and richer UI
  automation; dogfood beta implements the first Chrome bridge slice, while
  richer narratives and model-backed inference are still pending.
- On-device model inference is specified but not implemented.

## Cleanup Process

When Codex finds repeated friction, stale docs, confusing structure, or missing
checks, it should update this scorecard and add a small follow-up plan or fix.
`make cleanup-check` runs both structural linting and the repository audit for
stale plans, stale docs, fixture drift, and quality scorecard gaps.
