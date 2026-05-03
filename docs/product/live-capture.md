# Live Activity Capture

This spec defines the intended local capture architecture for IntentOS. The
current implementation includes fake-sensor capture fixtures, a manual
frontmost macOS app/window adapter, best-effort active browser tab enrichment,
an automated background timeline for local UI runs, and a dogfood beta recorder
that persists accepted metadata to local SQLite. The background timeline keeps
raw diagnostic samples separate from the merged user-facing activity timeline.
Future work must keep live capture metadata-first, permission-aware, visible in
runtime status, and reversible.

## Goal

Convert what the user is actively doing on macOS into local `ActivityEvent`
records that the existing behavior classifier can process.

The capture system should answer questions like:

- Is the user watching a YouTube video, reading a document, talking to ChatGPT,
  scrolling LinkedIn, coding, doing admin work, or playing a game?
- What evidence supports that classification?
- How confident is the system, and when should it preserve `unknown`?

## Signal Hierarchy

Use the cheapest, most structured, least invasive signal that can answer the
question.

1. Active app and process metadata from `NSWorkspace`.
2. Focused window title and accessible UI metadata from Accessibility APIs.
3. Active browser tab URL and title from browser adapters.
4. Short visible text excerpts from Accessibility where the app exposes them.
5. ScreenCaptureKit frame capture only as a fallback for low-confidence events.
6. Vision OCR on fallback frames when text metadata is unavailable.
7. Local classifier or model inference over the normalized event evidence.

Do not use screenshots when app, window, URL, and title metadata are enough.

## Source Adapters

Each source adapter must emit raw observations that can be normalized into
`ActivityEvent`.

| Source | Purpose | Permission |
| --- | --- | --- |
| `NSWorkspace` active app watcher | App name, bundle ID, process ID, app switch timing | none or standard app runtime |
| Accessibility focused-window reader | Window title, focused element, limited visible text | Accessibility permission |
| Browser adapters | Active tab URL/title for Safari, Chrome, Arc, and similar browsers | browser-specific local permission or automation access |
| ScreenCaptureKit fallback | Window or display frame when metadata is insufficient | Screen Recording |
| Vision OCR fallback | Text extraction from captured frames | local processing |

No keylogging is allowed. Keyboard input, clipboard contents, and password
fields are out of scope unless a future privacy review explicitly narrows and
approves a specific use.

## ActivityEvent Contract

Live capture must normalize into the generic event model, not a separate
classifier path.

Required event evidence:

- timestamp or start/end time
- duration
- app name
- bundle ID when available
- window title when available
- URL and domain when available
- short visible text excerpt when available and allowed
- source adapter
- confidence/evidence provenance

The classifier should receive bounded text snippets, not entire pages,
transcripts, screenshots, or conversations.

## Privacy Defaults

- Local-only storage and local-only inference by default.
- No keylogging.
- Raw screenshots are disabled by default.
- Raw screenshots must not be retained unless the user explicitly enables a
  debug mode.
- Sensitive surfaces must support an exclusion list by app, domain, URL pattern,
  and window title.
- Browser private/incognito contexts should be ignored or reduced to coarse app
  usage.
- Password fields, payment forms, banking, tax, health, and authentication
  pages should default to metadata-only capture or exclusion.
- Map, directions, and location-bearing navigation URLs are excluded by default
  because browser URLs can encode precise location coordinates.
- The user must be able to pause capture.
- Background capture must be explicit in `make app-status`, write local logs,
  and stop with `make app-stop`.

## Shipped Live Slices

The first live slice shipped as a one-shot manual capture path:

1. Active app/window sampler using macOS frontmost app/window metadata.
2. Browser active-tab metadata for supported browsers.
3. JSONL writer for local `ActivityEvent` records.
4. Replay command that classifies captured JSONL with the existing classifier.
5. Fixture tests for sampler output normalization and redaction.

The automated background timeline and session timeline slices are built on top
of the one-shot path. Background capture starts with the local UI, writes raw
diagnostic samples, merges adjacent equivalent activity into a user-facing
timeline artifact, and refreshes the live summary from that timeline. Bounded
manual sessions use the same merge behavior for local diagnostics. The CI path
uses `data/capture/fake_session_observations.json` and fake live providers so
parser, privacy, merge, replay, and UI behavior remain deterministic.

The dogfood beta recorder adds local SQLite persistence on the same
`ActivityEvent` boundary. It treats idle samples over five minutes as away time,
records long timestamp gaps as status notes instead of inventing activity, and
stores Chrome extension bridge events only after service-side privacy filtering.
Pause is a privacy control: while paused, the recorder should emit health
heartbeats but must not persist new activity rows. Corrections are derived
overlays and never mutate raw events.

ScreenCaptureKit and Vision OCR are deferred until metadata-only capture shows
clear gaps. On-device model inference is a second-pass classifier, not a
requirement for the first live slice.

## Current Manual Adapter

IntentOS currently provides a manual macOS frontmost app/window adapter through:

```sh
python3 -m intentos.capture_cli capture-macos --duration-seconds 5 --output .harness/runtime/artifacts/live-capture-events.jsonl
```

