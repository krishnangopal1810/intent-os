# Execution Plan: frictionless-new-computer-onboarding

Date: 2026-05-06
Status: Active

## Goal

Make IntentOS installable and usable on a new Mac without asking the tester to
read the repository, understand harness commands, diagnose macOS permissions,
or decide which setup path matters.

The target first-run promise is:

> From download to first protected-focus signal in under five minutes, with no
> Terminal required for the normal path.

## Context

Current source-beta setup is powerful but too technical. A new tester may need
to clone the repo, run `make verify`, build a local menu bar app, install it,
run permission checks, understand Accessibility versus Automation, decide
whether the Chrome bridge matters, inspect `make beta-status`, and then set a
daily focus. That is appropriate for Codex and internal dogfood work, but it is
not a startup-grade onboarding path.

The current product already has important building blocks: a local-only privacy
contract, menu bar wrapper, permission status API, setup guidance, diagnostics,
daily focus/avoid inputs, focus rescue state, pause/resume, delete-local-data,
and deterministic beta validation. The plan is to collapse those pieces into a
single guided first-run experience.

Reference onboarding patterns:

- Cursor makes the default path direct: download, run installer, open app, then
  a short first-time setup; its download page also exposes a one-line terminal
  install for technical users.
  <https://cursor.com/download>
- Raycast's quickstart starts with download, then immediately asks the user to
  try one useful workflow instead of reading all features.
  <https://manual.raycast.com/quickstart>
- Linear offers a fast start guide with role-based paths, demo workspace, live
  onboarding, and a community support path.
  <https://linear.app/docs/start-guide>
- Slack's new-user guide focuses on a short ordered path: sign in, set profile,
  configure notifications, send the first message, then learn more.
  <https://slack.com/help/articles/218080037-Getting-started-for-new-Slack-users>
- Notion uses onboarding answers to select starter templates, so the first
  workspace already contains something useful.
  <https://www.notion.com/help/start-with-a-template>
- macOS permission work must respect the platform: Accessibility trust can be
  checked and prompted, but the user still grants access through the system UI.
  <https://developer.apple.com/documentation/applicationservices/1459186-axisprocesstrustedwithoptions>

## Scope

- Replace the normal trusted-tester path with one artifact and one first-run
  journey: install app, open app, grant required permission, set focus/avoid,
  verify capture, and start the first focus block.
- Keep Terminal and `make` commands as fallback diagnostics, not the primary
  experience.
- Make Accessibility the only required first-run permission. Browser
  Automation and Chrome extension setup should be optional "improve browser
  detail" steps after first value.
- Consolidate permissioned capture behind a stable signed app or helper
  identity so users grant access to `IntentOS`, not Terminal, Python, osascript,
  or Codex.
- Add a first-run wizard to the menu bar/dashboard flow with progress,
  repair buttons, live verification, and plain-language privacy copy.
- Add one-click redacted setup diagnostics for tester support.
- Add deterministic onboarding harness coverage so setup regressions fail
  locally before testers see them.
- Update source-beta docs so trusted testers receive one simple path and one
  fallback path.

## Non-Goals

- Public App Store release.
- Cloud accounts, cloud telemetry, cloud inference, or sync.
- Screen Recording, screenshots, OCR, keylogging, page bodies, browser history
  import, cookies, tokens, or form contents.
- Hard blocking, notifications, calendar automation, team management, or mobile
  onboarding.
- Requiring Chrome extension setup before the first useful focus-rescue signal.
- Solving demand validation; this plan only removes activation friction.

## Product Principles

- The default path should have one obvious next button at every point.
- The user should always know why a permission is needed before macOS asks.
- Optional setup must be visibly optional and deferred until it improves an
  already-working product.
- Every setup state needs an in-product verification result, not a request to
  inspect logs.
- The setup experience should produce value while it verifies itself: "IntentOS
  can see your current app/window" is the first trust moment.
- Privacy language should be specific and short: local metadata only; no
  screenshots, keylogging, page bodies, cookies, cloud sync, or telemetry.

## Target First-Run Flow

1. Download or receive `IntentOS.app` or `IntentOS.dmg`.
2. Drag/open the app. If the app is not in Applications, show a one-click move
   or clear guidance.
3. App opens the onboarding dashboard and starts local service/capture
   automatically.
