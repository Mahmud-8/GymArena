"""Shared fixtures for the CSE454 unit and contract test suite.

The services build their FastAPI app at import time and read the database
settings from the environment, so a safe synthetic environment is installed
before any service module is imported. No real database is contacted: the
readiness tests replace ``psycopg.connect`` with an in-memory double.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SERVICES = json.loads((ROOT / "infra/services.json").read_text(encoding="utf-8"))

# One synthetic credential file shared by the suite. It is never a real secret.
_PASSWORD_FILE = Path(tempfile.gettempdir()) / "gymarena-test-db-password"
_PASSWORD_FILE.write_text("synthetic-test-password\n", encoding="utf-8")

os.environ.setdefault("DB_HOST", "database")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "gymarena_test")
os.environ.setdefault("DB_USER", "gymarena_test")
os.environ.setdefault("DB_PASSWORD_FILE", str(_PASSWORD_FILE))

# Make the shared runtime importable exactly as the Docker image does.
_RUNTIME = str(ROOT / "packages/runtime")
if _RUNTIME not in sys.path:
    sys.path.insert(0, _RUNTIME)

from gymarena_runtime import create_app  # noqa: E402


def _load_service_module(folder: str):
    """Import services/<folder>/api/routes.py under a unique module name.

    The service is imported with its own database identity in the environment,
    exactly as Compose provides it, so the captured settings are realistic.
    """
    module_name = "gymarena_service_" + folder.replace("-", "_")
    if module_name in sys.modules:
        return sys.modules[module_name]
    record = next(s for s in SERVICES if s["folder"] == folder)
    previous = {k: os.environ.get(k) for k in ("DB_NAME", "DB_USER")}
    os.environ["DB_NAME"] = record["database"]
    os.environ["DB_USER"] = record["db_user"]
    try:
        path = ROOT / "services" / folder / "api" / "routes.py"
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    return module


@pytest.fixture(scope="session")
def services():
    return SERVICES


@pytest.fixture(scope="session")
def service_apps():
    """folder -> (app, CONFIG) built by the shipped route module."""
    return {
        s["folder"]: (_load_service_module(s["folder"]).app,
                      _load_service_module(s["folder"]).CONFIG)
        for s in SERVICES
    }


@pytest.fixture(scope="session")
def runtime_module():
    import gymarena_runtime.app as runtime
    return runtime


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchone(self):
        return self._rows[0]

    def fetchall(self):
        return list(self._rows)


class FakeConnection:
    """Minimal psycopg connection double used by the readiness tests."""

    def __init__(self, database, user, relations):
        self.database = database
        self.user = user
        self.relations = relations
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.statements.append(sql)
        if "current_database()" in sql:
            return FakeResult([(self.database, self.user)])
        if "information_schema.tables" in sql:
            return FakeResult(list(self.relations.items()))
        raise AssertionError("Unexpected statement: " + sql)


def make_connection(service, *, database=None, user=None,
                    drop_tables=(), drop_views=(), table_as_view=(),
                    view_as_table=False):
    relations = {t: "BASE TABLE" for t in service["tables"]}
    relations.update({v: "VIEW" for v in service["views"]})
    for table in drop_tables:
        relations.pop(table, None)
    for view in drop_views:
        relations.pop(view, None)
    for table in table_as_view:
        relations[table] = "VIEW"
    if view_as_table:
        for view in service["views"]:
            relations[view] = "BASE TABLE"
    return FakeConnection(database or service["database"],
                          user or service["db_user"], relations)


def readiness_double(monkeypatch, connection=None, error=None):
    """Patch the runtime's psycopg.connect with a double or a raised error."""
    import gymarena_runtime.app as runtime

    def fake_connect(**kwargs):
        if error is not None:
            raise error
        return connection

    monkeypatch.setattr(runtime.psycopg, "connect", fake_connect)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient


@pytest.fixture
def build_app():
    return create_app
