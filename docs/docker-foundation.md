# GymArena Docker foundation

Compose supplies eight services and their owned PostgreSQL schemas. Each has its own multi-stage Dockerfile, FastAPI process and database login. Member registration and protected profile correction are now implemented; see [the Member slice](member-registration.md). Workout tracking, scoring, reminders, hardware and monitor animation remain subsequent work. Health alone does not establish functional acceptance.

## Start

Start Docker Desktop with Linux containers, open a terminal in the extracted `GymArena` folder, and run:

```sh
docker compose up
```

Compose builds the eight application images, generates local passwords, initializes the eight owned databases on first startup and waits for the database before starting the APIs. Internet access is needed for the initial image and package downloads. No `.env` file or real member data is required. Leave this terminal running; press Ctrl+C to stop.

For background operation with an explicit readiness wait:

```sh
docker compose up -d --build --wait --wait-timeout 180
docker compose ps
```

## Service addresses

| Service | Local address | Owned database |
| --- | --- | --- |
| Exercise Tracking | http://localhost:8101 | gymarena_tracking |
| Membership | http://localhost:8102 | gymarena_membership |
| Session Control | http://localhost:8103 | gymarena_session |
| Notifications | http://localhost:8104 | gymarena_notification |
| Member Profiles and Measurements | http://localhost:8105 | gymarena_member |
| Face Recognition | http://localhost:8106 | gymarena_recognition |
| Assessment and Challenges | http://localhost:8107 | gymarena_challenge |
| Scoring and Leaderboards | http://localhost:8108 | gymarena_scoring |

Each address exposes service metadata at `/`, process health at `/health/live`, database readiness at `/health/ready`, and API documentation at `/docs`. Readiness requires the service's expected tables and views. It returns HTTP 503 when that owned database is unavailable or incomplete. Database faults leave liveness separate, allowing recovery without pretending the service is ready.

Metadata declares the planned business interface and dependencies. Member Service reports `functional_operations_implemented: true` and lists its implemented operations; the other seven report false. All report `functional_interface_complete: false`. Member Service also serves its kiosk at `/kiosk/`. There is no device worker or fake workout result.

## Ownership and startup

The one-shot `credentials` container generates nine random passwords into separate Docker volumes: one administrator password and one per service. It also generates Member signing/staff keys in the Member credential volume. Existing valid files are preserved. Each application mounts only its own credential volume read-only; no secret values appear in Compose, source control or initialization logs.

The PostgreSQL container mounts all credentials for its initial administrator setup. It creates eight roles and databases, revokes public database connection privileges and applies the eight Part A SQL schemas as their owning roles. PostgreSQL is reachable on the Compose network, without a published host database port. Each application uses its own role, not the administrator.

The application runtime runs as UID 10001 with a read-only application filesystem, dropped capabilities, a small temporary directory and localhost-only published HTTP ports. The bootstrap container runs as root only to write its credential volumes; it has no network connection. Member confirmation/authorization covers this local slice. A full staff identity system, TLS deployment and production secret management remain subsequent work.

Canonical service dependencies remain planned API contracts. They do not create a circular Compose readiness dependency between Challenge, Session and Scoring. Each API waits on the owned database. Cross-service business clients will be added with the corresponding features.

## Data and schema changes

PostgreSQL data lives in the `postgres-data` named volume. Each credential has a separate named volume. Use the following to remove containers and the network while keeping the data and credentials:

```sh
docker compose down
```

Back up the database and its credential volumes together. Removing only credentials while retaining database data will create a password mismatch at the next initialization. The initial SQL runs only on an empty PostgreSQL data volume. Later schema edits need versioned migrations; changing an SQL file does not migrate existing data.

The original schemas contain 38 tables and two Scoring views. Member migration `002_registration_requests.sql` adds one retry-request table on startup, bringing the current total to 39 tables and two views. This additive migration preserves existing data. SQL alone does not implement approved targets, score transactions, feed consumers or leaderboard animation.

## Verify

With the services running, use Python 3.10 or newer on the host:

```sh
python tests/smoke_foundation.py --report foundation-smoke.json
```

The smoke check uses real HTTP endpoints and valid service credentials. It checks that each non-superuser role can access its own database but is denied connections to the seven other service databases, producing 56 denied cross-service connections. It also verifies the non-root UID and read-only application filesystem inside every service.

For the extended local check:

```sh
python tests/smoke_foundation.py --exercise-recovery --report foundation-recovery.json
```

This temporarily stops only this Compose project's database. It checks that all eight APIs remain live, report readiness 503, recover after the database restarts and retain a committed synthetic record. The synthetic record uses a uniquely named temporary test table that is removed after the check. Do not run the extended check against shared development work while someone else is using this Compose project.

Optional port overrides are listed in `.env.example`. The smoke script reads overrides from the host environment; export matching values when using non-default ports. Set a different `COMPOSE_PROJECT_NAME` in the environment if running a second independent copy.

## Dependency and image versions

The runtime dependency lockfile pins all resolved versions and wheel hashes. Docker installs only allowed binary wheels with hash verification. The Python 3.12 and PostgreSQL 16 base tags are version-family tags; their upstream patch images can change. The validation record identifies the image versions actually used for this run. Rebuild and rerun checks when updating the lockfile or image families.

## References

- [Docker multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Compose dependency readiness](https://docs.docker.com/compose/how-tos/startup-order/)
- [Official PostgreSQL image and first-start initialization](https://hub.docker.com/_/postgres)
- [FastAPI container deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [Psycopg binary installation](https://www.psycopg.org/psycopg3/docs/basic/install.html)

## Validation record

`docker-foundation-verification.json` is the historical initial foundation record. Current checks run against each revision in GitHub Actions; [delivery evidence](github-delivery.md) identifies the integrated baseline. See [member verification](member-registration.md#verification) for the added functional suite. Independent owner review and remaining functional acceptance are separate from passing automation.
