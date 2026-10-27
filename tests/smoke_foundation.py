"""Exercise actual HTTP services, database ownership and optional outage recovery.

Run from the repository root after `docker compose up -d --build --wait`.
Uses the Python standard library on the host; psycopg runs inside each service.
"""
import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES = json.loads((ROOT / "infra/services.json").read_text(encoding="utf-8"))


def compose(*args, input_text=None):
    result = subprocess.run(["docker", "compose", *args], cwd=ROOT, input=input_text,
                            text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(f"Compose operation failed: {' '.join(args[:3])}\n{result.stderr}")
    return result.stdout


def request(service, path):
    port = int(os.environ.get(service["id"].upper() + "_PORT", service["port"]))
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=8) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def wait_ready(timeout=90):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if all(request(s, "/health/ready")[0] == 200 for s in SERVICES):
                return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(2)
    raise AssertionError("The eight owned databases did not all become ready")


def in_service(service, source):
    return compose("exec", "-T", service["folder"], "python", "-", input_text=source)


CONNECTION = '''import errno, json, os, pathlib, psycopg
password = pathlib.Path(os.environ['DB_PASSWORD_FILE']).read_text().strip()
params = dict(host=os.environ['DB_HOST'], port=os.environ['DB_PORT'], user=os.environ['DB_USER'], password=password, connect_timeout=3)
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exercise-recovery", action="store_true",
                        help="Briefly stop this Compose project's database and verify recovery")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    checks = []
    wait_ready()
    for s in SERVICES:
        status, data = request(s, "/")
        assert status == 200 and data["service"] == s["folder"]
        assert data["functional_operations_implemented"] is False
        assert request(s, "/health/live")[0] == 200
        assert request(s, "/health/ready")[0] == 200
        status, schema = request(s, "/openapi.json")
        assert status == 200 and set(schema["paths"]) == {"/", "/health/live", "/health/ready"}
        checks.append({"check": "http_and_contract_boundary", "service": s["folder"], "passed": True})
        source = CONNECTION + f'''
with psycopg.connect(dbname={s['database']!r}, **params) as c:
    assert c.execute('SELECT current_user').fetchone()[0] == {s['db_user']!r}
    assert c.execute('SELECT rolsuper FROM pg_roles WHERE rolname = current_user').fetchone()[0] is False
    for database in {[x['database'] for x in SERVICES if x != s]!r}:
        assert c.execute('SELECT has_database_privilege(current_user, %s, %s)', (database, 'CONNECT')).fetchone()[0] is False
denied = []
for database in {[x['database'] for x in SERVICES if x != s]!r}:
    try:
        psycopg.connect(dbname=database, **params).close()
    except psycopg.Error as e:
        # libpq connection-establishment errors may omit the SQLSTATE.
        # The explicit ACL query above and this denial distinguish isolation
        # from a bad password, DNS failure or an unavailable server.
        assert e.sqlstate == '42501' or (e.sqlstate is None and 'permission denied for database' in str(e))
        denied.append(database)
    else:
        raise AssertionError('Cross-service database access was permitted')
assert os.getuid() == 10001
try:
    pathlib.Path('/app/api/unexpected-write').write_text('test')
except OSError as e:
    assert e.errno == errno.EROFS
else:
    raise AssertionError('Application filesystem is writable')
print(json.dumps(dict(denied=len(denied), non_root=True, read_only=True)))
'''
        result = json.loads(in_service(s, source))
        checks.append({"check": "database_and_process_isolation", "service": s["folder"], "passed": True, **result})

    if args.exercise_recovery:
        service = next(s for s in SERVICES if s["id"] == "member")
        # A newly created synthetic table avoids changing real member or feed records.
        probe = "foundation_smoke_" + uuid.uuid4().hex
        create = CONNECTION + f'''
with psycopg.connect(dbname={service['database']!r}, **params) as c:
    c.execute('CREATE TABLE {probe} (marker TEXT PRIMARY KEY)')
    c.execute('INSERT INTO {probe} VALUES (%s)', ('synthetic-persistence-check',))
'''
        in_service(service, create)
        try:
            compose("stop", "database")
            for s in SERVICES:
                assert request(s, "/health/live")[0] == 200
                code, response = request(s, "/health/ready")
                assert code == 503 and response["database"] == "unavailable"
                checks.append({"check": "outage_reports_503_but_process_stays_live", "service": s["folder"], "passed": True})
        finally:
            compose("start", "database")
            wait_ready()
            try:
                read = CONNECTION + f'''
with psycopg.connect(dbname={service['database']!r}, **params) as c:
    assert c.execute('SELECT marker FROM {probe}').fetchone()[0] == 'synthetic-persistence-check'
'''
                in_service(service, read)
                checks.append({"check": "postgres_restart_retains_committed_data", "passed": True})
            finally:
                in_service(service, CONNECTION + f"\nwith psycopg.connect(dbname={service['database']!r}, **params) as c:\n    c.execute('DROP TABLE {probe}')\n")
        checks.append({"check": "all_eight_services_recover", "passed": True})

    report = {"scope": "Docker foundation only", "checks": checks,
              "cross_database_connections_denied": sum(c.get("denied", 0) for c in checks),
              "functional_features_tested": False}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