4. Privacy screen states the local-only contract and asks the user to continue.
5. Required permission card: "App & window access." Button opens the
   Accessibility prompt/settings and then verifies readiness in place.
6. Optional permission card: "Browser detail." User can skip it and still
   proceed; the app explains that titles/URLs are better when enabled.
7. Optional extension card remains hidden behind "Improve browser detail" until
   native capture is healthy.
8. Capture check shows the current frontmost app/window metadata within 60
   seconds, or gives one repair action if it cannot.
9. User enters one focus to protect and one thing to avoid.
10. App starts a first focus block and shows the live state: protected, avoid
    leaking, recovery available, or needs evidence.
11. Dashboard and menu bar both expose "Setup complete", pause, delete local
    data, diagnostics, and a way to rerun onboarding.

## Implementation Plan

### Phase 1: Measure And Specify The Funnel

- Add a product spec section for activation milestones:
  `downloaded`, `opened`, `privacy_acknowledged`, `accessibility_verified`,
  `capture_verified`, `intent_set`, `first_rescue_state`, and
  `first_review_ready`.
- Record milestone timestamps locally in SQLite settings/runtime status.
- Add `time_to_capture_ready_seconds` and `time_to_intent_set_seconds` to
  redacted diagnostics.
- Update trusted beta feedback template to ask for setup time, permission
  confusion, first captured app/window, and first rescue state.

### Phase 2: Package A No-Terminal App Artifact

- Introduce a release packaging script that produces a tester-facing
  `IntentOS.app.zip` or `.dmg` with the menu bar app, web assets, service code,
  native capture helper, privacy policy, and uninstall/reset helper included.
- Keep `make package-beta` as the development path, but make the tester
  artifact runnable without repo checkout, `make`, Swift tools, or manual
  Python setup.
- Add preflight checks for macOS version, app location, writable local data
  directory, service port availability, and bundled runtime health.
- Prefer a boring bundled runtime or standalone service binary over asking new
  users to install Python, Homebrew, Xcode Command Line Tools, or repo
  dependencies.
- Add "Open at Login" as an opt-in after setup succeeds, not before trust is
  established.

### Phase 3: Stabilize macOS Permission Identity

- Move Accessibility-dependent capture into a signed native app/helper identity
  with a stable bundle identifier.
- Stop the normal first-run path from requiring the user to enable Terminal,
  Python, osascript, or Codex in Privacy & Security.
- Use the Accessibility trust prompt/check on app startup only after explaining
  why the app needs app/window metadata.
- Treat Browser Automation as optional enrichment and verify it only when a
  supported browser is frontmost.
- Add a "Something looks wrong" path that detects duplicate/old permission
  identities and explains exactly which one should be enabled.

### Phase 4: Build The Guided Onboarding UI

- Replace the current broad local setup panel with a compact stepper:
  `Privacy`, `App access`, `Capture check`, `Daily focus`, `First block`.
- Each step gets one primary action, one skip action only when safe, and a
  visible verification state.
- Show a live capture preview with bounded app/window/title/domain evidence
  after permission succeeds.
- Keep diagnostics and advanced setup behind disclosure.
- Add "Restart onboarding" from the menu bar and dashboard settings.
- Make empty and blocked states lead back into the stepper instead of a generic
  dashboard.

### Phase 5: Defer Optional Browser And Extension Work

- Rename browser setup around user value: "Browser detail", not Automation or
  Chrome bridge.
- Ask for browser detail only after native app/window capture is ready.
- Package the Chrome extension as an optional advanced artifact during source
  beta; for public beta, plan a Chrome Web Store path or remove it from first
  run.
- Keep `make chrome-bridge-smoke` manual until installed-extension setup is
  reliable.

### Phase 6: Make Support One Click

- Add "Copy Setup Report" and "Open Diagnostics" actions that include readiness
  states, milestone timings, app version, macOS version, service state, capture
  state, DB health, and recent redacted error summaries.
- Exclude raw titles, URLs, SQLite data, screenshots, page bodies, cookies,
  tokens, and keystrokes from the copied report.
- Add a visible "Delete local data" and "Uninstall IntentOS" explanation in the
  app, not only in docs.

### Phase 7: Validate With Trusted Testers

