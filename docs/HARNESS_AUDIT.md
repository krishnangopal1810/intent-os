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
| App legibility | Yellow | Commands and contracts exist in `docs/APP_RUNTIME.md`; real launch/UI validation awaits product code. |
| Logs and observability legibility | Yellow | `make observe` exists for local logs; metrics and traces are deferred until runtime complexity justifies them. |
| Architecture and taste enforcement | Red | Architecture principles exist, but no code or custom architecture lints exist yet. |
| Agent review and CI remediation loops | Yellow | Operating model exists; GitHub review automation is not yet wired into repo scripts. |
| Product verification gates | Yellow | `make verify` now fails once a product is specified without checks. CI runs harness checks until product tests exist. |
| Recurring cleanup | Yellow | Quality scorecard and cleanup rules exist; no scheduled cleanup agent or CI task exists yet. |

## Current Intentional Failure

`make verify` currently fails because IntentOS has a real product brief but no
product implementation or product verification path. That failure is expected
until the first MVP execution plan adds product code and tests. CI currently
runs `make harness-check` so the initial harness PR remains mergeable.

## Next Harness Upgrades

- Add product stack and architecture decision record.
- Add `scripts/product/dev.sh` and `scripts/product/verify.sh`.
- Add product tests and sample fixtures.
- Add UI/browser validation if the first interface is graphical.
- Add structural architecture checks after the first code layout exists.
- Add a recurring doc/quality cleanup command once there is enough product
  surface area to drift.
