# Trusted Source Beta Handoff

IntentOS is ready for trusted macOS source-beta testing with technical users.
This is not a public beta, notarized installer, or broad nontechnical release.

The launch goal is retention and trust: testers should be able to run the local
beta, grant permissions, see current-day activity, correct labels, complete the
daily intent loop, and share diagnostics without exposing raw personal data. The
product demand question is whether IntentOS protects a named focus strongly
enough that the tester would miss it next week.

## Tester Boundary

Invite 2-5 Mac users who are comfortable with:

- Running a source checkout or local ad-hoc app bundle.
- Granting macOS Accessibility permission, and browser Automation permission
  when browser title or URL enrichment is desired.
- Using Terminal if the menu bar app setup fails.
- Sharing command output, screenshots of permission state, or generated
  diagnostics instead of raw SQLite data.

Do not present this build as a polished installer, notarized app, public beta,
or cloud product.

## What Ships

- Native macOS frontmost app and window metadata capture.
- Optional browser title, URL, and domain enrichment when local permissions
  allow it.
- Optional Chrome MV3 bridge for bounded active-tab metadata.
- Local SQLite persistence under `.harness/runtime/beta/` with 30-day
  retention.
- Service-backed daily review dashboard.
- Sticky daily loop: one focus, one surface to avoid, evening review, and next
  adjustment.
- Local label corrections layered over raw events.
- Pause, resume, diagnostics, permission guidance, and delete-local-data.
- Local ad-hoc Swift menu bar app build/install path.

## Privacy Contract

IntentOS captures metadata only. It must not capture or retain:

- Screenshots or screen recordings.
- Keystrokes.
- Page bodies, cookies, tokens, or form contents.
- Browser history databases.
- Cloud telemetry, cloud storage, or cloud inference.

Diagnostics should use `make beta-status`, permission-check output,
`make diagnose-json`, smoke artifacts, or redacted feedback candidates. Do not
ask testers to share `.harness/runtime/beta/intentos.sqlite`.

## Setup Path

Preferred trusted-tester path:

1. Send the tester `.harness/runtime/artifacts/IntentOS-trusted-beta.zip`.
2. The tester opens `IntentOS.app`.
3. First run walks through Privacy, App access, Capture check, Daily focus, and
   First block.
4. Browser detail and the Chrome bridge are optional after app/window capture
   is healthy.

Build that artifact from the repo:

```sh
make package-onboarding-beta
```

Developer fallback from a fresh checkout:

```sh
make verify
make package-beta
make install-beta-app
```

If the app path is not working, run the beta directly:

```sh
make beta-dev
```

Then open the URL printed as `INTENTOS_BETA_UI_URL`.

## Permissions

Use `Run Permission Check` from the IntentOS menu, or run:

```sh
make beta-status
```

Required for native capture:

- Accessibility permission for the app or process that launched the beta.

Optional but useful:

- Browser Automation permission for active-tab title and URL enrichment.
- Chrome bridge extension for richer Chrome active-tab metadata.

If macOS lists Terminal, Python, osascript, Codex, or IntentOSBeta, enable the
entry that launched the beta.

## Chrome Bridge

The Chrome bridge is optional for first value. Native recorder capture remains
the primary launch path.

Package the extension:

```sh
make package-extension
```

Install the generated extension zip from
`.harness/runtime/artifacts/IntentOSChromeBridge.zip`, then run:

```sh
make chrome-bridge-smoke
```

The bridge is launch-ready on a trusted machine when the smoke reaches
`connected` or `posting_events`. A missing bridge is only a warning when native
recorder rows are increasing.

## Daily Test Flow

Ask each tester to complete this once:

1. Start IntentOS through the menu bar app or `make beta-dev`.
2. Confirm `make beta-status` reports the service as ready, native recorder as
   running, and SQLite `quick_check` as `ok`.
3. Set today's focus and one surface to avoid in the dashboard.
4. Work normally for at least two hours or until the evening review becomes
   available.
5. Review plan-vs-actual, correct any wrong labels, and submit the evening
   check-in with one next adjustment.
6. Answer the demand question: "Would you be upset if IntentOS stopped
   protecting this focus next week?"
7. Share feedback using the template below.

## Stop And Reset

Stop the beta runtime:

