# Architecture

IntentOS currently ships a local-first Python CLI MVP for generic multi-app
activity classification, plus the original YouTube-specific slice and a
dogfood beta runtime. The beta adds a standard-library Python localhost
service, SQLite persistence, a native macOS background recorder, an optional
Chrome extension bridge shell, service-backed UI mode, and a Swift menu bar
wrapper. The core product and verification path use
only local runtime dependencies so a fresh checkout can run deterministic
checks without network installation.

## Architecture Principles

- Prefer a small, complete vertical slice over a broad skeleton.
- Keep boundaries explicit and documented.
- Parse and validate data at system boundaries.
- Keep generated or derived artifacts reproducible.
- Choose tooling that Codex can run locally in this repository.
- Add mechanical checks for architectural rules once code exists.

## Current Stack

- Language: Python 3
- Runtime: CLI plus local static UI shell and local beta HTTP service
- Dependencies: Python standard library only
- Input: local JSON fixtures for YouTube and generic activity events
- Output: CLI narratives, JSON reports, local UI shell, SQLite beta database,
  service daily-review APIs, and checked-in UI screenshot evidence

Live capture work emits raw observations into the generic `ActivityEvent`
boundary. The current real adapter captures frontmost macOS app/window metadata
manually and enriches active browser tab metadata when local Automation
permission allows it. Sessionization and background timeline shaping are
handled above the adapter layer by repeatedly sampling metadata, applying
privacy policy, and merging adjacent equivalent `ActivityEvent` rows.

## Current Layers

The current local-first slice keeps these concerns separate:

- `intentos/activity.py`: generic `ActivityEvent` domain type and boundary
  validation.
- `intentos/classifier.py`: generic behavior taxonomy classifier.
- `intentos/reporting.py`: generic aggregate behavior reporting.
- `intentos/activity_cli.py`: multi-app activity CLI.
- `intentos/activity_evaluate.py`: labeled multi-app evaluation runner.
- `intentos/beta/store.py`: SQLite schema, retention, raw event persistence,
  settings, runtime status, corrections, and delete-local-data behavior.
- `intentos/beta/db_health.py`: SQLite quick-check, WAL checkpoint, and local
  DB/WAL/SHM file-size helpers used by beta status and reset flows.
- `intentos/beta/review.py`: service-backed daily review generation that reuses
  the existing classifier/reporting pipeline and layers corrections over
  derived labels.
- `intentos/beta/extension.py`: Chrome extension bridge validation and privacy
  filtering for bounded tab metadata.
- `intentos/beta/native_recorder.py`: beta native macOS recorder that samples
  frontmost app/window metadata, uses the existing browser metadata fallback,
  applies privacy filtering through the capture stack, and writes SQLite rows.
- `intentos/beta/permissions.py`: explicit dogfood permission probes, local
  repair actions, and target-specific setup guidance for Accessibility,
  browser Automation, Chrome bridge setup, and diagnostics.
- `intentos/beta/recorder.py`: beta recorder rules for idle and long-gap
  handling before persistence.
- `intentos/beta/service.py`: local `127.0.0.1` HTTP APIs for status, events,
  onboarding, permission checks, daily review, corrections, pause/resume,
  delete-local-data, and browser events.
- `intentos/beta/state.py`: shared status, permission summary, and onboarding
  state derived from SQLite settings and runtime health.
- `intentos/beta_cli.py`: beta service, native recorder, status, fixture
  seeding, fake bridge, and daily-review command wiring.
- `intentos/capture/core.py`: metadata-only capture observation validation and
  conversion to `ActivityEvent`.
- `intentos/capture/browser.py`: browser tab URL/title/domain normalization
  and best-effort active tab capture through local browser automation.
- `intentos/capture/privacy.py`: local privacy policy, exclusion, and redaction
  helpers.
- `intentos/capture/jsonl.py`: captured `ActivityEvent` JSONL persistence.
- `intentos/capture/live.py`: continuous metadata-only background timeline loop
  that writes raw samples, merged timeline events, replay summaries, and status
  artifacts.
- `intentos/capture/live_cli.py`: command wiring for the continuous live
  capture loop.
- `intentos/capture/macos.py`: manual macOS frontmost app/window metadata
  adapter using local System Events through `osascript`.
