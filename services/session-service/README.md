# Session Control

Owner: Ahmed Ebrahim ([@AhmedEbrahem25](https://github.com/AhmedEbrahem25))

Requirements: FR-05, FR-06

Own participant positions, the immutable challenge snapshot, the common active timer, joint recovery and finalized session outcomes.

Assigned branch: `feature/session-service`

The Docker foundation now runs this service as its own FastAPI process. It exposes `/`, `/health/live`, `/health/ready` and `/openapi.json`. Readiness checks the owned PostgreSQL database, expected tables and views.

The `ISessionControl` business operations remain planned. No registration, scoring, tracking, messaging or hardware behavior is implied by a healthy foundation.

- Entry point: `api/routes.py`
- Build: `Dockerfile` with dependency and non-root runtime stages
- Initial schema: `db/001_initial.sql`
- Local URL: http://localhost:8103
- Start all services from the repository root: `docker compose up`

See [Docker setup](../../docs/docker-foundation.md) for checks and data ownership.
