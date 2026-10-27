# Eight service runtime

The approved PM1 Part A container design uses eight services and the assignment requests a multi-stage Dockerfile for each service. The earlier README proposed one combined API. This foundation replaces that deployment plan with eight separate FastAPI processes in one monorepo.

One PostgreSQL host serves eight logical databases. Each service has its own login and credential volume. Public database connection privileges are revoked on each owned database. No application service receives the administrator or another service's credential file. Only the database initialization container sees all roles.

Business dependencies stay at the API boundary. They are listed in service metadata as planned contracts; readiness depends on the owning database, avoiding a startup cycle between Challenge, Session and Scoring. Functional clients, authentication, workers and device adapters are not implemented by this foundation.

This decision changes the runtime deployment, not the functional ownership or the approved diagrams.
