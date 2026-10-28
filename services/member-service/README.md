# Member Profiles and Measurements

Owner: Mohamed Soliman ([@xchan404](https://github.com/xchan404))

Requirements: FR-09, FR-10

Own member IDs, profile fields, member codes and confirmed timestamped scale readings.

Assigned branch: `feature/member-service`

The Docker foundation now runs this service as its own FastAPI process. It exposes `/`, `/health/live`, `/health/ready` and `/openapi.json`. Readiness checks the owned PostgreSQL database, expected tables and views.

US-17/GYM-17 and US-18/GYM-18 now implement validated registration, reusable
private codes, member confirmation and protected profile correction. The built
React kiosk is at <http://localhost:8105/kiosk/>. Full interface completion,
scale readings, scoring, tracking and messaging remain planned. See
[API contracts and acceptance checks](../../docs/member-registration.md).

- Entry point: `api/routes.py`
- Build: `Dockerfile` with dependency and non-root runtime stages
- Initial schema: `db/001_initial.sql`
- Additive retry-request migration: `db/002_registration_requests.sql`, applied on startup
- Use cases and store port: `application/profiles.py`
- Invariants and profile/event types: `domain/models.py`
- Owned SQL adapter and confirmation: `infrastructure/`
- Local URL: http://localhost:8105
- Start all services from the repository root: `docker compose up`

See [Docker setup](../../docs/docker-foundation.md) for checks and data ownership.