- `intentos/capture/session.py`: bounded live-session sampling helpers and
  adjacent `ActivityEvent` merge behavior.
- `intentos/capture/report_cli.py`: capture replay report formatting.
- `intentos/capture_cli.py`: fake-sensor normalization and replay CLI.
- `intentos/capture_replay.py`: JSONL replay through the existing behavior
  report.
- `intentos/youtube.py`: domain types, boundary validation, classification,
  aggregation, and report generation for the YouTube-specific slice.
- `intentos/cli.py`: YouTube command line interface.
- `intentos/evaluate.py`: YouTube fixture-based classifier evaluation.
- `data/activity/multi_app_events.json`: generic multi-app sample events.
- `data/activity/evaluation_set.json`: labeled multi-app evaluation set.
- `data/capture/fake_macos_observations.json`: deterministic fake app/window
  capture observations.
- `data/capture/fake_session_observations.json`: deterministic repeated
  session observations for merge, privacy, replay, and UI validation.
- `data/capture/fake_browser_tabs.json`: deterministic browser tab metadata.
- `data/capture/browser_active_tab_snapshot.json`: deterministic live browser
  active-tab fixture.
- `data/capture/macos_frontmost_snapshot.json`: deterministic real-adapter
  stdout fixture for macOS frontmost app/window parsing.
- `data/capture/privacy_policy.json`: local exclusion and text-bounding policy.
- `data/beta/fake_chrome_events.json`: deterministic fake Chrome extension
  bridge events for service, privacy, correction, and UI beta validation.
- `data/youtube/sample_watch_history.json`: deterministic local fixture.
- `data/youtube/evaluation_set.json`: labeled local evaluation set.
- `tests/test_activity_classification.py`: multi-app behavior tests.
- `tests/test_capture_core.py`: fake capture normalization and JSONL tests.
- `tests/test_capture_live.py`: continuous background timeline artifact refresh
  tests.
- `tests/test_capture_browser.py`: browser metadata normalization tests.
- `tests/test_capture_privacy.py`: exclusion and redaction policy tests.
- `tests/test_capture_macos.py`: macOS adapter parsing and permission-error
  tests that do not call live macOS APIs.
- `tests/test_capture_replay.py`: capture replay tests.
- `tests/test_youtube_mvp.py`: product behavior tests.
- `scripts/product/verify.sh`: product verification entry point for
  `make verify`.
- `scripts/product/validate-beta.sh`: deterministic beta API, persistence,
  correction, privacy, delete-data, and UI smoke validation.
- `scripts/product/dogfood-smoke.sh`: real-machine beta smoke that requires
  native recorder row growth, treats Chrome bridge as optional enhancement,
  preserves dogfood data, and writes blocked/pass evidence.
- `scripts/product/package-beta.sh`: local ad-hoc signed Swift menu bar app
  package builder with graceful skip behavior when macOS Swift tools are
  unavailable.
- `scripts/product/install-beta-app.sh`: local install/open helper for the
  dogfood menu bar app.
- `scripts/product/package-extension.sh`: internal Chrome extension package
  helper for dogfood bridge artifacts.
- `scripts/product/dev.sh`: local artifact server for inspecting CLI output.
- `scripts/product/start-ui.sh`: local static UI server for generated runtime
  artifacts.
- `scripts/product/validate-ui.sh`: UI smoke validator for local artifacts and
  optional headless browser render evidence.
- `scripts/product/render-ui-check.py`: rendered screenshot and DOM-probe
  checker used when Chrome or Chromium is available.
- `scripts/product/update-ui-screenshot.sh`: local browser screenshot
  generator for checked-in visual evidence.
- `scripts/product/check-ui-screenshot.sh`: screenshot manifest freshness gate
  used by UI validation and `make verify`.
- `docs/HARNESS_FEATURES.md`: harness contracts for upcoming automated source,
  parser-fixture, narrative, fallback-capture, model, and UI automation slices.
- `docs/product/imports.md`: fixture/parser contract for local records,
  browser history shapes, and ChatGPT exports; manual import is not the
  preferred user-facing product path.
