# Execution Plan: most-valuable-focus-rescue-strategy

Date: 2026-05-06
Status: Active

## Goal

Turn IntentOS from a private attention dashboard into a must-have focus rescue
product with a sharp acquisition wedge, a low-friction activation path, a daily
retention loop, and a credible path from trusted source beta to a free
open-source Mac product that builds the maintainer's brand.

The strategic bet is that the product wins by protecting a user's named
high-value commitment before the day is lost. It should not compete as another
time tracker, blocker, or analytics dashboard.

## Context

Product feedback says users are not sticky because the app still asks them to
  set up capture, inspect a dashboard, and interpret the evidence. The repo has
already moved toward a stronger wedge: the completed
[must-have focus rescue plan](../completed/2026-05-05-must-have-focus-rescue.md)
ships an in-day rescue state, recovery choices, and an evening proof-of-day
receipt.

Market signals support this wedge:

- Microsoft WorkLab's 2025 "infinite workday" report says Microsoft 365 users
  are interrupted every two minutes during core work hours, and nearly half of
  employees report chaotic, fragmented work.
- RescueTime, Rize, ActivityWatch, Opal, Freedom, Motion, and Reclaim all prove
  demand for automatic time awareness, blocking, focus sessions, or calendar
  defense. The gap IntentOS can own is intent-aware recovery: "I promised this
  mattered today; am I losing it right now?"
- Existing products mostly sell reports, blockers, timesheets, or schedules.
  IntentOS should sell a private local commitment guardian for builders whose
  work happens across editors, browsers, chat, and AI tools.

Reference links:

