# Security

The current MVP processes local YouTube watch-history fixture data only. It does
not use cloud storage, cloud inference, browser APIs, or external network calls.

## Baseline Rules

- Do not commit secrets.
- Keep `.env` files local.
- Validate all external input at boundaries.
- Treat user data as private by default.
- Prefer least-privilege tokens and service permissions.
- Document new data stores, credentials, and external integrations.

## Current Data Handling

- Input data is read from a local JSON file.
- Product verification uses deterministic fixture data under `data/youtube/`.
- Runtime artifacts are written under `.harness/runtime/`, which is ignored by
  git.
- No secrets, tokens, accounts, or personal browser history are required for the
  MVP.

## Required Before Real Users

- Authentication and authorization model
- Data retention policy
- Secret management approach
- Backup and recovery approach
- Abuse and rate-limit strategy for public endpoints
