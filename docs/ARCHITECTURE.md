# Architecture

No product architecture has been selected yet.

## Architecture Principles

- Prefer a small, complete vertical slice over a broad skeleton.
- Keep boundaries explicit and documented.
- Parse and validate data at system boundaries.
- Keep generated or derived artifacts reproducible.
- Choose tooling that Codex can run locally in this repository.
- Add mechanical checks for architectural rules once code exists.

## Expected Layers

The exact stack is still TBD, but product code should keep these concerns
separate:

- Product domain types and validation
- Persistence and external integrations
- Application services and workflows
- Runtime wiring
- UI or interface layer
- Test and observability utilities

## Dependency Rules

- Inner domain logic should not depend on UI or runtime wiring.
- External services should enter through explicit adapters.
- Shared utilities should be small, tested, and documented.
- Cross-cutting concerns such as auth, telemetry, and configuration should have
  one obvious entry point.

## Current Decisions

No architecture decisions have been made yet. Add durable decisions under
`docs/decisions/` as the product takes shape.
