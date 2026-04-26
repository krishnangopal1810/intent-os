# Harness Audit

This document tracks how the IntentOS harness compares to the OpenAI Harness
Engineering model described in:

<https://openai.com/index/harness-engineering/>

## Status Summary

The harness now supports an agent-first local product loop: repository-local
knowledge, execution plans, structural linting, product verification, runtime
artifacts, PR workflow, CI, documented live-capture/privacy contracts, a
deterministic fake-sensor replay loop, a local app shell for the UI,
deterministic UI validation, structured runtime JSONL events, `make diagnose`,
and a manual macOS metadata-only frontmost app/window adapter with best-effort
browser tab enrichment. It does not yet include browser screenshot automation,
rich metrics/traces, continuous session capture, or autonomous agent-to-agent
review.

## Principle Coverage

| Principle | Status | IntentOS State |
| --- | --- | --- |
| Empty repo shaped by Codex | Green | Harness, docs, scripts, and CI were generated from an empty product repo. |
| Humans steer, agents execute | Green | Product intent lives in `docs/product/BRIEF.md`; Codex is expected to implement slices through plans. |
| Short `AGENTS.md` as map | Green | `AGENTS.md` is short and points to deeper docs. |
| Repository knowledge as system of record | Green | Product, architecture, quality, reliability, security, decisions, references, and plans live in `docs/`. |
| First-class execution plans | Green | Active, completed, and parallel plan directories exist; completed plans document the YouTube MVP and multi-app ActivityEvent foundation. |
| Mechanical doc checks | Green | `harness-check` validates required files, active plan headings, and Markdown links; `harness-lint` checks active-plan hygiene and quality scorecard structure. |
| App legibility | Green | `make dev` generates MVP artifacts, serves the local UI shell, records the URL in `.harness/runtime/app.env`, and `make validate-ui` checks the shell against local artifacts. |
| Logs and observability legibility | Yellow | `make observe` exposes structured runtime events and app logs; `make diagnose` summarizes app state, validation evidence, and logs. Rich metrics and traces are deferred until runtime complexity justifies them. |
| Architecture and taste enforcement | Yellow | `harness-lint` enforces the current Python layer map, import boundaries, file-size limit, generated-file hygiene, and evaluation fixture coverage. |
| Capture/privacy policy enforcement | Yellow | `harness-lint` checks that live-capture, on-device inference, and security docs preserve metadata-first capture, no-keylogging, local-only, and screenshot fallback policies. Manual macOS capture has deterministic fixture tests. |
| Multi-agent coordination | Yellow | A parallel macOS live-capture package defines a shared tracker, three disjoint task files, merge order, and harness ownership checks. |
| Agent review and CI remediation loops | Yellow | Operating model exists; GitHub review automation is not yet wired into repo scripts. |
| Product verification gates | Green | `make verify` runs harness checks, harness linting, repository audit, unit tests, YouTube evaluation, generic activity CLI smoke evaluation, capture replay, and UI validation. CI runs `make verify`. |
| Recurring cleanup | Yellow | `make cleanup-check` catches several drift classes; no scheduled cleanup agent exists yet. |

## Current Verification State

`make verify` passes for the current product surface. It runs harness checks,
structural/taste linting, product unit tests, YouTube CLI and evaluation checks,
multi-app ActivityEvent CLI and evaluation checks, fake capture replay checks,
and cleanup-sensitive structural checks.

The harness also requires live-capture and on-device inference docs so future
macOS sensor work starts from the privacy and architecture contract. It
validates the macOS live-capture parallel package so three Codex agents can work
from explicit ownership boundaries.

Manual live validation is intentionally separate from CI:

```sh
make observe-live
```

This command writes live capture diagnostics and replay evidence under
`.harness/runtime/`, but it may require local Accessibility and Automation
permissions.

## Next Harness Upgrades

- Add browser screenshot and DOM automation to `make validate-ui` once the repo
  introduces a browser automation dependency.
- Keep deterministic capture fixtures for each real adapter. CI must exercise
  parser, normalization, privacy exclusion, and replay behavior without reading
  live user state.
- Extend structured runtime events as new capture, classification, reporting,
  and UI workflows are added.
- Keep `make observe-live` as the manual live sensor diagnostic and expand it
  as browser metadata adapters are added.
- Expand architecture lints as the codebase gains layers, especially
  source-adapter -> event-boundary -> classifier -> reporting direction.
- Expand cleanup/audit scripts so stale plans, stale docs, fixture drift, and
  quality scorecard gaps are detected mechanically.
