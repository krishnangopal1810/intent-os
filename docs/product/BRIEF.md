# Product Brief: IntentOS

This file is the product source of truth. Update it before asking Codex to build
product functionality.

## Current State

IntentOS has a product direction and local CLI MVPs for YouTube and generic
multi-app activity classification. The current implementation classifies
deterministic fixtures into behavior labels and reports aggregate time insights.

The preferred product path is now generic `ActivityEvent` classification. The
YouTube MVP remains as a concrete domain slice and regression fixture.

The current live product slice captures metadata-only macOS app/window samples,
enriches supported browser active-tab metadata when local Automation permission
allows it, and replays the result into the UI. It now supports one-shot manual
capture, a visible automated background timeline during local UI runs, and a
bounded live session timeline. The automated timeline keeps raw diagnostic
samples separate from merged user-facing activity segments, without adding
manual imports, screenshots, OCR, or model-backed classification.

The dogfood beta slice adds a local service-backed product loop: a Python
service stores normalized activity in SQLite for 30 days, runs a native macOS
background recorder as the default automated source, accepts optional bounded
Chrome tab metadata through a localhost extension bridge, serves daily review
APIs, lets users correct labels locally, guides first-run permissions without
blocking the dashboard, and can be launched through a native macOS menu bar
wrapper. The daily review UI now leads with a plan-vs-actual coach loop: the
user sets one focus and one thing to avoid, IntentOS renders the deterministic
signals it will match, compares the plan with captured behavior, recommends one
next block, surfaces a focus-rescue state when strict avoid evidence crosses
five minutes, records local rescue choices, rewards corrections as accuracy
improvements, and keeps weekly patterns collapsed behind progressive
disclosure.
Manual imports remain fixture/parser-only; beta users should not have to export
data to see value.

## Product Definition

IntentOS is a personal behavior intelligence system. It runs on-device and
understands how a user actually spends digital time: not just which apps they
used, but what they were doing and why.

It is not a time tracker. It is a behavior intelligence layer for digital life.

The demand wedge is sharper than behavior analytics: IntentOS must help the
user protect a named high-value commitment before the day slips away. People do
not need another dashboard. They may want a private system that notices when
the thing they promised themselves is losing to the avoid pattern they named
that morning, gives them a small rescue choice while recovery is still
possible, and produces an evening receipt that is specific enough to change the
next day.

## Target User

- Engineers
- Founders
- Knowledge workers
- High-agency people optimizing their time

Target users have high opportunity cost, already reflect on their behavior, and
are willing to try tools that make uncomfortable truths visible.

The priority beta user is narrower: a Mac-based builder with one valuable daily
output commitment, repeated digital drift, and enough agency to name both the
focus to protect and the surface to avoid. If that user would not be upset after
losing IntentOS for a week, the product is still too optional.

## Problem

Existing tools such as Screen Time and RescueTime mostly answer which apps were
used. Users want higher-level answers:

- Did I spend my time well?
- Am I learning or just consuming?
- Where am I wasting time without realizing it?

The core gap is that current tools do not reliably differentiate:

- Learning vs entertainment
- Deep work vs shallow work
- Intentional vs unconscious behavior

The urgent pain is not lack of information. Many target users already know they
waste time. The painful moment is realizing too late that the important thing
was never protected. A must-have IntentOS loop should make that loss visible
early enough to rescue, not merely explain it at night.

## Product Promise

IntentOS moves from activity tracking to intent inference. It transforms raw
digital activity into semantic insights about attention, intent, and behavior.

The first must-have promise is: "Tell me when my named focus is losing to the
avoid pattern I chose, while I can still recover the block."

## How It Works

1. Activity capture: app usage through macOS APIs, browser URLs and titles, and
   optional page metadata such as YouTube titles or document titles.
2. Semantic classification: deterministic rules and, later, optional
   on-device models classify activity into categories such as deep work,
   shallow work, learning, passive consumption, and communication.
3. Behavior inference: the system detects intent/outcome mismatch, recurring
   patterns, and time leakage.
4. Insight engine: the product outputs daily narratives, "you thought vs
   reality" comparisons, and behavioral anomalies.
5. Focus rescue: the beta turns the daily intent contract into a local in-day
   rescue state, then records whether the user recovered, continued
   intentionally, or corrected the evidence.

## Implemented Slices

### Metadata-Only Live Capture

The current live capture slice supports manual local smoke loops:

- frontmost macOS app/window metadata through local System Events
- best-effort browser active tab URL/title/domain enrichment
- local privacy exclusions and redaction before JSONL persistence
- visible automated background timeline status during `make dev` UI runs
- raw live sample artifacts plus merged timeline artifacts for the UI
- adjacent equivalent session sample merging
- replay through the generic `ActivityEvent` classifier
- UI preference for session timeline replay artifacts

Run:

```sh
make observe-live
make observe-session
```

These commands are intentionally manual and outside CI because they depend on
local macOS Accessibility and browser Automation permissions.

### Dogfood Beta Runtime

The current beta target is a trusted internal macOS dogfood build:

- local Python service bound to `127.0.0.1`
- SQLite database under `.harness/runtime/beta/intentos.sqlite`
- 30-day retention with startup cleanup
- native macOS recorder for frontmost app/window metadata and existing browser
  URL/title fallback
- optional Chrome bridge for richer URL/title/domain/tab metadata
- service-backed daily review UI with capture health, intent mix, merged
  timeline, plan-vs-actual coach hero, focus rescue state, next block, daily
  intent contract, weekly pattern disclosure, reactive surfaces,
  low-confidence segments, and local correction controls
- daily intent and evening review loop with deterministic intent-contract
  signals, plan-vs-actual receipts, correction reward, low-confidence count,
  and next adjustment handoff