- Run the flow with 3-5 new-Mac or clean-user-profile testers before further
  feature work.
- Watch installation live once, then require the next tester to complete setup
  from the artifact without a call.
- Convert repeated setup failures into deterministic fake permission scenarios,
  UI probes, or quality notes before marking the plan complete.

## Acceptance Criteria

- A tester can install and open IntentOS from one app artifact without cloning
  the repo or running `make`.
- On first launch, IntentOS starts the local service, opens onboarding, and
  shows the privacy contract before requesting permissions.
- The normal setup path asks the user to grant access to `IntentOS`, not
  Terminal, Python, osascript, or Codex.
- Accessibility is the only required permission for first value; browser detail
  and extension setup are optional and deferrable.
- The app verifies capture by showing a bounded current app/window metadata
  preview within 60 seconds after permission is granted.
- A new tester can set one focus and one avoid target during onboarding and see
  a first live state without interpreting the dashboard.
- Dashboard and menu bar expose setup status, rerun onboarding, pause/resume,
  delete local data, and redacted diagnostics.
- Median setup time for trusted technical Mac testers is under five minutes
  after they have the app artifact locally.
- At least three trusted testers complete install, permission grant, focus
  setup, and capture verification from the artifact; all repeated friction is
  recorded as harness coverage or a documented manual exception.

## Harness Impact

- Runtime commands and artifacts: add a tester-package command such as
  `make package-onboarding-beta` or extend `make package-beta` to emit the
  no-terminal artifact, installer metadata, setup milestone artifacts, and
  redacted setup report evidence.
- Fixtures or fakes required for deterministic `make verify`: add fake
  onboarding scenarios for fresh install, app-not-in-Applications, missing
  Accessibility, Accessibility granted, capture preview success, capture
  preview blocked, optional browser detail skipped, optional browser detail
  granted, duplicate permission identity, and setup completed.
- UI validation or screenshot evidence: extend `make validate-beta` and the
  rendered probes so they fail if first-run setup is hidden, steps are out of
  order, optional setup blocks first value, privacy copy is vague, long setup
  text clips, or the capture preview is missing in a ready scenario.
- Structured logs, metrics, or diagnostics: log local activation milestones,
  setup step transitions, permission check results, capture preview state, and
  setup report generation without raw personal activity data.
- Privacy, permission, or local-only constraints: preserve local-only metadata
  capture, pause/resume/delete-local-data, 30-day retention, no screenshots, no
  keylogging, no page bodies, no cookies, no cloud telemetry, and no cloud
  inference.
- Docs or harness checks to update: product brief, design doc, app runtime doc,
  security doc, trusted source beta handoff, quality scorecard, active strategy
  plan, `scripts/product/validate-beta.sh`, `scripts/product/ui-render-probe.js`,
  `scripts/product/render-ui-check.py`, and permission/unit tests.

## Verification

- `make harness-check`
- `make harness-lint`
- `make validate-beta`
- `make validate-ui`
- `make package-beta`
- new tester-package validation command once added
- `make dogfood-smoke` on a real Mac after permission identity changes
- `make verify`

## Implementation Notes

- The current setup panel and permission API are useful foundations, but the
  experience should be reframed around a user journey instead of a checklist.
- The biggest technical risk is macOS TCC identity. If the permissioned work
  stays in Python/osascript child processes, onboarding will remain confusing.
  The permissioned recorder should run under a stable signed `IntentOS`
  identity before this plan is considered complete.
- Browser extension setup should not block this plan. Native app/window
  metadata is already the primary beta path and should prove first value.
- Public notarization can come later, but the packaging shape should not assume
  users have the source tree, Swift compiler, Python, or `make`.

## Progress Log

- 2026-05-06: Plan created from product feedback that new-computer install,
  permissions, and first start are unintuitive and too difficult.
- 2026-05-06: Implemented first onboarding slice: guided first-run stepper,
  activation milestones, capture preview, redacted setup report, stable
  trusted app identity, bundled tester artifact target, optional browser detail,
  and deterministic beta validation coverage.

## Handoff Notes

Remaining hardening should focus on a real clean-profile Mac install and the
native permission boundary. The trusted app now uses a stable IntentOS bundle
identity and bundled runtime path, but the recorder still relies on the current
metadata adapter stack rather than a separate fully native helper.