The adapter uses local `osascript`/System Events metadata to capture app name,
bundle ID, process ID, and focused window title. When the frontmost app is a
supported browser and Automation permission allows it, the capture path also
adds active tab URL, title, and domain. It does not capture keystrokes,
screenshots, OCR text, clipboard contents, page bodies, or transcripts.
It may require Accessibility permission and browser Automation permission for
the terminal or Codex host app.

Replay the result with:

```sh
python3 -m intentos.capture_cli replay .harness/runtime/artifacts/live-capture-events.jsonl
```

Or use the harness wrapper:

```sh
make observe-live
```

`make observe-live` captures one live metadata sample, prints the latest
`ActivityEvent`, replays it through the classifier, and writes
`.harness/runtime/artifacts/live-capture-summary.json` plus
`.harness/runtime/logs/live-capture.log`. The deterministic product artifact
build clears stale live capture artifacts unless preservation is requested; the
`make dev` harness then starts the automated background timeline and writes
fresh `live-capture-*` artifacts. If privacy exclusions drop every row, the
live summary is still written with an empty report.

## Current Session Timeline

IntentOS also provides a manual bounded session command:

```sh
python3 -m intentos.capture_cli capture-session --duration-seconds 30 --interval-seconds 5 --output .harness/runtime/artifacts/live-session-capture-events.jsonl
```

Or use the harness wrapper:

```sh
make observe-session
```

The session path repeatedly samples the same metadata sources, enriches each
browser sample when possible, applies the privacy policy, drops excluded rows,
merges adjacent equivalent `ActivityEvent` rows, and replays the resulting
timeline through the existing classifier. It writes
`.harness/runtime/artifacts/live-session-capture-summary.json` and
`.harness/runtime/logs/live-session-capture.log`. It does not capture
keystrokes, screenshots, OCR text, clipboard contents, page bodies, or
transcripts.

Use `make dev-live` when the UI should show a fresh live session. It runs this
bounded session command first, preserves the live replay artifact, and then
starts the UI with a strict `?mode=live-session` URL. The resulting session
timeline reflects only the activity captured during that bounded command
window, not historical macOS usage. The UI must show a live-capture error when
that live session artifact is unavailable; it must not fall back to fixture
capture summaries from an explicit live URL.

## Current Background Timeline

`make dev` starts the local UI and then starts a visible background metadata
sampler:

```sh
python3 -m intentos.capture_cli capture-live --interval-seconds 2 --output .harness/runtime/artifacts/live-capture-events.jsonl --timeline-output .harness/runtime/artifacts/live-capture-timeline-events.jsonl --summary-json .harness/runtime/artifacts/live-capture-summary.json --summary-text .harness/runtime/artifacts/live-capture-summary.txt --status-json .harness/runtime/artifacts/live-capture-status.json
```

The sampler appends privacy-filtered raw `ActivityEvent` rows to
`live-capture-events.jsonl`, merges adjacent equivalent rows into
`live-capture-timeline-events.jsonl`, refreshes `live-capture-summary.json` from
the merged timeline after each sample, and writes status under
`.harness/runtime/artifacts/live-capture-status.json`. Its PID, interval, raw
output path, timeline output path, status path, and log path are recorded in
`.harness/runtime/app.env`, and `make app-stop` stops it. It records frontmost
app/window metadata and, for supported browsers, active tab URL/title/domain
when Automation permission allows it.

## Dogfood Beta Capture

`make beta-dev` starts a local service-backed beta flow:

```sh
make beta-dev
make beta-status
make beta-stop
```

The beta service stores accepted events in
`.harness/runtime/beta/intentos.sqlite`, exposes `/api/status`,
`/api/daily-review`, `/api/events`, `/api/corrections`, `/api/pause`,
`/api/resume`, `/api/delete-local-data`, and `/api/browser-event`, and serves
the dashboard from `.harness/runtime/beta/site/` with service-backed beta mode
required. If the beta service config is missing, the UI must show a live
service problem rather than fixture reports. The live beta dashboard does not
show a separate YouTube domain panel; real YouTube activity is folded into the
normal activity mix, timeline, and review queues. The Chrome MV3 bridge shell
captures only bounded tab metadata: URL, title, domain, tab/window id, active
state, timestamp, source, and optional YouTube/document page-kind metadata. It
does not send page bodies, cookies, tokens, screenshots, keystrokes, or
clipboard contents.

Daily review APIs summarize the requested local day, labeled in the UI as
“Today since midnight” for the current day, and include the beta service start
timestamp separately. Recorder health is based on both process state and fresh
heartbeat updates so a stalled recorder does not appear healthy just because an
old PID or last event remains in SQLite.

## Harness Requirements

Future capture work must update:

- this spec
- [on-device-inference.md](on-device-inference.md) when model behavior changes
- [../SECURITY.md](../SECURITY.md) when permissions or data handling changes
- [../ARCHITECTURE.md](../ARCHITECTURE.md) when adapters or layers are added
- active execution plans under `docs/plans/active/`

`make verify` must remain local and deterministic. Live sensor tests should use
fixtures or fakes in CI, with manual capture smoke checks documented separately.
The current real-adapter fixtures are
`data/capture/macos_frontmost_snapshot.json` and
`data/capture/browser_active_tab_snapshot.json`; future real adapters must add
equivalent fixtures before they are considered harness-ready. The session
timeline fixture is `data/capture/fake_session_observations.json`.
