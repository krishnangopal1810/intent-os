# Security

No product data model exists yet. Use this baseline for future implementation.

## Baseline Rules

- Do not commit secrets.
- Keep `.env` files local.
- Validate all external input at boundaries.
- Treat user data as private by default.
- Prefer least-privilege tokens and service permissions.
- Document new data stores, credentials, and external integrations.

## Required Before Real Users

- Authentication and authorization model
- Data retention policy
- Secret management approach
- Backup and recovery approach
- Abuse and rate-limit strategy for public endpoints