- `web/`: static local UI shell that reads generated JSON artifacts.
- `extension/chrome/`: Chrome MV3 bridge shell for bounded tab metadata only.
- `macos/IntentOSBeta/`: native menu bar wrapper source and Info.plist for the
  local dogfood app bundle.

## Dependency Rules

- Inner domain logic should not depend on UI or runtime wiring.
- External services should enter through explicit adapters.
- Shared utilities should be small, tested, and documented.
- Cross-cutting concerns such as auth, telemetry, and configuration should have
  one obvious entry point.
- Live capture adapters should normalize into `ActivityEvent`; they should not
  own classification rules.
- Beta corrections must layer on top of raw `ActivityEvent` rows and derived
  classifications; they must not overwrite raw persisted events.
- Capture adapters should be metadata-first. ScreenCaptureKit and Vision OCR
  are fallbacks for low-confidence events, not default sensors.
- Local model inference should be a second-pass classifier behind an explicit
  boundary; core reporting should not depend on a model being installed.

## Data Flow

```text
fixtures or future source adapters
  -> ActivityEvent boundary validation
  -> optional local SQLite persistence for beta runtime
  -> deterministic classifier
  -> optional local model second pass
  -> aggregate reporting
  -> CLI/runtime artifacts
  -> evaluation and CI gates
```

The YouTube-specific path remains available as a domain fixture and regression
suite, but new product surfaces should prefer the generic `ActivityEvent`
pipeline.

## Long-Term Architecture

The long-term architecture diagram lives in
[architecture/long-term-plan.md](architecture/long-term-plan.md). It maps the
planned end state across local capture/import sources, privacy controls,
`ActivityEvent` normalization, rules-first classification, optional local model
second-pass inference, behavior narratives, UI/CLI surfaces, diagnostics, and
future action controls.

The machine-readable source is
[architecture/long-term-plan.json](architecture/long-term-plan.json). The
harness validates that graph through
`scripts/harness/check-architecture-plan.py`, which is called by
`make harness-check` and therefore by `make verify`. Future feature plans
should update the graph when they add, remove, or change a roadmap node,
artifact contract, or verification gate.

## Current Decisions

- The MVP uses deterministic, inspectable classification rules instead of a
  model. This is intentional: it gives Codex and reviewers a visible baseline
  for labels, confidence, uncertainty, and aggregation before a local model is
  introduced.
- The first interface is now a local static UI shell backed by generated JSON
  artifacts. Checked-in screenshot evidence is guarded by a source manifest;
  richer DOM automation is deferred until the UI becomes interactive enough to
  justify it.
- The classifier preserves uncertainty with an `unknown` label when metadata is
  sparse or cue scores are too close.
- Generic activity classification is now the preferred product path. YouTube is
  still supported as a concrete domain-specific path and fixture.
- The first capture implementation uses fake metadata fixtures in CI and a
  manual macOS frontmost app/window adapter with best-effort browser tab
  enrichment for local smoke tests. ScreenCaptureKit, Vision OCR, and model
  inference come later when metadata-only capture leaves meaningful gaps.

## Mechanical Enforcement

`scripts/harness/lint.py` enforces the current layer map, import boundaries,
basic file-size limits, generated-file hygiene, active-plan hygiene, quality
scorecard rows, and labeled evaluation set coverage. Add new rules there when a
review finding or repeated mistake should become agent-visible policy.

As modules grow, promote these expectations from docs into lints:

- source adapters may emit observations but must not classify behavior
- event-boundary modules may parse and validate but must not own reporting
- classifiers may depend on taxonomy and event types but not live sensors
- reports may depend on classifier output but not raw capture adapters
- UI/runtime wiring may orchestrate lower layers but should not bypass privacy
  filtering

## Next Architecture Work

- Add real user import paths on top of the `ActivityEvent` boundary before
  adding heavier sensors.
- Keep each next feature aligned with `docs/HARNESS_FEATURES.md` so new
  adapters, parsers, local models, and UI flows have deterministic fixtures and
  verification before relying on live data.
- Expand lint rules to enforce source adapter -> event -> classifier -> report
  direction when those modules exist.
- Expand cleanup/audit checks for stale plans, stale docs, fixture drift, and
  quality scorecard gaps as the documentation surface grows.
- Add a local model boundary only after fixture evaluation shows deterministic
  rules are insufficient.
