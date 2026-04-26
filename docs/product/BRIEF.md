# Product Brief: IntentOS

This file is the product source of truth. Update it before asking Codex to build
product functionality.

## Current State

IntentOS has a product direction and a first local CLI MVP. The current
implementation classifies deterministic sample YouTube watch activity into
learning, entertainment, or unknown and reports aggregate time insights.

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

## First Useful Slice

Week 1 focuses on YouTube classification:

- Detect watched YouTube videos.
- Classify watched videos as learning or entertainment.
- Report the user's YouTube time split.

Example output:

> You spent 2h on YouTube. 68% was passive consumption.

The detailed MVP spec is
[mvp-youtube-classification.md](mvp-youtube-classification.md).

## Acceptance Criteria

- The system can ingest a local sample of watched YouTube activity.
- Each video is classified as learning or entertainment with a confidence score
  and short reason.
- The system outputs aggregate time spent, percentage learning, and percentage
  passive consumption.
- The system stores or processes data locally only.
- The result feels specific enough that target users say: "This is
  uncomfortably accurate."

## Non-Goals

- Full-device activity capture in the first slice.
- Browser extension distribution in the first slice.
- Cloud-hosted inference or cloud storage of personal activity.
- Automatic blocking, scheduling, or workflow execution in the first slice.
- Generic productivity dashboards that only restate app usage.

## Constraints

- Codex should be able to build, test, run, inspect, and document the product
  end to end.
- Product knowledge must live in this repository, not only in chat history.
- The first implementation should be a small complete vertical slice.
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

- What is the first source of YouTube watch history: browser history, exported
  Google data, a local browser extension, or manual sample import?
- What local model or classifier should be used for the MVP?
- How will the product evaluate classification accuracy before real users?
- What action loop follows the first insight?
