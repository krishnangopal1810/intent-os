# Harness Audit

This document tracks how the IntentOS harness compares to the OpenAI Harness
Engineering model described in:

<https://openai.com/index/harness-engineering/>

## Status Summary

The harness now follows the repository-knowledge and planning model, and it
defines the executable app-legibility contract. It does not yet fully implement
application legibility, observability, architecture enforcement, or autonomous
PR loops because product code has not been created.

## Principle Coverage

| Principle | Status | IntentOS State |
| --- | --- | --- |
| Empty repo shaped by Codex | Green | Harness, docs, scripts, and CI were generated from an empty product repo. |
| Humans steer, agents execute | Green | Product intent lives in `docs/product/BRIEF.md`; Codex is expected to implement slices through plans. |
| Short `AGENTS.md` as map | Green | `AGENTS.md` is short and points to deeper docs. |
| Repository knowledge as system of record | Green | Product, architecture, quality, reliability, security, decisions, references, and plans live in `docs/`. |
| First-class execution plans | Green | Active and completed plan directories exist; first MVP plan is active. |
| Mechanical doc checks | Yellow | `harness-check` validates required files, active plan headings, and Markdown links. Freshness and ownership checks are not implemented yet. |
| App legibility | Yellow | `make dev` generates MVP artifacts and exposes the summary through local logs; UI validation awaits a UI. |
| Logs and observability legibility | Yellow | `make observe` exposes local runtime logs; metrics and traces are deferred until runtime complexity justifies them. |
| Architecture and taste enforcement | Red | Architecture principles exist, but no code or custom architecture lints exist yet. |
| Agent review and CI remediation loops | Yellow | Operating model exists; GitHub review automation is not yet wired into repo scripts. |
| Product verification gates | Green | `make verify` runs harness checks, unit tests, and fixture evaluation. CI runs `make verify`. |
| Recurring cleanup | Yellow | Quality scorecard and cleanup rules exist; no scheduled cleanup agent or CI task exists yet. |

## Current Intentional Failure

`make verify` now passes for the first YouTube classification slice. It runs
harness checks, product unit tests, and fixture-based CLI evaluation.

## Next Harness Upgrades

- Add architecture decision record.
- Add UI/browser validation if the first interface is graphical.
- Add structural architecture checks after the first code layout exists.
- Add a recurring doc/quality cleanup command once there is enough product
  surface area to drift.
