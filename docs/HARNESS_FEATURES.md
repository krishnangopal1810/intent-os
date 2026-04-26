# Next Feature Harness Contracts

This file defines the harness support future IntentOS slices must add before
their product behavior is considered complete. It is a contract for Codex: each
new feature must be runnable, inspectable, deterministic in CI, and visible in
the local UI when user-facing behavior changes.

## Shared Requirements

Every next feature must preserve these baseline rules:

- Normalize new activity sources into the existing `ActivityEvent` boundary.
- Keep `make verify` deterministic and permission-free.
- Add deterministic fixtures or fakes for every parser, adapter, model, and
  fallback.
- Write runtime artifacts under `.harness/runtime/artifacts/`.
- Emit structured runtime events with stable fields such as `component`,
  `event`, `mode`, `artifact_path`, `duration_ms`, `event_count`, and `status`.
- Apply privacy exclusions and redaction before user-derived records are
  persisted into runtime artifacts.
- Update `docs/APP_RUNTIME.md`, `docs/ARCHITECTURE.md`,
  `docs/RELIABILITY.md`, `docs/QUALITY.md`, and the active execution plan when
  commands, artifacts, permissions, or verification behavior change.
- Refresh checked-in UI screenshot evidence when rendered UI behavior changes.
- Add or update the active plan's `## Harness Impact` section before
  implementation. The section must name runtime artifacts, fixtures/fakes, UI
  validation, diagnostics, privacy/permission constraints, and docs or harness
  checks affected by the slice.

## Universal Use-Case Classes

Classify every future use-case into one or more of these harness impact classes
before implementation. A use-case can say "none" for a class only when that is
explicitly true.

| Use-case class | Harness support required |
| --- | --- |
| New data source or adapter | Boundary validation into `ActivityEvent`, deterministic fixtures or fake adapters, privacy filtering before persistence, replay artifacts, and parser/error tests in `make verify`. |
| New classifier or inference path | Labeled fixtures, deterministic fallback behavior, local-only execution, confidence/unknown handling, and evaluation thresholds in `make verify`. |
| New report or narrative | Generated JSON/text artifacts, deterministic report fixtures, UI loading behavior when visible, and validation that reports are derived from normalized records rather than raw source data. |
| New UI workflow | Local artifact-backed state, `make validate-ui` coverage, checked-in screenshot evidence when rendered output changes, and richer browser automation once clicks, filters, or navigation become core behavior. |
| New permissioned live capability | Manual diagnostic command outside CI, clear permission status, fixture-backed equivalent in `make verify`, local logs, and privacy defaults that fail closed. |
| New long-running process | `make dev` or documented runtime integration, `make app-status`, `make app-stop`, structured events, startup/error logs, and artifact paths in `.harness/runtime/app.env`. |
| New export or integration | Local sample fixtures, redaction rules, deterministic dry-run or fake target, no network dependency in `make verify`, and explicit artifact names for what would be sent or written. |
| New agent workflow or parallel work | Active plan ownership, parallel tracker when multiple agents edit disjoint files, merge order, verification ownership, and harness checks for repeated coordination rules. |

## Feature Matrix

| Feature | Harness support required before completion |
| --- | --- |
| Manual real-data import | Document the CSV/JSON schema, add deterministic import fixtures, add an import smoke command, write import JSONL and report artifacts, log accepted/excluded/error row counts, and include import conversion plus replay in `make verify`. |
| Browser history import | Use copied/exported local browser data or deterministic fixture databases, never live profile reads in CI; add fixtures for Chrome/Safari/Arc shapes, privacy exclusions for private/auth/location URLs, replay artifacts, and parser validation tests. |
| ChatGPT export parser | Use local export fixtures, bound conversation evidence before classification, redact sensitive content, add parser/evaluation fixtures for coding, learning, admin, communication, and entertainment conversations, and verify fallback to `unknown`. |
| Daily behavior narratives | Generate narratives from report artifacts rather than raw source data, add deterministic narrative fixtures, validate the UI rendering path, and refresh screenshot evidence if the dashboard changes. |
| ScreenCaptureKit and Vision OCR fallback | Keep screenshots disabled by default; require Screen Recording permission only for manual diagnostics; do not retain raw frames outside explicit local debug mode; use deterministic frame/OCR fixtures in CI; log permission and fallback reasons. |
| Local model second-pass classifier | Put model calls behind an explicit local boundary, keep deterministic rules as fallback, use a fake or tiny checked-in model path in CI, require labeled evaluation fixtures, and fail closed to `unknown` when unavailable. |
| Richer DOM automation | Extend `make validate-ui` only when interactions exist; record DOM and screenshot evidence, fail on blank renders, horizontal overflow, clipped visible text, and missing workflow states. |

## Runtime Artifact Naming

Use stable artifact names so the UI and diagnostics can discover new sources:

- Manual imports: `import-events.jsonl`, `import-summary.txt`,
  `import-summary.json`, and `import-validation.json`.
- Browser history imports: `browser-history-events.jsonl`,
  `browser-history-summary.json`, and `browser-history-validation.json`.
- ChatGPT exports: `chatgpt-events.jsonl`, `chatgpt-summary.json`, and
  `chatgpt-validation.json`.
- Daily narratives: `daily-narrative-summary.json` and UI validation evidence.
- Fallback capture: fallback-specific JSONL and summary files with
  `screencapturekit` or `ocr` in the name, plus explicit permission status.
- Local model runs: report artifacts must include the model/runtime identifier
  and fallback reason when a model was skipped or unavailable.

## Verification Gates

Future feature PRs should extend these gates instead of relying on manual
judgment:

- `scripts/product/verify.sh` for deterministic product smoke commands.
- `scripts/harness/lint.py` for layer rules, required docs, fixture contracts,
  privacy constraints, and stale-plan checks.
- `scripts/harness/audit.py` for drift checks across roadmap, docs, fixtures,
  screenshot evidence, and quality notes.
- `scripts/product/validate-ui.sh` for any user-visible UI workflow.

Manual commands such as `make observe-live`, `make observe-session`, or future
permission-dependent diagnostics must stay outside CI and must have equivalent
fixture-backed verification.

## Completion Checklist

A future use-case is not harness-ready until all applicable items are true:

- The active plan includes a complete `## Harness Impact` section.
- Runtime commands are documented and write stable artifacts under
  `.harness/runtime/artifacts/`.
- `make verify` covers deterministic fixtures or fakes for the new behavior.
- `make diagnose` or another documented command exposes enough local evidence
  to debug failures without relying on chat history.
- User-visible changes are covered by `make validate-ui` and screenshot
  evidence when the rendered UI changes.
- Privacy, permissions, and local-only constraints are documented and enforced
  before user-derived data is persisted.
