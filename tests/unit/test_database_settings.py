"""Unit tests for the shared database settings and credential handling."""
from __future__ import annotations

import pytest

from gymarena_runtime.app import DatabaseSettings


def _env(monkeypatch, tmp_path, **overrides):
    password = tmp_path / "password"
    password.write_text("  synthetic-secret\n", encoding="utf-8")
    values = {
        "DB_HOST": "database",
        "DB_PORT": "5432",
        "DB_NAME": "gymarena_member",
        "DB_USER": "gymarena_member",
        "DB_PASSWORD_FILE": str(password),
    }
    values.update(overrides)
    for key, value in values.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    return password


def test_TC_DB_01_settings_are_read_from_the_environment(monkeypatch, tmp_path):
    """TC-DB-01: the settings object mirrors the configured environment."""
    password = _env(monkeypatch, tmp_path)
    settings = DatabaseSettings.from_environment()
    assert (settings.host, settings.port, settings.name, settings.user) == (
        "database", 5432, "gymarena_member", "gymarena_member")
    assert settings.password_file == password


def test_TC_DB_02_port_defaults_to_5432_when_absent(monkeypatch, tmp_path):
    """TC-DB-02: an omitted DB_PORT falls back to 5432."""
    _env(monkeypatch, tmp_path, DB_PORT=None)
    assert DatabaseSettings.from_environment().port == 5432


def test_TC_DB_03_missing_required_setting_fails_fast(monkeypatch, tmp_path):
    """TC-DB-03: a missing required variable stops startup with KeyError."""
    _env(monkeypatch, tmp_path, DB_HOST=None)
    with pytest.raises(KeyError):
        DatabaseSettings.from_environment()


def test_TC_DB_04_non_numeric_port_is_rejected(monkeypatch, tmp_path):
    """TC-DB-04: a non-numeric DB_PORT is rejected instead of defaulting."""
    _env(monkeypatch, tmp_path, DB_PORT="not-a-port")
    with pytest.raises(ValueError):
        DatabaseSettings.from_environment()


def test_TC_DB_05_empty_credential_file_never_reaches_the_driver(monkeypatch, tmp_path):
    """TC-DB-05: an empty password file raises ValueError before connecting."""
    password = _env(monkeypatch, tmp_path)
    password.write_text("   \n", encoding="utf-8")
    settings = DatabaseSettings.from_environment()

    def forbidden(**kwargs):
        raise AssertionError("psycopg.connect must not be called")

    import gymarena_runtime.app as runtime
    monkeypatch.setattr(runtime.psycopg, "connect", forbidden)
    with pytest.raises(ValueError, match="credential file is empty"):
        settings.connect()


def test_TC_DB_06_connect_uses_bounded_timeouts_and_strips_the_password(monkeypatch, tmp_path):
    """TC-DB-06: connect applies timeouts, statement timeout and the app name."""
    _env(monkeypatch, tmp_path)
    settings = DatabaseSettings.from_environment()
    captured = {}

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_connect(**kwargs):
        captured.update(kwargs)
        return Connection()

    import gymarena_runtime.app as runtime
    monkeypatch.setattr(runtime.psycopg, "connect", fake_connect)
    with settings.connect():
        pass
    assert captured == {
        "host": "database",
        "port": 5432,
        "dbname": "gymarena_member",
        "user": "gymarena_member",
        "password": "synthetic-secret",
        "connect_timeout": 3,
        "options": "-c statement_timeout=2000",
        "application_name": "gymarena-foundation",
    }


def test_TC_DB_07_a_missing_credential_file_reports_not_ready(monkeypatch, tmp_path):
    """TC-DB-07: an unreadable credential file yields 503, not an unhandled error."""
    from fastapi.testclient import TestClient
    from gymarena_runtime import create_app

    _env(monkeypatch, tmp_path, DB_PASSWORD_FILE=str(tmp_path / "absent"))
    app = create_app({
        "folder": "member-service", "name": "Member Profiles and Measurements",
        "interface": "IMemberProfile", "requirements": "FR-09, FR-10",
        "tables": ["members"], "views": [], "dependencies": {},
        "external_interfaces": ["IScaleInput"],
    })
    response = TestClient(app).get("/health/ready")
    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"
    assert "absent" not in response.text
