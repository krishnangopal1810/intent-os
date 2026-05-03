# IntentOS

<p align="center">
  <strong>The private daily review for your digital life.</strong>
</p>

<p align="center">
  IntentOS turns local Mac activity metadata into behavior intelligence:
  deep work, learning, admin, communication, active creation,
  passive consumption, entertainment, and the unknowns worth reviewing.
</p>

<p align="center">
  <a href=".github/workflows/verify.yml"><img alt="verify" src="https://img.shields.io/badge/verify-make%20verify-0f766e"></a>
  <img alt="runtime" src="https://img.shields.io/badge/runtime-local--only-111827">
  <img alt="privacy" src="https://img.shields.io/badge/privacy-metadata--only-334155">
  <img alt="status" src="https://img.shields.io/badge/status-macOS%20source%20beta-b45309">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-blue">
</p>

<p align="center">
  <a href="#try-it">Try it</a>
  ·
  <a href="#privacy-contract">Privacy</a>
  ·
  <a href="#architecture">Architecture</a>
  ·
  <a href="#command-reference">Commands</a>
  ·
  <a href="#start-here-if-you-are-codex">Codex handoff</a>
</p>

![IntentOS private daily review dashboard](docs/assets/screenshots/intent-os-ui.png)

## The Idea

Screen Time can tell you which apps were open. IntentOS is being built to tell
you what that time meant.

It is not another timer, blocker, or cloud productivity dashboard. It is a
local-first behavior layer for answering one uncomfortable question:

> Was my attention aligned with what I actually care about?

The current repo is a source-based macOS beta. It is already runnable,
inspectable, fixture-backed, service-backed, and privacy-constrained. It is not
yet a polished public installer. It is reasonable for trusted Mac friends who
are comfortable running a source beta and granting local permissions; it is not
ready for broad nontechnical distribution.

## Why This Should Exist

App names are too blunt. The same surface can represent completely different
intent.

| Surface | IntentOS tries to distinguish |
| --- | --- |
| Browser | Research, taxes, documentation, shopping, feed loops, lectures. |
| ChatGPT | Debugging, learning, admin drafting, planning, casual entertainment. |
| Slack or WhatsApp | Coordination, relationship maintenance, reactive shallow work. |
| Editor or writing app | Deep creation, light edits, review, stalled context switching. |
| YouTube | Learning, passive consumption, entertainment, background noise. |

IntentOS keeps raw local events separate from user corrections, so the product
can learn from review without rewriting history.

## What Works Today

IntentOS currently ships a local macOS source beta with:

| Capability | Current status |
| --- | --- |
| Native macOS capture | Frontmost app/window metadata through a local recorder. |
| Browser enrichment | Optional title, URL, and domain when local permissions allow it. |
| Chrome bridge | Optional MV3 metadata bridge for richer dogfood testing. |
| Local persistence | SQLite under `.harness/runtime/beta/` with 30-day retention. |
| Behavior classification | Deterministic, inspectable rules over the product taxonomy. |
| Daily review UI | Service-backed dashboard plus fixture-backed demo mode. |
| Corrections | Local relabel overlays that do not mutate raw events. |
| User controls | Pause, resume, diagnostics, permission guidance, delete local data. |
| Packaging | Local ad-hoc Swift menu bar app build/install path. |
| Verification | `make verify`, UI screenshot freshness, beta validation, fixtures. |

Manual imports remain useful for fixtures and regression tests, but the beta
path is live and automated. No CSV export is required before the product can
show value.

Manual metadata-only macOS diagnostics are available through `make observe-live`,
`make observe-session`, and `make dev-live` when you want to inspect current
local activity outside the deterministic CI path.

## Try It

Requirements:

- Python 3 and `make` for the deterministic demo.
- macOS plus Accessibility permission for live capture and the menu bar beta.

Run the fixture-backed product in one command:

```sh
make dev
```

Open the URL printed as `INTENTOS_APP_URL`.

Run the live local beta:

```sh
make beta-dev
make beta-status
```

Open the URL printed as `INTENTOS_BETA_UI_URL`.

Stop the beta runtime:

```sh
make beta-stop
```

Build and install the local menu bar app:

```sh
make package-beta
make install-beta-app
```

For trusted friend testing, start with the menu bar app or `make beta-dev`,
then use `Run Permission Check` from the IntentOS menu and inspect
`make beta-status` if capture looks stuck. The Chrome bridge is optional for
the first test pass; native recorder capture is the primary beta path.

Run the full local gate:

```sh
make verify
```

## Privacy Contract

IntentOS is intentionally boring about privacy.

| Rule | Current behavior |
| --- | --- |
| Local first | Services bind to `127.0.0.1`; runtime data stays under `.harness/runtime/`. |
| Metadata only | App name, window title, bounded title/URL/domain metadata. |
| No screenshots | Raw screenshots are not captured or retained. |
| No keylogging | Keyboard input is never captured. |
| No page bodies | Page text, cookies, tokens, and bodies are rejected. |
| User control | Pause/resume and delete-local-data are built into the beta. |
| Optional Chrome | Native recorder is primary; Chrome bridge is enrichment only. |

