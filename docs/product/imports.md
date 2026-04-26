# Local Import Paths

This spec covers local user-data import features that should land before
heavier sensors, OCR, or model-backed classification. All import paths must
normalize into `ActivityEvent` and reuse the existing classifier, reporting,
privacy policy, JSONL persistence, and UI artifact flow.

## Goals

- Let a user classify historical activity without always-on capture.
- Expand realistic evaluation examples before adding OCR or local models.
- Keep all parsing, validation, classification, and reporting local.

## Manual CSV/JSON Import

The first import slice should accept a small documented CSV or JSON schema with
these fields:

- `started_at`: ISO-8601 timestamp.
- `duration_seconds`: positive integer seconds.
- `source_app`: app or source name.
- `surface`: domain, workspace, channel, app surface, or explicit source type.
- `title`: visible title, page title, document title, or conversation title.
- `url`: optional HTTP or HTTPS URL.
- `metadata`: optional object for bounded source-specific fields.

The importer must validate every row before writing runtime artifacts. Rows
must already satisfy the `ActivityEvent` boundary shape that replay reads from
JSONL: non-empty text for `started_at`, `source_app`, `surface`, and `title`;
a positive integer `duration_seconds`; optional text for `url`; and an optional
object for `metadata`. Invalid rows should fail with actionable errors and
should not write partial misleading reports. Privacy exclusions and redaction
apply before imported records are persisted.

Expected harness artifacts:

- `.harness/runtime/artifacts/import-events.jsonl`
- `.harness/runtime/artifacts/import-summary.txt`
- `.harness/runtime/artifacts/import-summary.json`
- `.harness/runtime/artifacts/import-validation.json`

## Browser History Import

Browser history import is a later slice. It should read local copied/exported
history data, not live browser profiles in CI. Fixture coverage must include
Chrome, Safari, and Arc-shaped records or copied databases, plus excluded
private/authentication/location-bearing URLs.

The importer should produce `ActivityEvent` rows with bounded title, URL,
domain, browser name, and source provenance. It must not retain full page
bodies, cookies, session tokens, or profile databases in runtime artifacts.

## ChatGPT Export Parser

The ChatGPT export parser should use local exported files or deterministic
fixtures. It should classify conversation intent from bounded metadata and
short redacted excerpts, not full conversations by default.

Fixture coverage should include coding, learning, admin drafting,
communication, entertainment, and ambiguous conversations that preserve
`unknown`.

## Privacy Rules

- Imports are local-only.
- No cloud inference or cloud storage.
- No cookies, tokens, passwords, or browser session data in fixtures or runtime
  artifacts.
- Sensitive domains, apps, URLs, and titles must pass through the same privacy
  policy used by capture.
- Model prompts or conversation excerpts must not be persisted unless an
  explicit local debug mode is added later.

## Verification

Every import slice must add:

- Deterministic input fixtures.
- Unit tests for valid conversion, validation errors, privacy exclusions, and
  replay.
- A CLI smoke command in `scripts/product/verify.sh`.
- Structured runtime events for row counts, exclusions, output paths, and
  replay status.
- UI validation and refreshed screenshot evidence when imported artifacts
  change visible behavior.
