# Membership

Owner: Mahmoud Emad ([@Mahmud-8](https://github.com/Mahmud-8))

Requirements: FR-03, FR-04

Own subscription dates, contact numbers and renewal history. Publish committed renewal events.

Assigned branch: `feature/membership-service`

The Docker foundation now runs this service as its own FastAPI process. It exposes `/`, `/health/live`, `/health/ready` and `/openapi.json`. Readiness checks the owned PostgreSQL database, expected tables and views.

The `IMembership` business operations remain planned. No registration, scoring, tracking, messaging or hardware behavior is implied by a healthy foundation.

- Entry point: `api/routes.py`
- Build: `Dockerfile` with dependency and non-root runtime stages
- Initial schema: `db/001_initial.sql`
- Local URL: http://localhost:8102
- Start all services from the repository root: `docker compose up`

See [Docker setup](../../docs/docker-foundation.md) for checks and data ownership.