- focus rescue action persistence for shown, return-to-focus,
  continue-intentionally, pause-capture, and corrected-evidence choices
- pause/resume and delete-local-data controls
- guided first-run local-only onboarding with Privacy, App access, Capture
  check, Daily focus, and First block steps; Accessibility is required for
  first value, while browser detail and the Chrome bridge are optional
- redacted setup report, capture preview, activation milestones, and stable
  trusted app identity surfaced through beta status
- local Swift menu bar wrapper that launches/stops the beta harness
- real dogfood smoke evidence that observes live local capture without seeding
  fake rows or deleting user data

Run:

```sh
make beta-dev
make beta-status
make validate-beta
make package-beta
make package-onboarding-beta
make install-beta-app
make package-extension
```

The beta remains local-only: no cloud sync, telemetry, page bodies,
keylogging, screenshots, OCR, or public distribution.

### Generic Multi-App Activity

The current generic classifier handles local fixture events from surfaces such
as ChatGPT, coding editors, WhatsApp, Slack, LinkedIn, Instagram, tax websites,
Notion, browser pages, and YouTube.

It classifies activity into the behavior taxonomy documented in
[TAXONOMY.md](TAXONOMY.md):

- deep work
- shallow work
- learning
- communication
- admin
- passive consumption
- active creation
- entertainment
- unknown

Run:

```sh
python3 -m intentos.activity_cli data/activity/multi_app_events.json
python3 -m intentos.activity_evaluate data/activity/evaluation_set.json --min-accuracy 85
```

### YouTube MVP

The first MVP focused on YouTube classification:

- Detect watched YouTube videos.
- Classify watched videos as learning or entertainment.
- Report the user's YouTube time split.

Example output:

> You spent 2h on YouTube. 68% was passive consumption.

The detailed MVP spec is
[mvp-youtube-classification.md](mvp-youtube-classification.md).

## Planned Capture and Inference

- [live-capture.md](live-capture.md) defines the metadata-first macOS capture
  architecture, source adapters, permissions, privacy defaults, and first live
  slice.
- [on-device-inference.md](on-device-inference.md) defines the rules-first
  inference ladder and where Apple Foundation Models, Core ML, or MLX may fit
  after deterministic fixture evaluation shows a need.
- [imports.md](imports.md) remains useful for deterministic fixture and parser
  contracts, but manual import is no longer the preferred user-facing product
  path because it adds friction.
- Live capture and beta capture must not use keylogging, raw screenshot
  retention, cloud inference, page bodies, cookies, or manual user exports as a
  primary product path.

## Current Verification

- `make verify` runs harness checks, structural linting, repository audit, unit
  tests, CLI smoke checks, YouTube evaluation, multi-app `ActivityEvent`
  evaluation, capture replay, beta validation, UI validation, package contract
  checks, cohort evidence checks, and screenshot freshness checks.
- The multi-app evaluation set keeps generic behavior classification from
  regressing while future adapters are added.
- The YouTube evaluation set preserves the first domain-specific slice as a
  regression fixture.

## YouTube MVP Acceptance Criteria

- The system can ingest a local sample of watched YouTube activity.
- Each video is classified as learning or entertainment with a confidence score
  and short reason.
- The system outputs aggregate time spent, percentage learning, and percentage
  passive consumption.
- The system stores or processes data locally only.
- The result feels specific enough that target users say: "This is
  uncomfortably accurate."

## Non-Goals

- Public continuous full-device activity capture outside the local dogfood
  beta.
- Public browser extension distribution.
- Cloud-hosted inference or cloud storage of personal activity.
- Automatic blocking, scheduling, or workflow execution in the current local
  slices.
- Generic productivity dashboards that only restate app usage.
- Broad consumer launch before the Mac builder focus-rescue loop has retained
  trusted testers.
- Public always-on live capture is not implemented.
- Screenshot capture and OCR are not part of the first live capture slice.

## Constraints

- Codex should be able to build, test, run, inspect, and document the product
  end to end.
- Product knowledge must live in this repository, not only in chat history.
- New implementations should be small complete vertical slices.
- Privacy is a product feature. The default design must be on-device.
- Classification accuracy is existential for user trust.

## Key Risks

1. Insight without timely rescue may cause churn.
2. Classification accuracy must be high enough to feel trustworthy.
3. Privacy concerns require on-device design and clear data handling.
4. The product can degrade into "just another productivity app" if it only
   summarizes app usage.
5. A broad audience can make the product feel optional; the beta must prove a
   narrow group wants the focus-rescue loop badly.

## Vision

Phase 1: Understanding. Provide accurate breakdowns of how time is spent.

Phase 2: Feedback. Detect misalignment, such as "You planned deep work, but
spent 60% in shallow loops."

Phase 3: Rescue. Surface timely, local recovery choices when the user's named
focus is losing to the avoid pattern they chose.

Phase 4: Execution. Take agentic actions such as blocking distractions,
scheduling focus blocks, and automating workflows.

## Long-Term Direction

IntentOS becomes the control plane for human digital behavior: a system that
understands intent, optimizes time, and executes actions on behalf of the user.

## Why Now

- Apple Silicon makes on-device inference practical.
- LLMs make semantic understanding of activity feasible.
- Demand for self-optimization tools is rising.

## Open Questions

- What in-day rescue moment makes the priority beta user say they would be
  upset to lose the app?
- Which automated source most improves that rescue moment first: browser
  extension metadata, calendar/planned-intent context, Accessibility excerpts,
  or IDE/Git/terminal context?
- How should labeled evaluation fixtures be expanded with real personal
  examples?
- What local model should eventually replace or augment deterministic rules?
- What action loop follows the first timely rescue?
