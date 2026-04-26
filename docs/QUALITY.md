# Quality Scorecard

Use this document to keep quality visible to future Codex runs.

## Current Score

| Area | Status | Notes |
| --- | --- | --- |
| Product definition | Green | IntentOS brief and Week 1 YouTube MVP are specified. |
| Architecture | Red | Stack and boundaries not selected yet. |
| Verification | Yellow | Harness checks exist; product checks must fail until product runtime exists. |
| Security | Yellow | Baseline exists; product model pending. |
| Reliability | Yellow | Baseline exists; runtime pending. |
| UX | Yellow | Week 1 YouTube classification workflow specified; UI not designed yet. |

## Known Gaps

- Architecture needs stack choice after product requirements are known.
- Product tests cannot exist until product code exists.
- Runtime harness commands exist, but no product runtime has been wired yet.
- Browser validation is specified but not implemented because no UI exists.

## Cleanup Process

When Codex finds repeated friction, stale docs, confusing structure, or missing
checks, it should update this scorecard and add a small follow-up plan or fix.
