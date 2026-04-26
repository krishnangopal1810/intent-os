# Architecture

IntentOS currently ships a local-first Python CLI MVP for YouTube activity
classification. The implementation uses only the Python standard library so a
fresh checkout can run product verification without dependency installation.

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
- Input: local JSON watch-history fixture
- Output: CLI narrative and JSON report

## Current Layers

The first slice keeps these concerns separate:

- `intentos/youtube.py`: domain types, boundary validation, classification,
  aggregation, and report generation.
- `intentos/cli.py`: command line interface.
- `intentos/evaluate.py`: fixture-based classifier evaluation.
- `data/youtube/sample_watch_history.json`: deterministic local fixture.
- `data/youtube/evaluation_set.json`: labeled local evaluation set.
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

## Current Decisions

- The MVP uses deterministic, inspectable classification rules instead of a
  model. This is intentional: it gives Codex and reviewers a visible baseline
  for labels, confidence, uncertainty, and aggregation before a local model is
  introduced.
- The first interface is a CLI, not a graphical UI. Browser validation remains
  out of scope until a UI exists.
- The classifier preserves uncertainty with an `unknown` label when metadata is
  sparse or cue scores are too close.

## Mechanical Enforcement

`scripts/harness/lint.py` enforces the current layer map, import boundaries,
basic file-size limits, generated-file hygiene, active-plan hygiene, quality
scorecard rows, and labeled evaluation set coverage. Add new rules there when a
review finding or repeated mistake should become agent-visible policy.
