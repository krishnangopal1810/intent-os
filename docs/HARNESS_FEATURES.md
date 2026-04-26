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
