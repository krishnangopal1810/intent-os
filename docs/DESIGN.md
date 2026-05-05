# Design

IntentOS UI shell is the local interface for daily intent accountability and
daily behavior review. It is
intentionally product-first: the first screen is a compact coach board with a
plan-vs-actual verdict, daily intent contract, one next block, correction
reward, and local runtime status. Metrics, focus queues, activity breakdown,
weekly patterns, and capture replay evidence remain available through
disclosures, but secondary to the default action flow. Legacy domain-specific
summaries must stay out of the primary navigation.

## UX Principles

- Start with the real product workflow, not a marketing page.
- Keep the first screen useful for the target user.
- Favor progressive disclosure over dense dashboards: the default screen should
  show the next action first, then let the user open supporting evidence.
- Prefer clear controls, predictable navigation, and visible system state.
- Make empty, loading, error, and success states explicit.
- Avoid decorative UI that does not help the user complete the workflow.
- Make new product capabilities visible in the UI as soon as they can produce a
  deterministic local artifact.

## Visual Quality Bar

- Layouts must work on mobile and desktop.
- Text must fit within its containers.
- Interactive controls must have obvious affordances and focus states.
- UI changes should be verified visually when the product has a frontend.
- UI changes must pass `make validate-ui`.
- UI source, fixture, or report-output changes must refresh the checked-in
  screenshot with `make update-ui-screenshot`.
- Manual product feedback should become a copy, density, navigation, workflow,
  or scenario guardrail in the local UI harness when it can be checked
  deterministically.

## Current UI Shell

- Source files live in `web/`.
- The first viewport should answer whether the day matched the plan, which
  focus and avoid signals were matched, what IntentOS learned, and what to do
  in the next block.
- The first viewport should include a compact command center that separates
  "Now", "Trust", and "Tonight" so the user can act before inspecting the full
  report.
- Section navigation should remain visible while the review content scrolls;
  Review, Decisions, Timeline, and Activity are app tabs, not page links that
  strand the user away from navigation.
- The daily plan module should ask for one focus and one thing to avoid, show
  how tonight's review will compare that plan to captured behavior, then show
  the evening plan-vs-actual review when enough local signal exists.
- First-run setup should be a guided stepper, not a broad checklist: Privacy,
  App access, Capture check, Daily focus, and First block, with browser detail
  clearly optional after capture works.
- Internal beta, dogfood, sticky-loop, recorder, bridge, database, and harness
  terms should not appear as primary dashboard language.
- Service or data loading problems should appear as a plain-language notice at
  the top of the review board, with recovery guidance instead of raw fetch,
  "No rows", or local-service developer wording.
- The action surface should read as one next-block recommendation, not a full
  analytics dashboard. Keep the default first viewport capped to one visible
  decision card, with metrics, weekly patterns, focus queues, and raw evidence
  behind expandable supporting-detail rows.
- `scripts/product/dev.sh` copies the shell to `.harness/runtime/site/` and
  writes JSON report artifacts.
- `make dev` serves the shell at the URL recorded in
  `.harness/runtime/app.env`.
- `make validate-ui` builds the shell, starts a temporary local server, fetches
  the page and JSON artifacts, writes
  `.harness/runtime/artifacts/ui-validation.txt`, and, when Chrome or Chromium
  exists locally, captures rendered desktop and mobile browser evidence under
  `.harness/runtime/artifacts/ui-render*`. The shared render probe enforces the
  visible-copy policy, first-viewport density budget, long-text wrapping,
  Activity navigation behavior, service reconnect copy, and daily-intent
  preview updates.
- `docs/assets/screenshots/intent-os-ui.png` is the checked-in visual baseline
  for the current fixture-backed UI.

## Design System Notes

The local shell follows macOS utility-app conventions: split-view navigation,
SF system typography, restrained light materials, 8px cards, compact status
badges, and behavior-color dots that match the timeline and breakdown.
