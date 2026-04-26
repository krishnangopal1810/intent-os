# MVP Spec: YouTube Classification

## Status

Implemented for the first local fixture-based CLI slice.

## Goal

Build the first IntentOS slice: classify watched YouTube time as learning or
entertainment and summarize the result in language that feels behaviorally
accurate.

## User

An engineer, founder, or knowledge worker who uses YouTube for both learning and
distraction and wants a truthful breakdown of that time.

## Problem

YouTube usage is semantically mixed. A two-hour session could be a focused
course, passive entertainment, or a drift from intentional learning into
recommendation-driven consumption. App-level time tracking cannot see this.

## Inputs

The MVP should start with a local sample file before integrating with live
capture. The sample should support:

- Video title
- URL or video ID
- Channel name when available
- Watch duration
- Watched timestamp
- Optional description or page metadata

## Classification Labels

- `learning`: intentional educational, technical, professional, or
  skill-building content.
- `entertainment`: passive consumption, reaction content, general distraction,
  or content consumed without a clear learning intent.
- `unknown`: insufficient metadata or ambiguous activity. Unknown should be
  visible, not hidden.

## Outputs

- Per-video label, confidence, and reason.
- Aggregate watched duration.
- Percentage learning.
- Percentage entertainment or passive consumption.
- A daily narrative suitable for the product UI or CLI.

## Acceptance Criteria

- Runs locally from a fresh checkout.
- Has deterministic sample data for tests.
- Provides a repeatable evaluation command.
- Produces a summary similar to: "You spent 2h on YouTube. 68% was passive
  consumption."
- Does not require cloud storage or cloud inference for the default path.

## Verification

The current implementation includes:

- Unit tests for classification rules and aggregation.
- A fixture-based evaluation over sample YouTube activity.
- A labeled evaluation set with learning, entertainment, and unknown examples.
- CLI output through `python3 -m intentos.cli`.
- `scripts/product/verify.sh`, which is called by `make verify`.

## Product Risks

- Bad labels break trust quickly.
- A dashboard without action may feel interesting once and then become stale.
- The model must expose uncertainty instead of pretending all classifications
  are precise.