See [docs/SECURITY.md](docs/SECURITY.md) for the full security baseline.

## How It Works

```mermaid
flowchart LR
  A["macOS app/window metadata"] --> B["ActivityEvent"]
  C["optional browser URL/title"] --> B
  D["optional Chrome bridge"] --> B
  B --> E["privacy filter"]
  E --> F["local SQLite or fixture artifacts"]
  F --> G["rules-first classifier"]
  G --> H["daily review"]
  H --> I["local corrections"]
  I --> G
```

The classifier is deliberately rules-first today. Local model inference is
planned only after fixtures show where deterministic rules plateau.

## Behavior Taxonomy

IntentOS classifies activity into a small, inspectable set:

| Label | Meaning |
| --- | --- |
| `deep_work` | Focused coding, writing, analysis, or problem solving. |
| `learning` | Intentional educational or skill-building activity. |
| `communication` | Messages, calls, coordination, relationship maintenance. |
| `admin` | Taxes, billing, banking, forms, travel, account work. |
| `passive_consumption` | Feed loops, low-intent browsing, clips, recommendation drift. |
| `active_creation` | Creating personal or public output outside core work. |
| `entertainment` | Deliberate leisure, games, shows, comedy, sports, music. |
| `unknown` | Sparse or conflicting evidence. |

The source of truth is [docs/product/TAXONOMY.md](docs/product/TAXONOMY.md).

## What It Is Not

- Not a Chrome-only extension.
- Not a keylogger.
- Not a screenshot recorder.
- Not a cloud analytics product.
- Not a public installer yet.
- Not an automation agent or blocker in the current beta.

## Why Star It

Star this repo if you care about any of these:

- a privacy-first alternative to app-name productivity tracking
- local semantic classification of real digital behavior
- macOS capture that starts with metadata instead of invasive sensors
- an agent-readable product harness with docs, fixtures, screenshots, and CI
- a practical path from daily review to future local intent intelligence

## Architecture

| Layer | Purpose |
| --- | --- |
| `intentos/activity.py` | Generic `ActivityEvent` boundary. |
| `intentos/classifier.py` | Rules-first behavior classifier. |
| `intentos/reporting.py` | Aggregate behavior summaries. |
| `intentos/capture/` | macOS, browser, privacy, session, and replay adapters. |
| `intentos/beta/` | SQLite store, service APIs, recorder, status, corrections. |
| `web/` | Local daily review dashboard. |
| `macos/IntentOSBeta/` | Native menu bar wrapper. |
| `extension/chrome/` | Optional MV3 Chrome metadata bridge. |
| `scripts/harness/` | Runtime, validation, linting, screenshot, and diagnostics. |

The canonical architecture doc is
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Command Reference

| Goal | Command |
| --- | --- |
| Run all gates | `make verify` |
| Open fixture UI | `make dev` |
| Capture a fresh live UI session | `make dev-live` |
| Observe one live macOS sample | `make observe-live` |
| Observe a bounded live session | `make observe-session` |
| Run real beta | `make beta-dev` |
| Inspect beta health | `make beta-status` |
| Stop beta | `make beta-stop` |
| Validate beta deterministically | `make validate-beta` |
| Package app | `make package-beta` |
| Install app | `make install-beta-app` |
| Package Chrome bridge | `make package-extension` |
| Run real local capture smoke | `make dogfood-smoke` |
| Refresh screenshot evidence | `make update-ui-screenshot` |
| Diagnose runtime | `make diagnose` |

More runtime contracts live in [docs/APP_RUNTIME.md](docs/APP_RUNTIME.md).

## Roadmap

The next slices are deliberately practical:

- fresh beta install smoke on a clean macOS user
- optional Chrome bridge connected/posting-events smoke
- sharper first-run permission recovery
- richer daily behavior narratives
- local model second-pass classification after rules plateau
- low-confidence visible-text or OCR fallback only if metadata is insufficient

See [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) for the maintained roadmap.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. The short
version:

- keep changes scoped to a product slice
- add or update verification when behavior changes
- preserve the local-only privacy contract
- run `make verify` before handoff whenever possible

Issues are welcome for bugs, product ideas, local beta feedback, and
classification examples that should become fixtures.

## Start Here If You Are Codex

Read these in order:

1. [AGENTS.md](AGENTS.md)
2. [docs/README.md](docs/README.md)
3. [docs/product/BRIEF.md](docs/product/BRIEF.md)
4. [docs/product/TAXONOMY.md](docs/product/TAXONOMY.md)
5. [docs/product/live-capture.md](docs/product/live-capture.md)
6. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
7. [docs/APP_RUNTIME.md](docs/APP_RUNTIME.md)
8. [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md)

Then make the smallest complete product slice and run:

```sh
make verify
```

## License

IntentOS is released under the [MIT License](LICENSE).
