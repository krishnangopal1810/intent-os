# Quality Scorecard

Use this document to keep quality visible to future Codex runs.

## Current Score

| Area | Status | Notes |
| --- | --- | --- |
| Product definition | Green | IntentOS brief, behavior taxonomy, YouTube slice, and multi-app `ActivityEvent` foundation are specified. |
| Architecture | Yellow | Local-first Python CLI stack, MVP boundaries, and future capture adapter boundaries are documented and linted. |
| Verification | Green | `make verify` runs harness checks, harness linting, unit tests, CLI smoke evaluation, and labeled fixture evaluation. |
| Security | Yellow | Local-only defaults and live-capture privacy rules are documented; implementation and permission UX are pending. |
| Reliability | Yellow | CLI verification and artifact runtime exist; UI and richer observability are pending. |
| UX | Yellow | CLI reports exist for YouTube and multi-app fixtures; UI is not designed yet. |

## Known Gaps

- Architecture lints cover the current Python layer map but need expansion as
  new layers appear.
- Browser validation is specified but not implemented because no UI exists.
- Live multi-app capture is not implemented.
- Classifier quality is only local-fixture-tested; real evaluation data is
  pending.
- No manual import path exists yet for real user activity.
- On-device model inference is specified but not implemented.

## Cleanup Process

When Codex finds repeated friction, stale docs, confusing structure, or missing
checks, it should update this scorecard and add a small follow-up plan or fix.
