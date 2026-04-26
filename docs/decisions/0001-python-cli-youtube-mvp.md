# Decision: Python CLI for YouTube MVP

Date: 2026-04-26
Status: Accepted

## Context

The first IntentOS slice needs to classify local YouTube watch activity as
learning, entertainment, or unknown. It must run from a fresh checkout and make
`make verify` pass without depending on cloud services or package installation.

## Decision

Use a Python standard-library CLI for the first MVP. Keep the classifier
deterministic and inspectable, with visible cue scores, confidence, and reasons.

## Consequences

- The MVP can run locally with `python3 -m intentos.cli`.
- `make verify` can execute product tests and fixture evaluation without
  dependency installation.
- The classifier is simple and transparent, but it is not yet a high-accuracy
  semantic model.
- A future local model can replace the rule engine behind the same
  classification boundary.

## Alternatives Considered

- Browser extension first: deferred because distribution and browser permission
  work would slow the first local product slice.
- Cloud LLM classification: rejected for the default path because privacy and
  on-device behavior are core product constraints.
- Frontend first: deferred because the key MVP risk is semantic classification,
  not dashboard presentation.
