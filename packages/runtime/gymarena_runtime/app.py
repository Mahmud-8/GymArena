"""Operational foundation for independently deployed GymArena services."""
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse

log = logging.getLogger("gymarena.readiness")


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    name: str
    user: str
    password_file: Path

    @classmethod
    def from_environment(cls):
        return cls(
            host=os.environ["DB_HOST"],
            port=int(os.environ.get("DB_PORT", "5432")),
            name=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password_file=Path(os.environ["DB_PASSWORD_FILE"]),
        )

    def connect(self):
        password = self.password_file.read_text(encoding="utf-8").strip()
        if not password:
            raise ValueError("The database credential file is empty")
        return psycopg.connect(
            host=self.host,
            port=self.port,
            dbname=self.name,
            user=self.user,
            password=password,
            connect_timeout=3,
            options="-c statement_timeout=2000",
            application_name="gymarena-foundation",
        )


def create_app(config: dict) -> FastAPI:
    settings = DatabaseSettings.from_environment()
    app = FastAPI(
        title=config["name"] + " foundation",
        version="0.1.0",
        description=(
            "Operational service skeleton. The named business interface is planned; "
            "its functional operations are not implemented."
        ),
    )

    @app.get("/", tags=["foundation"])
    def metadata():
        return {
            "service": config["folder"],
            "stage": "foundation",
            "implemented": ["service_metadata", "liveness", "database_readiness"],
            "functional_operations_implemented": False,
            "planned_interface": config["interface"],
            "planned_requirements": config["requirements"],
            "planned_service_dependencies": config["dependencies"],
            "planned_external_interfaces": config["external_interfaces"],
        }

    @app.get("/health/live", tags=["health"])
    def live():
        return {"service": config["folder"], "status": "alive"}

    @app.get("/health/ready", tags=["health"], responses={503: {"description": "Owned database is unavailable or incomplete"}})
    def ready():
        try:
            with settings.connect() as connection:
                database, role = connection.execute(
                    "SELECT current_database(), current_user"
                ).fetchone()
                if database != settings.name or role != settings.user:
                    raise ValueError("Unexpected database identity")
                relations = dict(connection.execute(
                    "SELECT table_name, table_type FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                ).fetchall())
                if any(relations.get(t) != "BASE TABLE" for t in config["tables"]):
                    raise ValueError("Owned database tables are incomplete")
                if any(relations.get(v) != "VIEW" for v in config["views"]):
                    raise ValueError("Owned database views are incomplete")
            return {"service": config["folder"], "status": "ready", "database": "ready"}
        except (psycopg.Error, OSError, ValueError):
            # Keep connection details, password paths and provider messages out of HTTP responses.
            log.warning("Owned database is not ready for %s", config["folder"])
            return JSONResponse(
                status_code=503,
                content={"service": config["folder"], "status": "not_ready", "database": "unavailable"},
            )

    return app
