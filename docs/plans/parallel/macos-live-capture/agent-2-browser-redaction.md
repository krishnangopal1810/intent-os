# Agent 2: Browser Metadata and Redaction Policy

## Objective

Build the browser context and privacy policy layer for metadata-only capture.
This agent owns URL/title normalization, app/domain/window exclusions, and safe
text bounding so future capture does not leak sensitive user content by default.

## Owned Files

- `intentos/capture/browser.py`
- `intentos/capture/privacy.py`
- `data/capture/fake_browser_tabs.json`
- `data/capture/privacy_policy.json`
- `tests/test_capture_browser.py`
- `tests/test_capture_privacy.py`

## Inputs

- Read [TRACKER.md](TRACKER.md) first.
- Read [../../../product/live-capture.md](../../../product/live-capture.md).
- Read [../../../product/on-device-inference.md](../../../product/on-device-inference.md).
- Read [../../../SECURITY.md](../../../SECURITY.md).
- Treat Agent 1's raw observation/event boundary as the integration point.

## Required Implementation

- Define a browser tab metadata object with browser name, bundle ID, URL,
  title, domain, and source.
- Add URL/domain normalization with standard-library parsing only.
- Add privacy policy loading from local JSON.
- Support exclusions by app name, bundle ID, domain, URL substring, and window
  title substring.
- Add bounded visible-text handling with a small default character limit.
- Ensure private/incognito indicators cause events to be excluded or reduced to
  coarse app-level metadata.
- Ensure banking, tax, payment, health, password, and authentication cues are
  excluded or reduced to metadata-only capture.
- Add fake browser tab fixtures covering YouTube, ChatGPT, LinkedIn feed,
  Google Docs, income tax, private browsing, and an unknown browser page.
- Add tests for domain parsing, exclusion matching, redaction, private browsing,
  and sensitive-site handling.

## Out of Scope

- Live browser automation or AppleScript.
- JSONL writing.
- Replay CLI.
- Classifier/reporting changes.
- Runtime harness commands.
- Any raw screenshot, OCR, keylogging, clipboard, or network behavior.

## Verification

Run:

```sh
python3 -m unittest tests.test_capture_browser tests.test_capture_privacy
make verify
```

If integration with Agent 1's package path is not available yet, use local tests
that avoid importing Agent 1's files and describe the expected integration in
the handoff.

## Handoff

Return:

- files changed
- privacy policy schema
- redaction/exclusion behavior
- verification output
- any integration assumptions Agent 1 or Agent 3 must honor