```sh
make beta-stop
```

Pause capture from the dashboard or menu bar when testing sensitive work.

Delete local user data from the dashboard or menu bar. This clears beta user
tables and generated beta review/smoke artifacts while preserving enough
runtime state to explain service health.

## Diagnostics To Share

Preferred:

```sh
make beta-status
make diagnose-json
make dogfood-smoke
```

For UI or permission issues, screenshots of the dashboard notice, permission
check output, or macOS permission panes are acceptable.

For label quality issues after corrections exist:

```sh
make feedback-fixture-candidates
```

Only commit or share privacy-redacted fixture candidates after reviewing them.

## Troubleshooting

Dashboard says reconnect:

```sh
make beta-status
make beta-stop
make beta-dev
```

No activity appears:

```sh
make beta-status
```

Check Accessibility permission for the launcher process, then keep IntentOS
running while switching apps for a few minutes.

Browser metadata is sparse:

- Confirm native app/window capture works first.
- Grant browser Automation permission if requested.
- Install the optional Chrome bridge only after native capture is healthy.

Pause does not look private:

```sh
make dogfood-smoke
```

The smoke verifies that recorder heartbeats remain fresh while activity row
counts stay stable during pause.

## Feedback Template

Use one feedback record per test day:

```md
## Tester

- macOS version:
- Launch path: menu bar app or make beta-dev
- Browser used:
- Chrome bridge installed: yes/no

## Setup

- Setup blocker:
- Permission-check output summary:
- beta-status readiness:

## Capture Health

- Saw current-day activity: yes/no
- Missing app/window/browser surfaces:
- Pause/resume behaved correctly: yes/no

## Review Trust

- Wrong labels:
- Low-confidence or unknown examples:
- Corrections submitted:
- Any privacy concern:

## Daily Loop

- Focus set:
- Avoid target set:
- Evening review completed: yes/no
- Did the review change tomorrow's behavior:
- Would you be upset if IntentOS stopped protecting this focus next week:
- What would make the answer definitely yes:

## Diagnostics Shared

- beta-status:
- diagnose-json:
- smoke artifact:
```

## Launch Criteria

The trusted source beta is considered launched when:

- At least two testers launch through the menu bar app or `make beta-dev`.
- At least two testers grant required permissions and see current-day activity.
- At least two testers complete focus, avoid, evening review, and check-in.
- At least two testers answer whether they would be upset if IntentOS stopped
  protecting their named focus next week, and the answers are recorded in docs,
  plans, fixtures, or quality notes.
- `make beta-status` reports ready service, running native recorder, and
  SQLite `quick_check` `ok` on tester machines.
- At least one installed Chrome bridge smoke reaches `connected` or
  `posting_events`.
- Feedback that changes product assumptions is recorded in docs, plans,
  fixtures, or quality notes.

## Current Local Evidence

2026-05-03 launch gate on the dogfood machine:

- `make cleanup-check` passed.
- `make validate-ui` passed with desktop and mobile render probes.
- `make validate-beta` passed with service-backed desktop and mobile render
  probes.
- `make verify` passed.
- `make package-beta` built `.harness/runtime/artifacts/IntentOSBeta.app` with
  ad-hoc signing.
- `make install-beta-app` installed and opened
  `/Users/kgopal/Applications/IntentOSBeta.app`.
- `make package-extension` wrote
  `.harness/runtime/artifacts/IntentOSChromeBridge.zip`.
- `make beta-status` reported readiness `ready`, native recorder `running`,
  SQLite `quick_check` `ok`, and Chrome bridge `never_connected` as an
  optional unchecked enhancement.
- `make diagnose-json` wrote
  `.harness/runtime/artifacts/diagnose.json`.
- `make dogfood-smoke` passed for 30 minutes without fake bridge rows. Rows
  increased from 6032 to 6119, native recorder stayed `running`, pause privacy
  passed, and Chrome bridge absence was recorded only as a warning.

Remaining blocker:

- `make chrome-bridge-smoke` wrote
  `.harness/runtime/artifacts/beta-chrome-bridge-smoke.json` with status
  `blocked` because the installed Chrome bridge did not reach `connected` or
  `posting_events` before timeout. Native recorder stayed `running` and rows
  increased from 6124 to 6159 during that blocked smoke.
