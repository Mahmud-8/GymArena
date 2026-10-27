# Face Recognition

Owner: Mohamed Soliman ([@xchan404](https://github.com/xchan404))

Requirements: FR-11, FR-12

Own enrollment consent and face references. Suggest matches, obtain confirmation and offer member-code or staff fallback.

Assigned branch: `feature/recognition-service`

The Docker foundation now runs this service as its own FastAPI process. It exposes `/`, `/health/live`, `/health/ready` and `/openapi.json`. Readiness checks the owned PostgreSQL database, expected tables and views.

The `IRecognition` business operations remain planned. No registration, scoring, tracking, messaging or hardware behavior is implied by a healthy foundation.

- Entry point: `api/routes.py`
- Build: `Dockerfile` with dependency and non-root runtime stages
- Initial schema: `db/001_initial.sql`
- Local URL: http://localhost:8106
- Start all services from the repository root: `docker compose up`

See [Docker setup](../../docs/docker-foundation.md) for checks and data ownership.
