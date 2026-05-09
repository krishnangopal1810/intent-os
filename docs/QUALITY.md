# Quality Scorecard

Use this document to keep quality visible to future Codex runs.

## Current Score

| Area | Status | Notes |
| --- | --- | --- |
| Product definition | Yellow | IntentOS brief, behavior taxonomy, YouTube slice, multi-app `ActivityEvent` foundation, dogfood beta target, and must-have focus-rescue wedge are specified; real demand validation is still pending. |
| Architecture | Yellow | Local-first Python CLI/UI stack, beta service/SQLite boundaries, MVP boundaries, and capture adapter boundaries are documented and linted. |
| Verification | Green | `make verify` runs harness checks, harness linting, repository audit, unit tests, CLI smoke evaluation, capture replay, beta validation, UI validation, package contract checks, cohort evidence checks, and labeled fixture evaluation. |
| Security | Yellow | Local-only defaults, live-capture privacy rules, beta SQLite retention, Chrome bridge filtering, background timeline visibility, guided first-run permission handling, and redacted setup reports are documented. |
| Reliability | Yellow | CLI verification, beta API validation, UI validation, screenshot evidence, artifact runtime, bundled trusted-tester packaging, package contract checks, installed app smoke evidence, adapter fixture manifest checks, JSON diagnostics, cohort evidence scaffolding, and a passing 30-minute native-recorder dogfood smoke exist; richer observability is pending. |
| UX | Yellow | The beta now has guided first run, stable IntentOS app identity, capture preview, setup report, menu bar launch, daily intent coach hero, focus rescue state/actions, correction controls, and desktop/mobile UI validation; public notarized installer polish is still pending. |

## Harness-Driven Feedback Policy

Product feedback is a quality input. When feedback changes behavior, copy,
layout, setup guidance, classification, privacy expectations, or runtime
resilience, the related work must update the harness or name the existing check
that already covers it. Follow
[HARNESS_DRIVEN_DEVELOPMENT.md](HARNESS_DRIVEN_DEVELOPMENT.md) before closing
feedback-driven work.

Use this scorecard to record only the exceptions: feedback that cannot yet be
checked deterministically, why it remains manual, and what proxy harness check
exists until the gap is closed.

## Known Gaps

- Demand validation is intentionally manual for now: the harness can verify the
  focus-rescue loop exists, but it cannot prove users want it badly. The proxy
  checks are the completed focus-rescue plan, `make validate-beta`,
  `make validate-ui`, `make cohort-evidence-check`, and recorded trusted-tester
  answers to whether they would be upset if IntentOS stopped protecting their
  named focus. The cohort evidence template requires every repeated feedback
  theme to map to a fixture, UI probe, validation scenario, quality note, or
  manual exception. When cohort results are present, the check enforces the
  current demand targets instead of treating demand evidence as advisory.
- Architecture lints cover the current Python layer map, unregistered
  `intentos/` and `tests/` modules, split dashboard script sizes, and the beta
  validation wrapper/module boundary; new runtime layers still need explicit
  entries when they appear.
- Browser screenshot evidence is checked in and guarded by a source manifest;
  rendered desktop/mobile DOM probes now cover decision cards, next move text,
  visible-copy policy, overflow, cut-off or clipped text, first-screen density
  budgets, plan-vs-actual hero presence, inline receipt presence, weekly
  disclosure presence, Activity navigation disclosure, long-text wrapping,
  service-stale recovery, empty beta state, missing-intent preview, setup
  guidance, and capture events; richer end-to-end UI workflows are still
  pending.
- Trusted beta packaging now emits a bundled `IntentOS-trusted-beta.zip` with
  stable app identity, guided first run, deterministic stale-dashboard menu
  guards, and a macOS CI artifact upload path; notarization, auto-update, and
  public distribution are still out of scope.
- Daily intent coach state is local and deterministic; richer habit mechanics
  such as notifications, calendar planning, blocking, and streaks remain out of
  scope.
- Fresh dogfood smoke evidence exists for native recorder row growth and pause
  privacy; the Chrome extension bridge still needs an installed-extension smoke
  that reaches connected or posting-events state.
- `make chrome-bridge-smoke` records installed Chrome bridge smoke evidence
  without fake bridge rows, but the fresh 2026-05-03 dogfood-machine run was
  blocked because the installed bridge never reached `connected` or
  `posting_events`; native recorder stayed healthy and remains the primary
  beta path.
- The adapter fixture manifest covers the current capture fixtures and replay
  path; future adapters must add manifest entries before completion.
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
