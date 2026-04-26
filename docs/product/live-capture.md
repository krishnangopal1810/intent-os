# Live Activity Capture

This spec defines the intended local capture architecture for IntentOS. The
current implementation includes fake-sensor capture fixtures, a manual
frontmost macOS app/window adapter, and best-effort active browser tab
enrichment. Future work must keep live capture metadata-first,
permission-aware, and reversible.

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

## First Live Slice

Build the first live slice in this order:

1. Active app/window sampler using macOS frontmost app/window metadata.
2. Browser active-tab metadata for one browser.
3. JSONL writer for local `ActivityEvent` records.
4. Replay command that classifies captured JSONL with the existing classifier.
5. Fixture tests for sampler output normalization and redaction.

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
`.harness/runtime/logs/live-capture.log`. The UI prefers the live summary when
it exists and falls back to fixture replay otherwise. If privacy exclusions drop
every row, the live summary is still written with an empty report.

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
equivalent fixtures before they are considered harness-ready.
