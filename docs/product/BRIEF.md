# Product Brief: IntentOS

This file is the product source of truth. Update it before asking Codex to build
product functionality.

## Current State

IntentOS has a product direction and local CLI MVPs for YouTube and generic
multi-app activity classification. The current implementation classifies
deterministic fixtures into behavior labels and reports aggregate time insights.

The preferred product path is now generic `ActivityEvent` classification. The
YouTube MVP remains as a concrete domain slice and regression fixture.

## Product Definition

IntentOS is a personal behavior intelligence system. It runs on-device and
understands how a user actually spends digital time: not just which apps they
used, but what they were doing and why.

It is not a time tracker. It is a behavior intelligence layer for digital life.

## Target User

- Engineers
- Founders
- Knowledge workers
- High-agency people optimizing their time

Target users have high opportunity cost, already reflect on their behavior, and
are willing to try tools that make uncomfortable truths visible.

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

## Product Promise

IntentOS moves from activity tracking to intent inference. It transforms raw
digital activity into semantic insights about attention, intent, and behavior.

## How It Works

1. Activity capture: app usage through macOS APIs, browser URLs and titles, and
   optional page metadata such as YouTube titles or document titles.
2. Semantic classification: on-device models classify activity into categories
   such as deep work, shallow work, learning, passive consumption, and
   communication.
3. Behavior inference: the system detects intent/outcome mismatch, recurring
   patterns, and time leakage.
4. Insight engine: the product outputs daily narratives, "you thought vs
   reality" comparisons, and behavioral anomalies.

## Implemented Slices

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

## Current Verification

- `make verify` runs harness checks, structural linting, unit tests, CLI smoke
  checks, YouTube evaluation, and multi-app `ActivityEvent` evaluation.
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

- Full-device activity capture in the current local slices.
- Browser extension distribution in the current local slices.
- Cloud-hosted inference or cloud storage of personal activity.
- Automatic blocking, scheduling, or workflow execution in the current local
  slices.
- Generic productivity dashboards that only restate app usage.
- Live capture is not implemented yet.

## Constraints

- Codex should be able to build, test, run, inspect, and document the product
  end to end.
- Product knowledge must live in this repository, not only in chat history.
- New implementations should be small complete vertical slices.
- Privacy is a product feature. The default design must be on-device.
- Classification accuracy is existential for user trust.

## Key Risks

1. Insight without action may cause churn.
2. Classification accuracy must be high enough to feel trustworthy.
3. Privacy concerns require on-device design and clear data handling.
4. The product can degrade into "just another productivity app" if it only
   summarizes app usage.

## Vision

Phase 1: Understanding. Provide accurate breakdowns of how time is spent.

Phase 2: Feedback. Detect misalignment, such as "You planned deep work, but
spent 60% in shallow loops."

Phase 3: Execution. Take agentic actions such as blocking distractions,
scheduling focus blocks, and automating workflows.

## Long-Term Direction

IntentOS becomes the control plane for human digital behavior: a system that
understands intent, optimizes time, and executes actions on behalf of the user.

## Why Now

- Apple Silicon makes on-device inference practical.
- LLMs make semantic understanding of activity feasible.
- Demand for self-optimization tools is rising.

## Open Questions

- What is the first real user-data import path: manual JSON/CSV, Google
  Takeout, browser history, macOS window tracking, or ChatGPT export?
- How should labeled evaluation fixtures be expanded with real personal
  examples?
- What local model should eventually replace or augment deterministic rules?
- What action loop follows the first insight?
