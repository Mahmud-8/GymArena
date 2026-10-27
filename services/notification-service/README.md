# Notifications

Owner: Ahmed Ebrahim ([@AhmedEbrahem25](https://github.com/AhmedEbrahem25))

Requirements: FR-07, FR-08

Schedule and cancel expiry reminders, prevent duplicates, deliver approved follow-up and retain provider acknowledgements.

Assigned branch: `feature/notification-service`

The Docker foundation now runs this service as its own FastAPI process. It exposes `/`, `/health/live`, `/health/ready` and `/openapi.json`. Readiness checks the owned PostgreSQL database, expected tables and views.

The `INotifications` business operations remain planned. No registration, scoring, tracking, messaging or hardware behavior is implied by a healthy foundation.

- Entry point: `api/routes.py`
- Build: `Dockerfile` with dependency and non-root runtime stages
- Initial schema: `db/001_initial.sql`
- Local URL: http://localhost:8104
- Start all services from the repository root: `docker compose up`

See [Docker setup](../../docs/docker-foundation.md) for checks and data ownership.
