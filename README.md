# intent-os

IntentOS is a local-first personal behavior intelligence system. It is not a
time tracker. It classifies digital activity by behavioral intent so a user can
understand whether time was spent on deep work, learning, communication, admin,
passive consumption, entertainment, or unknown activity.

This repository is also an agent-first product harness. Codex should be able to
read the docs, choose the next scoped plan, implement the slice, verify it, and,
when explicitly asked, open, review, and merge a PR once checks pass.

## Current Product Surface

- Generic multi-app `ActivityEvent` classification.
- YouTube-specific fixture classification from the first MVP slice.
- Deterministic local fixtures and labeled evaluation sets.
- CLI reports and JSON reports.
- Local UI shell served from generated runtime artifacts.
- Metadata-only fake-sensor capture normalization and replay.
- Manual metadata-only macOS frontmost app/window capture.
- Harness checks, architecture linting, cleanup checks, runtime artifacts, and
  CI running `make verify`.
- Live-capture and on-device inference specs for the next macOS slices.

The first real live sensor is intentionally narrow: it samples the current
frontmost macOS app/window through local System Events metadata and writes
`ActivityEvent` JSONL. Browser tab metadata, screenshot capture, OCR, local
model inference, and UI/browser validation remain future extensions after the
metadata path is reliable.

## Start Here

- [AGENTS.md](./AGENTS.md): short map Codex should read first.
- [docs/README.md](./docs/README.md): full repository knowledge index.
- [docs/product/BRIEF.md](./docs/product/BRIEF.md): product source of truth.
- [docs/product/TAXONOMY.md](./docs/product/TAXONOMY.md): behavior labels and
  classification rules of thumb.
- [docs/product/live-capture.md](./docs/product/live-capture.md): macOS capture
  strategy and privacy defaults.
- [docs/product/on-device-inference.md](./docs/product/on-device-inference.md):
  local model and rules-first inference strategy.
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md): current layers and dependency
  rules.
- [docs/HARNESS_AUDIT.md](./docs/HARNESS_AUDIT.md): status against the OpenAI
  Harness Engineering model.
- [docs/NEXT_STEPS.md](./docs/NEXT_STEPS.md): recommended next slices.
- [docs/plans/README.md](./docs/plans/README.md): execution plan workflow.

## Common Commands

```sh
make harness-check
make harness-lint
make harness-status
make cleanup-check
make verify
make dev
make app-status
make diagnose
make validate-ui
make observe
make observe-live
```

Run the current product:

```sh
python3 -m intentos.capture_cli normalize-observations data/capture/fake_macos_observations.json --browser-tabs data/capture/fake_browser_tabs.json --output .harness/runtime/artifacts/capture-events.jsonl
python3 -m intentos.capture_cli replay .harness/runtime/artifacts/capture-events.jsonl
python3 -m intentos.capture_cli capture-macos --duration-seconds 5 --output .harness/runtime/artifacts/live-capture-events.jsonl
python3 -m intentos.activity_cli data/activity/multi_app_events.json
python3 -m intentos.activity_evaluate data/activity/evaluation_set.json --min-accuracy 85
python3 -m intentos.cli data/youtube/sample_watch_history.json
```

`make observe-live` runs the manual macOS frontmost app/window smoke loop,
writes `.harness/runtime/artifacts/live-capture-events.jsonl`, replays it
through the classifier, and writes `.harness/runtime/logs/live-capture.log`.
It may require Accessibility and Automation permissions for the Codex host app
or terminal. CI uses deterministic fixtures instead of live macOS state.

`make dev` serves the UI URL recorded in `.harness/runtime/app.env`.
`make diagnose` prints app state, structured runtime events, UI validation
evidence, and recent logs.

Create a scoped execution plan with:

```sh
scripts/harness/new-plan.sh first-product-slice
```

Then fill in the generated plan under `docs/plans/active/` and prompt Codex to
implement that plan end to end.

`make verify` is the main merge gate. It runs harness checks, structural linting,
unit tests, YouTube fixture evaluation, multi-app fixture evaluation, and CLI
smoke checks.

## Next Work

See [docs/NEXT_STEPS.md](./docs/NEXT_STEPS.md). The recommended next slice is
the metadata-only browser tab capture adapter.
