# UI Screenshots

This directory contains checked-in visual evidence for the local IntentOS UI.

- `intent-os-ui.png`: current fixture-backed UI screenshot.
- `intent-os-ui.json`: source manifest and screenshot metadata.

Run `make update-ui-screenshot` after changing `web/`, UI fixture inputs, or
the reporting code that feeds the UI. `make validate-ui` and `make verify`
check the manifest and PNG content so stale or blank screenshots fail fast.
