"""Per-service HTTP contract tests for the eight GymArena foundation services.

Every generated test function carries its test-case ID (TC-<code>-<n>) in its
name, as required by the CSE454 test report. The tests exercise the shipped
FastAPI application objects; the readiness tests replace ``psycopg.connect``
with a double, so no database or Docker runtime is needed.
"""
from __future__ import annotations

import psycopg
import pytest

from conftest import SERVICES, make_connection, readiness_double

SERVICE_CODES = {
    "exercise-tracking-service": "ETS",
    "membership-service": "MSH",
    "session-service": "SES",
    "notification-service": "NTS",
    "member-service": "MBR",
    "recognition-service": "REC",
    "challenge-service": "CHL",
    "scoring-service": "SCR",
}

EXPECTED_IMPLEMENTED = ["service_metadata", "liveness", "database_readiness"]


def _tests_for(service):
    code = SERVICE_CODES[service["folder"]]
    folder = service["folder"]

    def app_of(service_apps):
        app, config = service_apps[folder]
        return app, config

    def test_TC_01_metadata_reports_the_planned_contract(client, service_apps):
        """TC-01: metadata endpoint returns the planned interface and FR IDs."""
        app, config = app_of(service_apps)
        response = client(app).get("/")
        assert response.status_code == 200
        assert response.json() == {
            "service": folder,
            "stage": "foundation",
            "implemented": EXPECTED_IMPLEMENTED,
            "functional_operations_implemented": False,
            "planned_interface": config["interface"],
            "planned_requirements": config["requirements"],
            "planned_service_dependencies": config["dependencies"],
            "planned_external_interfaces": config["external_interfaces"],
        }

    def test_TC_02_liveness_answers_without_touching_the_database(client, service_apps, monkeypatch):
        """TC-02: liveness returns 200 and performs no database access."""
        app, _ = app_of(service_apps)

        def forbidden(**kwargs):
            raise AssertionError("Liveness must not open a database connection")

        import gymarena_runtime.app as runtime
        monkeypatch.setattr(runtime.psycopg, "connect", forbidden)
        response = client(app).get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"service": folder, "status": "alive"}

    def test_TC_03_readiness_is_200_when_the_owned_schema_is_complete(client, service_apps, monkeypatch):
        """TC-03: readiness returns 200 when every owned table and view exists."""
        app, config = app_of(service_apps)
        connection = make_connection(service)
        readiness_double(monkeypatch, connection)
        response = client(app).get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"service": folder, "status": "ready", "database": "ready"}
        assert any("information_schema.tables" in s for s in connection.statements)
        assert any("current_database()" in s for s in connection.statements)

    def test_TC_04_readiness_is_503_when_the_database_is_unreachable(client, service_apps, monkeypatch):
        """TC-04: an unreachable database yields 503 and the not_ready contract."""
        app, _ = app_of(service_apps)
        readiness_double(monkeypatch, error=psycopg.OperationalError("connection refused"))
        response = client(app).get("/health/ready")
        assert response.status_code == 503
        assert response.json() == {"service": folder, "status": "not_ready", "database": "unavailable"}

    def test_TC_05_readiness_is_503_for_a_foreign_database_identity(client, service_apps, monkeypatch):
        """TC-05: connecting to another service's database must not report ready."""
        app, _ = app_of(service_apps)
        connection = make_connection(service, database="gymarena_someone_else")
        readiness_double(monkeypatch, connection)
        response = client(app).get("/health/ready")
        assert response.status_code == 503
        assert response.json()["database"] == "unavailable"

    def test_TC_06_readiness_is_503_when_an_owned_table_is_missing(client, service_apps, monkeypatch):
        """TC-06: a missing owned table makes the service not ready."""
        app, _ = app_of(service_apps)
        connection = make_connection(service, drop_tables=(service["tables"][0],))
        readiness_double(monkeypatch, connection)
        response = client(app).get("/health/ready")
        assert response.status_code == 503
        assert response.json()["status"] == "not_ready"

    def test_TC_07_readiness_is_503_when_an_owned_relation_has_the_wrong_kind(client, service_apps, monkeypatch):
        """TC-07: a view in place of a table (or the reverse) is rejected."""
        app, _ = app_of(service_apps)
        if service["views"]:
            connection = make_connection(service, view_as_table=True)
        else:
            connection = make_connection(service, table_as_view=(service["tables"][0],))
        readiness_double(monkeypatch, connection)
        response = client(app).get("/health/ready")
        assert response.status_code == 503
        assert response.json()["database"] == "unavailable"

    def test_TC_08_readiness_failure_does_not_leak_connection_details(client, service_apps, monkeypatch):
        """TC-08: the 503 body exposes no host, user, password path or provider text."""
        app, _ = app_of(service_apps)
        secret_text = ("password authentication failed for user "
                       f"{service['db_user']} at /credentials/password on database")
        readiness_double(monkeypatch, error=psycopg.OperationalError(secret_text))
        response = client(app).get("/health/ready")
        body = response.text
        assert response.status_code == 503
        assert set(response.json()) == {"service", "status", "database"}
        for leaked in (service["db_user"], "/credentials", "password", "database:"):
            assert leaked not in body

    def test_TC_09_openapi_exposes_only_the_foundation_boundary(client, service_apps):
        """TC-09: the published API surface is exactly the three foundation paths."""
        app, _ = app_of(service_apps)
        response = client(app).get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert set(schema["paths"]) == {"/", "/health/live", "/health/ready"}
        assert schema["info"]["title"].endswith("foundation")

    return {
        f"test_TC_{code}_01_metadata_reports_the_planned_contract": test_TC_01_metadata_reports_the_planned_contract,
        f"test_TC_{code}_02_liveness_answers_without_touching_the_database": test_TC_02_liveness_answers_without_touching_the_database,
        f"test_TC_{code}_03_readiness_is_200_when_the_owned_schema_is_complete": test_TC_03_readiness_is_200_when_the_owned_schema_is_complete,
        f"test_TC_{code}_04_readiness_is_503_when_the_database_is_unreachable": test_TC_04_readiness_is_503_when_the_database_is_unreachable,
        f"test_TC_{code}_05_readiness_is_503_for_a_foreign_database_identity": test_TC_05_readiness_is_503_for_a_foreign_database_identity,
        f"test_TC_{code}_06_readiness_is_503_when_an_owned_table_is_missing": test_TC_06_readiness_is_503_when_an_owned_table_is_missing,
        f"test_TC_{code}_07_readiness_is_503_when_an_owned_relation_has_the_wrong_kind": test_TC_07_readiness_is_503_when_an_owned_relation_has_the_wrong_kind,
        f"test_TC_{code}_08_readiness_failure_does_not_leak_connection_details": test_TC_08_readiness_failure_does_not_leak_connection_details,
        f"test_TC_{code}_09_openapi_exposes_only_the_foundation_boundary": test_TC_09_openapi_exposes_only_the_foundation_boundary,
    }


globals().update({name: fn for service in SERVICES for name, fn in _tests_for(service).items()})
