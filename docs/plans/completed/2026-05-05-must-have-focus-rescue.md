# Execution Plan: must-have-focus-rescue

Date: 2026-05-05
Status: Completed

## Goal

Make IntentOS feel necessary to the priority beta user by turning the existing
daily intent contract into an in-day focus rescue loop: protect one named focus,
watch one named avoid pattern, surface a timely local recovery state, and end
the day with a specific proof-of-day receipt.

## Context

Product feedback says people do not feel they need this app. The current beta
is credible as a private attention audit, but a dashboard and evening review can
still feel optional. The sharper wedge is preventing a named daily commitment
from being lost to a named drift pattern while recovery is still possible.

This plan follows the harness-driven feedback policy: demand itself remains
manual to validate, but the repo should deterministically verify that the
focus-rescue loop exists, is visible, and produces inspectable service and UI
evidence.

## Scope

- Define a `focus_rescue` state derived from today's intent contract and
  captured activity.
- Extend the local beta API payloads so the dashboard and menu bar can show
  whether focus is protected, avoid is leaking, recovery is available, or
  evidence is insufficient.
- Add a small local recovery choice surface: return to focus, continue
  intentionally, pause capture, or correct the evidence.
- Add an evening proof-of-day receipt with protected focus time, avoid leakage,
  rescue moments, and correction impact.
- Update deterministic beta and UI validation to cover the new rescue state,
  empty state, long text, and receipt copy.
- Update trusted tester feedback prompts to ask whether the user would be upset
  if IntentOS stopped protecting the named focus next week.

## Non-Goals

- Public distribution, notarization, or installer polish.
- Cloud inference, cloud storage, telemetry, screenshots, keylogging, page
  bodies, cookies, or full conversation capture.
- Automatic blocking, scheduling, notifications, or workflow execution in this
  slice.
- Broad habit mechanics such as streaks, scores, social sharing, or gamified
  accountability.
- Chrome bridge recovery unless it directly improves the focus-rescue evidence
  for the current tester workflow.

## Acceptance Criteria

- The product brief and next-steps docs frame the next slice around protecting a
  named high-value focus from a named avoid pattern.
- `/api/daily-loop` or a related beta API exposes deterministic
  `focus_rescue` data for the current day, including state, reason, supporting
  evidence, and available local choices.
- The service persists enough local state to distinguish a rescue that was
  shown, accepted, continued intentionally, paused, or corrected.
- The dashboard makes the rescue state the first product moment and keeps
  generic analytics secondary.
- The menu bar exposes concise rescue status labels that match the service
  state.
- The evening review includes a proof-of-day receipt with protected focus time,
  avoid leakage, rescue moments, and correction impact.
- `make validate-beta` covers API payloads, persistence, and state transitions
  with deterministic fixtures or fakes.
- `make validate-ui` covers rendered rescue status, empty state, receipt copy,
  and long-text wrapping.
- `make update-ui-screenshot` refreshes visual evidence if UI source, fixtures,
  or report output change.
- Trusted tester feedback is recorded in docs or fixtures when it changes
  product assumptions.

## Harness Impact

- Runtime commands and artifacts: `make beta-dev`, `make beta-status`,
  `make validate-beta`, `make validate-ui`, and beta daily-loop artifacts should
  expose focus-rescue state.
- Fixtures or fakes required for deterministic `make verify`: add or update
  beta fixture scenarios for focus protected, avoid leaking, recovery
  available, no intent set, and insufficient evidence.
- UI validation or screenshot evidence: update rendered UI probes and screenshot
  evidence when the rescue surface changes the dashboard.
- Structured logs, metrics, or diagnostics: record rescue state transitions in
  beta diagnostics without persisting sensitive page bodies or raw text.
- Privacy, permission, or local-only constraints: keep all rescue inference
  local, metadata-first, and compatible with pause/resume/delete-local-data.
- Docs or harness checks to update: product brief, next steps, trusted tester
  handoff, visible-copy policy, beta validation, and UI validation.

## Verification

- `python3 -m unittest discover -s tests`
- `make harness-check`
- `make harness-lint`
- `make validate-beta`
- `make validate-ui`
- `make verify`

## Implementation Notes

- The rescue state should be conservative. If evidence is sparse or
  contradictory, show evidence insufficient rather than making a dramatic claim.
- Treat "continue intentionally" as a valid user choice, not a failure. The
  product should protect agency, not shame the user.
- The first implementation can derive rescue state from deterministic
  intent-contract signals already generated for focus and avoid inputs.
- Demand validation remains manual: the deterministic proxy is whether the
  product presents the rescue loop clearly enough for testers to answer whether
  they would miss it.

## Progress Log

- 2026-05-05: Plan created.
- 2026-05-05: Product direction updated from attention audit/testing readiness
  toward a must-have focus-rescue wedge.
- 2026-05-05: Implemented `focus_rescue` in the daily-loop payload, local
  rescue action persistence, `POST /api/focus-rescue-action`, dashboard action
  controls, menu bar rescue labels, beta validation, rendered UI probes, and
  unit coverage.
- 2026-05-05: `make validate-beta`, `make validate-ui`, and
  `make update-ui-screenshot` passed.
- 2026-05-06: Split focus rescue helpers out of `loop_coach.py`, split service
  utilities out of `service.py`, added local activation diagnostics for first
  intent, first rescue state, first recovery choice, and completed review, and
  extended beta validation coverage.
- 2026-05-06: `python3 -m unittest discover -s tests`, `make harness-check`,
  `make harness-lint`, `make validate-beta`, `make validate-ui`, and
  `make verify` passed.

## Handoff Notes

Completed. Demand validation remains manual: the next slice should put the
source beta in front of trusted testers and record whether they would miss the
protected-focus loop next week.
