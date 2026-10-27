# Assessment and Challenges

Owner: Mohamed Hegazy ([@mohamed-hegazy1](https://github.com/mohamed-hegazy1))

Requirements: FR-13, FR-14

Record supervised assessments and trainer-approved levels. Version challenge rules and adapt targets within approved bounds.

Assigned branch: `feature/challenge-service`

The Docker foundation now runs this service as its own FastAPI process. It exposes `/`, `/health/live`, `/health/ready` and `/openapi.json`. Readiness checks the owned PostgreSQL database, expected tables and views.

The `IChallenge` business operations remain planned. No registration, scoring, tracking, messaging or hardware behavior is implied by a healthy foundation.

- Entry point: `api/routes.py`
- Build: `Dockerfile` with dependency and non-root runtime stages
- Initial schema: `db/001_initial.sql`
- Local URL: http://localhost:8107
- Start all services from the repository root: `docker compose up`

See [Docker setup](../../docs/docker-foundation.md) for checks and data ownership.
