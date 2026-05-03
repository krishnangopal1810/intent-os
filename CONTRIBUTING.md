# Contributing To IntentOS

IntentOS is a local-first behavior intelligence project. Contributions should
make the product more useful without weakening privacy, verification, or repo
legibility.

## Before You Start

Read:

1. [README.md](README.md)
2. [docs/README.md](docs/README.md)
3. [docs/product/BRIEF.md](docs/product/BRIEF.md)
4. [docs/product/TAXONOMY.md](docs/product/TAXONOMY.md)
5. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

For capture, local model, UI, or runtime changes, also read the relevant docs
linked from [AGENTS.md](AGENTS.md).

## Contribution Rules

- Keep changes scoped to one clear product or harness improvement.
- Preserve local-first behavior: no cloud storage, cloud inference, telemetry,
  keylogging, page bodies, cookies, tokens, or raw screenshot retention.
- Add deterministic fixtures or tests for behavior changes.
- Update durable docs when product behavior, architecture, workflow, or known
  risks change.
- Do not hide important context in issue or PR comments only.
- Prefer boring, inspectable technology unless the product requirement clearly
  needs something else.

## Development Loop

Run the full gate before handoff when possible:

```sh
make verify
```

Useful narrower commands:

```sh
make dev
make validate-ui
make validate-beta
make harness-check
make harness-lint
```

For UI changes that affect rendered output, refresh screenshot evidence:

```sh
make update-ui-screenshot
```

For live macOS capture diagnostics, use:

```sh
make observe-live
make observe-session
make dev-live
```

These live commands depend on local macOS permissions and current user state,
so they are not CI gates.

## Pull Requests

A good PR includes:

- what changed and why
- verification run, or a clear reason it could not run
- docs updates for product or architecture changes
- screenshots or UI evidence when rendered behavior changes
- explicit notes for privacy-sensitive capture or inference changes

Small complete slices are preferred over broad skeletons.
