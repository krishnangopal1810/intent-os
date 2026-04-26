# Architecture

IntentOS currently ships a local-first Python CLI MVP for generic multi-app
activity classification, plus the original YouTube-specific slice. The
implementation uses only the Python standard library so a fresh checkout can run
product verification without dependency installation.

## Architecture Principles

- Prefer a small, complete vertical slice over a broad skeleton.
- Keep boundaries explicit and documented.
- Parse and validate data at system boundaries.
- Keep generated or derived artifacts reproducible.
- Choose tooling that Codex can run locally in this repository.
- Add mechanical checks for architectural rules once code exists.

## Current Stack

- Language: Python 3
- Runtime: CLI-first local process
- Dependencies: Python standard library only
- Input: local JSON fixtures for YouTube and generic activity events
- Output: CLI narratives and JSON reports

Future live capture work should add macOS source adapters that emit raw
observations into the generic `ActivityEvent` boundary. Those adapters are not
implemented yet.

## Current Layers

The current local-first slice keeps these concerns separate:

- `intentos/activity.py`: generic `ActivityEvent` domain type and boundary
  validation.
- `intentos/classifier.py`: generic behavior taxonomy classifier.
- `intentos/reporting.py`: generic aggregate behavior reporting.
- `intentos/activity_cli.py`: multi-app activity CLI.
- `intentos/activity_evaluate.py`: labeled multi-app evaluation runner.
- `intentos/capture/core.py`: metadata-only capture observation validation and
  conversion to `ActivityEvent`.
- `intentos/capture/browser.py`: browser tab URL/title/domain normalization.
- `intentos/capture/privacy.py`: local privacy policy, exclusion, and redaction
  helpers.
- `intentos/capture/jsonl.py`: captured `ActivityEvent` JSONL persistence.
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
- `data/capture/fake_browser_tabs.json`: deterministic browser tab metadata.
- `data/capture/privacy_policy.json`: local exclusion and text-bounding policy.
- `data/youtube/sample_watch_history.json`: deterministic local fixture.
- `data/youtube/evaluation_set.json`: labeled local evaluation set.
- `tests/test_activity_classification.py`: multi-app behavior tests.
- `tests/test_capture_core.py`: fake capture normalization and JSONL tests.
- `tests/test_capture_browser.py`: browser metadata normalization tests.
- `tests/test_capture_privacy.py`: exclusion and redaction policy tests.
- `tests/test_capture_replay.py`: capture replay tests.
- `tests/test_youtube_mvp.py`: product behavior tests.
- `scripts/product/verify.sh`: product verification entry point for
  `make verify`.
- `scripts/product/dev.sh`: local artifact server for inspecting CLI output.

## Dependency Rules

- Inner domain logic should not depend on UI or runtime wiring.
- External services should enter through explicit adapters.
- Shared utilities should be small, tested, and documented.
- Cross-cutting concerns such as auth, telemetry, and configuration should have
  one obvious entry point.
- Live capture adapters should normalize into `ActivityEvent`; they should not
  own classification rules.
- Capture adapters should be metadata-first. ScreenCaptureKit and Vision OCR
  are fallbacks for low-confidence events, not default sensors.
- Local model inference should be a second-pass classifier behind an explicit
  boundary; core reporting should not depend on a model being installed.

## Data Flow

```text
fixtures or future source adapters
  -> ActivityEvent boundary validation
  -> deterministic classifier
  -> optional local model second pass
  -> aggregate reporting
  -> CLI/runtime artifacts
  -> evaluation and CI gates
```

The YouTube-specific path remains available as a domain fixture and regression
suite, but new product surfaces should prefer the generic `ActivityEvent`
pipeline.

## Current Decisions

- The MVP uses deterministic, inspectable classification rules instead of a
  model. This is intentional: it gives Codex and reviewers a visible baseline
  for labels, confidence, uncertainty, and aggregation before a local model is
  introduced.
- The first interface is a CLI, not a graphical UI. Browser validation remains
  out of scope until a UI exists.
- The classifier preserves uncertainty with an `unknown` label when metadata is
  sparse or cue scores are too close.
- Generic activity classification is now the preferred product path. YouTube is
  still supported as a concrete domain-specific path and fixture.
- The first capture implementation uses fake metadata fixtures in CI. The first
  live sensor slice should add `NSWorkspace`, Accessibility, and one browser
  metadata adapter behind the same `ActivityEvent` boundary. ScreenCaptureKit,
  Vision OCR, and model inference come later when metadata-only capture leaves
  meaningful gaps.

## Mechanical Enforcement

`scripts/harness/lint.py` enforces the current layer map, import boundaries,
basic file-size limits, generated-file hygiene, active-plan hygiene, quality
scorecard rows, and labeled evaluation set coverage. Add new rules there when a
review finding or repeated mistake should become agent-visible policy.

## Next Architecture Work

- Add adapter layer once live capture implementation begins.
- Expand lint rules to enforce source adapter -> event -> classifier -> report
  direction when those modules exist.
- Add a local model boundary only after fixture evaluation shows deterministic
  rules are insufficient.
