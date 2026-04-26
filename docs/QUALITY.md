# Quality Scorecard

Use this document to keep quality visible to future Codex runs.

## Current Score

| Area | Status | Notes |
| --- | --- | --- |
| Product definition | Green | IntentOS brief and Week 1 YouTube MVP are specified. |
| Architecture | Yellow | Local-first Python CLI stack and MVP boundaries are documented. |
| Verification | Green | `make verify` runs harness checks, unit tests, and fixture evaluation. |
| Security | Yellow | MVP is local-only; real user data capture policy is still pending. |
| Reliability | Yellow | CLI verification and artifact runtime exist; UI and richer observability are pending. |
| UX | Yellow | Week 1 YouTube classification workflow specified; UI not designed yet. |

## Known Gaps

- Architecture lints do not exist yet.
- Browser validation is specified but not implemented because no UI exists.
- Live YouTube capture is not implemented.
- Classifier quality is only fixture-tested; real evaluation data is pending.

## Cleanup Process

When Codex finds repeated friction, stale docs, confusing structure, or missing
checks, it should update this scorecard and add a small follow-up plan or fix.
