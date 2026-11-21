# Unit and contract testing

The foundation is verified by two independent suites:

| Suite | Entry point | Needs | Checks |
| --- | --- | --- | --- |
| Unit and contract tests | `pytest` (`tests/unit/`) | Python 3.12 only | Service HTTP contracts, readiness logic, database settings, repository consistency |
| Docker foundation smoke test | `python tests/smoke_foundation.py` | Docker Compose | Real containers, database isolation, outage and recovery |

The unit suite replaces `psycopg.connect` with an in-memory double, so it runs
without PostgreSQL, Docker or network access.

## Run

```bash
python -m venv .venv
.venv/bin/pip install --require-hashes -r infra/requirements.lock
.venv/bin/pip install -r tests/requirements.txt
.venv/bin/python -m pytest -q --cov=packages/runtime/gymarena_runtime --cov=services --cov-report=term-missing
```

`pytest.ini` points `testpaths` at `tests/unit` and puts `packages/runtime` on
the import path, so a plain `pytest` works from the repository root.

## Test-case IDs

Every test name starts with its report ID:

| Prefix | File | Meaning |
| --- | --- | --- |
| `TC-ETS-nn` | `tests/unit/test_service_contract.py` | exercise-tracking-service |
| `TC-MSH-nn` | `tests/unit/test_service_contract.py` | membership-service |
| `TC-SES-nn` | `tests/unit/test_service_contract.py` | session-service |
| `TC-NTS-nn` | `tests/unit/test_service_contract.py` | notification-service |
| `TC-MBR-nn` | `tests/unit/test_service_contract.py` | member-service |
| `TC-REC-nn` | `tests/unit/test_service_contract.py` | recognition-service |
| `TC-CHL-nn` | `tests/unit/test_service_contract.py` | challenge-service |
| `TC-SCR-nn` | `tests/unit/test_service_contract.py` | scoring-service |
| `TC-REPO-nn` | `tests/unit/test_repository_contract.py` | cross-service repository agreements |
| `TC-DB-nn` | `tests/unit/test_database_settings.py` | shared database settings |

`nn` is `01`–`09` for a service, `01`–`11` for the repository and `01`–`07`
for the database settings.

## Scope and limits

The suite tests what the foundation implements: service metadata, liveness,
database readiness, configuration and schema agreement. The sixteen business
requirements (`FR-01`–`FR-16`) are declared in each service README but their
operations are not implemented, so no unit test claims them. Add the acceptance
test for an FR together with the feature that implements it, using the next free
`TC-<code>-nn` number.

## CI

[`.github/workflows/unit-tests.yml`](../.github/workflows/unit-tests.yml) runs
the suite on every push and pull request, prints the missing-line report and
uploads `coverage/junit.xml`, `coverage/coverage.xml` and `coverage/html/` as
the `unit-test-evidence-<sha>` artifact.