- [Microsoft WorkLab: Breaking down the infinite workday](https://www.microsoft.com/en-us/worklab/work-trend-index/breaking-down-infinite-workday/)
- [RescueTime](https://www.rescuetime.com/)
- [Rize](https://rize.io/)
- [ActivityWatch](https://activitywatch.net/)
- [Opal](https://opalapp.com/)
- [Reclaim getting started](https://help.reclaim.ai/en/articles/5224992-getting-started-with-reclaim)

## Scope

- Positioning: define IntentOS as "private focus rescue for builders," not time
  tracking, app blocking, or employee analytics.
- ICP: narrow the first audience to Mac-based founders, engineers, and
  independent builders with one expensive daily output commitment and repeated
  digital drift.
- Activation: reduce first value to a 5-minute setup and a 20-minute proof loop:
  install, grant local permissions, set one focus, set one avoid pattern, then
  see a live rescue state.
- Retention: make the daily loop habit-forming without gamification: morning
  commitment, in-day rescue, evening receipt, one next adjustment.
- Trust: keep the local-only privacy contract central to product, copy, setup,
  diagnostics, and open-source positioning.
- GTM: run founder-led concierge cohorts before public launch; show outcomes
  before polish.
- Brand: validate that the product is useful and distinctive enough that
  retained users talk about it, star it, share it, or associate the maintainer
  with private local focus tooling.
- Measurement: define traction metrics and deterministic product proxies so
  demand feedback becomes docs, fixtures, probes, or quality notes.

## Non-Goals

- Broad public launch before trusted beta retention is proven.
- Generic habit tracking, wellness journaling, team surveillance, or broad
  productivity-suite positioning.
- Cloud storage, cloud inference over personal activity, screenshots,
  keylogging, page bodies, cookies, or browser-history ingestion.
- Calendar automation, hard blocking, notifications, scheduling, mobile, or team
  management until the private focus rescue loop is sticky for the first ICP.
- Optimizing for vanity metrics such as waitlist size before activation and
  weekly retention are credible.

## Strategy

### 1. Make The Promise Painfully Specific

Default promise:

> IntentOS privately notices when today's most important work is losing to the
> avoid pattern you named this morning, while there is still time to recover.

Reject broader copy such as "AI productivity dashboard" or "automatic time
tracker." The product should be judged by one question: would the priority user
be upset if IntentOS stopped protecting their named focus next week?

### 2. Own A Narrow Beachhead

First ICP:

- Mac-based founder, engineer, creator, or independent operator.
- Uses browser, editor, chat, and AI tools heavily.
- Has one daily output that materially changes their week.
- Already knows they drift, but sees it too late.
- Cares enough about privacy to prefer local capture over cloud dashboards.

Do not chase students, broad wellness users, enterprise admins, or mobile-first
screen-time users until the first ICP retains.

### 3. Collapse Onboarding To First Rescue

The first-run path should be:

1. Start local app.
2. Explain the privacy boundary in one screen.
3. Run permission check with one-click repair guidance.
4. Ask for one focus and one avoid pattern.
5. Show the exact local signals IntentOS will match.
6. After enough evidence, show one state: protected, leaking, rescue available,
   or evidence insufficient.

Every extra setup step must either increase trust or improve first rescue
accuracy. Otherwise it is friction.

### 4. Design For The Daily Habit

The habit loop should be:

- Morning: "What must be protected today? What must not steal it?"
- Workday: "You are safe," "avoid is leaking," or "recovery is still possible."
- Rescue: choose return to focus, continue intentionally, pause, or correct
  evidence.
- Evening: receipt with protected focus time, avoid leakage, rescue moments,
  corrections, and tomorrow's adjustment.

The product should not shame the user. "Continue intentionally" is a success
when the user consciously changes the plan.

### 5. Win Trust Before Scale

The defensible product surface is local, inspectable, and correction-driven:

- No screenshots, keylogging, page bodies, cookies, telemetry, or cloud
  inference.
- Corrections layer over raw events and improve future matching.
- Diagnostics are shareable without exposing raw local data.
- The free open-source model should reinforce trust: no employer surveillance
  SKU, no cloud upsell over personal activity, and no hidden telemetry.

### 6. GTM: Concierge Cohorts Before Public Launch

Run small cohorts of 5-10 high-agency Mac builders. For each cohort:

- Recruit from founder, indie hacker, engineer, AI-builder, and deep-work
  communities.
- Screen for a painful repeated avoid pattern and one measurable output goal.
- Install live with the tester, watch setup friction, and collect the first
  daily receipt.
- Ask the demand question after day 3 and day 7.
- Convert trust-breaking labels into fixture candidates before classifier work
  is considered done.

Do not launch Product Hunt, broad social campaigns, or broad public promotion
until activation is smooth enough that strangers can reach first rescue without
a call.

### 7. Build Brand Through Public Proof

Open-source hypothesis:

- Keep the product free and open-source.
- Use a trusted cohort to produce credible public proof: setup clips,
  before/after daily receipts, privacy writeups, architecture notes, and
  fixture-driven improvement stories.
- Treat stars, forks, thoughtful issues, retained users, referrals, and
  invitations to collaborate as brand signals.
- Avoid monetization mechanics that make users doubt the local-only privacy
  contract.

## Acceptance Criteria

- The active focus-rescue implementation ships the first measurable product
  moment: current rescue state, one recovery choice, and evening receipt.
- Trusted beta setup reaches first value in under five minutes for technical Mac
  testers after dependencies exist locally.
- At least five target users complete a three-day focus rescue cohort.
- At least three target users complete a seven-day cohort.
- At least two target users say they would be upset if IntentOS stopped
  protecting their named focus next week, and their feedback is recorded in
  docs, fixtures, quality notes, or active plans.
- At least one tester refers another target user, opens a useful issue, or
  agrees to be cited in an anonymized public proof note.
- Product copy and UI avoid generic dashboard positioning and lead with focus
  rescue.
- Any repeated setup, trust, classification, or retention failure becomes a
  harness check or a documented manual exception.

## Metrics

- Activation: percentage of target testers who reach first rescue state within
  the first work session.
- Setup friction: median time from clone or app open to ready capture.
- Daily commitment rate: percentage of active days with focus and avoid set
  before noon local time.
- Rescue usefulness: percentage of avoid-leaking states followed by return to
  focus, continue intentionally, or correction.
- Review completion: percentage of active days with evening receipt reviewed.
- Accuracy trust: correction rate, low-confidence count, and repeated
  wrong-label classes promoted into fixtures.
- Retention: day 3, day 7, and week 2 active usage among target testers.
- Demand and brand: "upset if gone" yes rate, referred tester count, GitHub
  stars or issues from target users, and permission to share anonymized proof.

## Harness Impact

- Runtime commands and artifacts: `make beta-dev`, `make beta-status`,
  `make validate-beta`, `make validate-ui`, `make dogfood-smoke`,
  `make feedback-fixture-candidates`, and `make diagnose-json` should expose
  activation, rescue, correction, and receipt evidence.
- Fixtures or fakes required for deterministic `make verify`: add or update
  scenarios for first-run setup, first rescue state, avoid leaking, recovery
  accepted, continue intentionally, correction applied, evidence insufficient,
  and evening receipt.
- UI validation or screenshot evidence: rendered probes should fail if the
  first viewport returns to generic analytics, hides rescue state, hides the
  recovery choice, breaks long-text wrapping, or shows developer-facing setup
  copy.
- Structured logs, metrics, or diagnostics: record local activation milestone,
  rescue state transitions, recovery choices, correction count, and receipt
  readiness without raw page bodies, screenshots, cookies, tokens, or full text.
- Privacy, permission, or local-only constraints: preserve metadata-first local
  capture, pause/resume/delete-local-data, exclusion rules, and correction
  overlays; do not add cloud calls to personal activity data.
- Docs or harness checks to update: product brief, design doc, trusted beta
  handoff, quality scorecard, active focus-rescue plan, visible-copy policy,
  beta validation, UI render probe, and feedback fixture workflow.

## Roadmap

### Phase 0: Positioning Lock

- Rewrite visible product copy around "private focus rescue for builders."
- Remove or subordinate dashboard-first language.
- Add the demand question to every tester feedback flow.

### Phase 1: Must-Have Product Moment

- Ship the active focus-rescue plan.
- Make the menu bar and dashboard lead with rescue state.
- Add recovery choices and evening proof-of-day receipt.
- Verify through `make validate-beta`, `make validate-ui`, and `make verify`.

### Phase 2: Activation Compression

- Package the source beta path so a technical Mac tester can start without
  reading the repo.
- Make permission check, capture health, and privacy boundaries self-explanatory.
- Instrument local activation milestones in diagnostics.

### Phase 3: Concierge Cohort

- Recruit 5-10 Mac builders with a concrete daily output and avoid pattern.
- Run three-day and seven-day cohorts.
- Record all demand answers and friction themes in durable docs.
- Promote repeated classification feedback into fixture candidates.

### Phase 4: Public Open-Source Beta

- Publish only after retention signal exists.
- Keep the product free and open-source.
- Publish a plain-language privacy page, setup guide, architecture note, and
  anonymized proof examples.
- Open access through referrals from retained testers before broad promotion.

### Phase 5: Expansion Only After Pull

- Add richer browser capture or local model inference only when it materially
  improves rescue accuracy for retained users.
- Add calendar or notification hooks only when users ask for earlier recovery,
  not because the product needs more features.
- Explore teams only when individual users pull the product into work groups
  and privacy controls can prevent surveillance use.

## Verification

- `make harness-check`
- `make harness-lint`

## Implementation Notes

- "Most valuable app" is not a feature volume goal. For this product, value
  comes from protecting a scarce daily commitment with enough trust and accuracy
  that the user changes behavior.
- The strongest near-term moat is not an AI model. It is a private local data
  contract, a correction loop, and a daily product moment that competitors do
  not frame around named intent recovery.
- The product should keep saying "evidence insufficient" when metadata is thin.
  False certainty will hurt trust faster than sparse data.

## Progress Log

- 2026-05-06: Plan created from product strategy review and current market
  positioning research.
- 2026-05-06: Must-have focus rescue implementation completed; next work should
  validate demand with trusted testers and reduce activation friction.

## Handoff Notes

Start with trusted tester demand validation and activation compression. This
strategy plan should steer copy, setup, activation metrics, tester selection,
open-source trust, and brand-building proof.
