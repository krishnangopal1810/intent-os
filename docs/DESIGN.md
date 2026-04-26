# Design

IntentOS UI shell is the local interface for daily behavior review. It is
intentionally product-first: the first screen shows the current behavior
summary, activity breakdown, capture replay evidence, and YouTube MVP summary
from local runtime artifacts.

## UX Principles

- Start with the real product workflow, not a marketing page.
- Keep the first screen useful for the target user.
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
- UI changes must pass `make validate-ui`; browser screenshots should be added
  once a browser automation dependency is introduced.

## Current UI Shell

- Source files live in `web/`.
- `scripts/product/dev.sh` copies the shell to `.harness/runtime/site/` and
  writes JSON report artifacts.
- `make dev` serves the shell at the URL recorded in
  `.harness/runtime/app.env`.
- `make validate-ui` builds the shell, starts a temporary local server, fetches
  the page and JSON artifacts, and writes
  `.harness/runtime/artifacts/ui-validation.txt`.

## Future Design System Notes

Record product-specific typography, color, spacing, component, and accessibility
rules here once the product direction is known.
