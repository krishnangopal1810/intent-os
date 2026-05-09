# Next Steps

This file is the short roadmap. Completed implementation detail belongs in
`docs/plans/completed/`; active work belongs in `docs/plans/active/`.

## Current Product Bet

IntentOS should keep sharpening the trusted Mac beta around one promise:
protect a named focus from a named avoid pattern while recovery is still
possible. The bundled app path, first-run stepper, local beta service, daily
intent loop, focus rescue state, and evening receipt are the current product
center.

## Recommended Slices

1. Trusted cohort evidence: run the bundled `IntentOS-trusted-beta.zip` with a
   small Mac cohort and record setup time, first live state, repeated feedback,
   retention, and would-miss signals through the cohort evidence template.
2. Browser extension capture: keep Chrome bridge detail optional, then improve
   the installed-extension smoke until it reliably reaches connected or
   posting-events state without fake rows.
3. Calendar or planned-intent integration: use only local deterministic
   fixtures at first, and require a `HARNESS_FEATURES.md` class plan before
   adding any new permissioned source.
4. Accessibility visible-text excerpts: treat this as a metadata-first
   enrichment with strict bounding, redaction, and fixture coverage before any
   broader capture.
5. ScreenCaptureKit and Vision fallback: keep ScreenCaptureKit/OCR out of the
   default path; only add it as an explicit low-confidence fallback with no raw
   screenshot retention.
6. Local model second-pass classifier: add a local model boundary only after
   deterministic rules and labeled fixtures show a concrete classification gap.

## Guardrails

- The Automated background timeline and native recorder remain the primary
  beta capture paths.
- Manual imports are fixture/parser infrastructure, not the preferred
  user-facing activation path.
- Every product-feedback change must name or add the harness check that would
  catch the regression next time.
- Run `make chrome-bridge-smoke` before claiming the installed bridge is ready
  for tester setup.

## Harness Upgrades To Keep Current

`make cleanup-check` should continue catching stale plans, fixture drift, and
quality scorecard gaps before they become chat-only context. Run
`make harness-check`, `make harness-lint`, `make cleanup-check`, and
`make verify` before merging roadmap work.
