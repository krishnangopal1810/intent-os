# Harness Audit

This document tracks how the IntentOS harness compares to the OpenAI Harness
Engineering model described in:

<https://openai.com/index/harness-engineering/>

## Status Summary

The harness now supports an agent-first local product loop: repository-local
knowledge, execution plans, structural linting, product verification, runtime
artifacts, PR workflow, CI, documented live-capture/privacy contracts, a
deterministic fake-sensor replay loop, a local app shell for the UI,
deterministic UI validation, checked-in screenshot evidence, structured runtime
JSONL events, `make diagnose`, and a manual macOS metadata-only frontmost
app/window adapter with best-effort browser tab enrichment plus bounded session
timeline capture. It also defines next-feature harness contracts for imports,
daily narratives, fallback capture, local models, and richer UI automation. It
does not yet include rich DOM automation, rich
metrics/traces, always-on session capture, or autonomous agent-to-agent review.

## Self-Sufficiency Verdict

The harness is self-sufficient for the product surface shipped so far:
fixture-backed classification, fake capture replay, one-shot manual live
macOS/browser metadata capture, bounded live session timeline capture, local UI
inspection, optional headless browser render diagnostics, screenshot evidence,
CI, PR review, and merge workflows all have repository-local commands and docs.

The harness now names the required support for later ScreenCaptureKit/OCR,
local-model, import, narrative, and UI automation work in
`docs/HARNESS_FEATURES.md`. Those slices must still add their actual fake
adapters, fixtures, privacy gates, product commands, metrics/traces where
justified, and stricter architecture lint rules as they are implemented.

## Principle Coverage

| Principle | Status | IntentOS State |
| --- | --- | --- |
| Empty repo shaped by Codex | Green | Harness, docs, scripts, and CI were generated from an empty product repo. |
| Humans steer, agents execute | Green | Product intent lives in `docs/product/BRIEF.md`; Codex is expected to implement slices through plans. |
| Short `AGENTS.md` as map | Green | `AGENTS.md` is short and points to deeper docs. |
| Repository knowledge as system of record | Green | Product, architecture, quality, reliability, security, decisions, references, and plans live in `docs/`. |
| First-class execution plans | Green | Active, completed, and parallel plan directories exist; completed plans document the YouTube MVP, multi-app ActivityEvent foundation, live capture, UI shell, and session timeline. |
| Mechanical doc checks | Green | `harness-check` validates required files, active plan headings, and Markdown links; `harness-lint` checks active-plan hygiene, quality scorecard structure, and next-feature harness contracts. |
| App legibility | Green | `make dev` generates fixture-backed MVP and session timeline artifacts, serves the local UI shell, starts the visible background metadata sampler, and records the URL, data mode, capture mode, capture PID, status path, and log path in `.harness/runtime/app.env`; `make dev-live` is the explicit capture-then-serve path for fresh bounded macOS session data; `make validate-ui` checks the shell against local artifacts with optional headless browser screenshot and DOM-probe diagnostics; checked-in screenshot evidence is guarded by a source manifest. |
| Logs and observability legibility | Yellow | `make observe` exposes structured runtime events and app logs; `make diagnose` summarizes app state, validation evidence, and logs. Rich metrics and traces are deferred until runtime complexity justifies them. |
| Architecture and taste enforcement | Yellow | `harness-lint` enforces the current Python layer map, import boundaries, file-size limit, generated-file hygiene, and evaluation fixture coverage. |
| Capture/privacy policy enforcement | Yellow | `harness-lint` checks that live-capture, on-device inference, and security docs preserve metadata-first capture, no-keylogging, local-only, and screenshot fallback policies. Manual macOS, browser active-tab, and session merge paths have deterministic fixture tests. |
| Multi-agent coordination | Yellow | A parallel macOS live-capture package defines a shared tracker, three disjoint task files, merge order, and harness ownership checks. |
| Agent review and CI remediation loops | Yellow | Operating model exists; GitHub review automation is not yet wired into repo scripts. |
| Product verification gates | Green | `make verify` runs harness checks, harness linting, repository audit, unit tests, YouTube evaluation, generic activity CLI smoke evaluation, capture replay, and UI validation. CI runs `make verify`. |
| Recurring cleanup | Yellow | `make cleanup-check` catches several drift classes; no scheduled cleanup agent exists yet. |

## Current Verification State

`make verify` passes for the current product surface. It runs harness checks,
structural/taste linting, product unit tests, YouTube CLI and evaluation checks,
multi-app ActivityEvent CLI and evaluation checks, fake capture replay checks,
session timeline replay checks, UI validation, and cleanup-sensitive structural
checks.

The harness also requires live-capture and on-device inference docs so future
macOS sensor work starts from the privacy and architecture contract. It
validates the macOS live-capture parallel package so three Codex agents can work
from explicit ownership boundaries.

Manual live validation is intentionally separate from CI:

```sh
make dev-live
make observe-live
make observe-session
```

These commands write live capture diagnostics and replay evidence under
`.harness/runtime/`, but they may require local Accessibility and Automation
permissions.

## Next Harness Upgrades

- Expand browser automation in `make validate-ui` when the UI becomes
  interactive enough to require click, filter, and navigation checks.
- Keep `docs/HARNESS_FEATURES.md` current as manual import, browser history,
  ChatGPT export, narrative, ScreenCaptureKit/OCR, and local model slices land.
- Keep deterministic capture fixtures for each real adapter. CI must exercise
  parser, normalization, privacy exclusion, and replay behavior without reading
  live user state.
- Extend structured runtime events as new capture, classification, reporting,
  and UI workflows are added.
- Keep `make observe-live` as the manual live sensor diagnostic and expand it
  as browser metadata adapters are added.
- Expand architecture lints as the codebase gains layers, especially
  source-adapter -> event-boundary -> classifier -> reporting direction.
- Keep expanding cleanup/audit scripts so stale plans, stale docs, fixture
  drift, and quality scorecard gaps stay mechanically visible as the repo grows.
