# Design

IntentOS UI shell is the local interface for daily behavior review. It is
intentionally product-first: the first screen is a compact review board with a
daily verdict, next move, action queue, current behavior summary, activity
breakdown, capture replay evidence, and local runtime artifact status. Legacy
domain-specific summaries must stay out of the primary navigation.

## UX Principles

- Start with the real product workflow, not a marketing page.
- Keep the first screen useful for the target user.
- Favor dense, native-app review surfaces over oversized dashboard cards.
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

## Current UI Shell

- Source files live in `web/`.
- The first viewport should answer what to repeat, what leaked attention, what
  needs trust/correction review, and what to do next.
- The action surface should read as an operating queue, not a marketing card
  grid.
- `scripts/product/dev.sh` copies the shell to `.harness/runtime/site/` and
  writes JSON report artifacts.
- `make dev` serves the shell at the URL recorded in
  `.harness/runtime/app.env`.
- `make validate-ui` builds the shell, starts a temporary local server, fetches
  the page and JSON artifacts, writes
  `.harness/runtime/artifacts/ui-validation.txt`, and, when Chrome or Chromium
  exists locally, captures rendered desktop and mobile browser evidence under
  `.harness/runtime/artifacts/ui-render*`.
- `docs/assets/screenshots/intent-os-ui.png` is the checked-in visual baseline
  for the current fixture-backed UI.

## Design System Notes

The local shell follows macOS utility-app conventions: split-view navigation,
SF system typography, restrained light materials, 8px cards, compact status
badges, and behavior-color dots that match the timeline and breakdown.
