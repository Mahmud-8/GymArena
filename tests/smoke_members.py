"""Real HTTP/PostgreSQL acceptance checks; synthetic records are removed by request UUID.

Requires an isolated COMPOSE_PROJECT_NAME beginning gymarena-ci- or exactly
gymarena-member-validation. Never runs against the normal user's project.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from http.cookiejar import CookieJar
from http.client import HTTPException as HTTPConnectionError
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BASE = f"http://127.0.0.1:{os.environ.get('MEMBER_PORT', '8105')}"


def compose(*args, source=None):
    result = subprocess.run(["docker", "compose", *args], cwd=ROOT, input=source,
                            text=True, encoding="utf-8", capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(f"Compose failed ({' '.join(args[:3])}): {result.stderr}")
    return result.stdout


def inside(source):
    return compose("exec", "-T", "member-service", "python", "-", source=source)


CONNECTION = """from gymarena_runtime.app import DatabaseSettings
from uuid import UUID
settings = DatabaseSettings.from_environment()
"""


class Client:
    def __init__(self):
        self.jar = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def call(self, path, method="GET", body=None, headers=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(BASE + path, data=data, method=method,
                                         headers={"Content-Type": "application/json", **(headers or {})})
        try:
            response = self.opener.open(request, timeout=12)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read()
            content = json.loads(raw) if raw and "application/json" in response.headers.get("Content-Type", "") else raw.decode()
            return response.status, content, response.headers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    project = os.environ.get("COMPOSE_PROJECT_NAME", "")
    if not (project.startswith("gymarena-ci-") or project == "gymarena-member-validation"):
        raise SystemExit("Use an isolated gymarena-ci-* or gymarena-member-validation Compose project.")
    checks, request_ids = [], []

    def passed(name):
        checks.append({"check": name, "passed": True})
        print("PASS " + name, flush=True)

    def key():
        value = str(uuid4())
        request_ids.append(value)
        return {"Idempotency-Key": value}

    def count():
        return json.loads(inside(CONNECTION + """
import json
with settings.connect() as c:
    print(json.dumps([c.execute('SELECT count(*) FROM ' + t).fetchone()[0] for t in
                      ('members', 'member_registered_outbox', 'member_registration_requests')]))
"""))

    try:
        compose("exec", "-T", "member-service", "python", "-", source=(ROOT / "tests/member_unit.py").read_text(encoding="utf-8"))
        passed("domain_and_confirmation_unit_suite")
        client = Client()
        before = count()
        for data in ({"full_name": "", "age": 20}, {"full_name": "Valid Name", "age": 0},
                     {"full_name": "Valid Name", "age": True}, {"full_name": "A<script>", "age": 20},
                     {"full_name": "Valid Name", "age": "20"}, {"full_name": "Valid Name", "age": 20.5}):
            status, data, _ = client.call("/api/members", "POST", data, key())
            assert status == 422 and data["fields"], (status, data)
        assert count() == before
        passed("invalid_fields_never_persist_partial_profiles")

        details = {"full_name": "  محمود   اختبار  ", "age": 23}
        registration_key = key()
        status, session, headers = client.call("/api/members", "POST", details, registration_key)
        assert status == 201, (status, session)
        member, csrf = session["member"], session["csrf_token"]
        member_id = member["member_id"]
        assert member["full_name"] == "محمود اختبار" and member["age"] == 23
        assert headers["Cache-Control"] == "no-store"
        cookie = headers["Set-Cookie"].lower()
        assert "httponly" in cookie and "samesite=strict" in cookie and "path=/api" in cookie
        assert count() == [x + 1 for x in before]
        passed("registration_commits_profile_request_and_event_with_private_cookie")

        status, replay, _ = client.call("/api/members", "POST", details, registration_key)
        assert status == 200 and replay["member"] == member
        csrf = replay["csrf_token"]
        assert count() == [x + 1 for x in before]
        status, _, _ = client.call("/api/members", "POST", {**details, "age": 24}, registration_key)
        assert status == 409 and count() == [x + 1 for x in before]
        passed("idempotent_retry_and_conflicting_retry")

        anonymous = Client()
        assert anonymous.call(f"/api/members/{member_id}")[0] == 401
        assert anonymous.call("/api/member-session", headers={"Cookie": "gymarena_member=invalid.signature"})[0] == 401
        assert client.call(f"/api/members/{uuid4()}")[0] == 403
        assert client.call("/api/member-registrations")[0] == 403
        assert client.call("/api/member-session")[1]["member"] == member
        passed("missing_tampered_and_cross_member_access_rejected")

        correction = {"full_name": "Corrected Test Member", "age": 24, "expected_updated_at": member["updated_at"]}
        assert anonymous.call(f"/api/members/{member_id}", "PATCH", correction)[0] == 401
        assert client.call(f"/api/members/{uuid4()}", "PATCH", correction, {"X-CSRF-Token": csrf})[0] == 403
        assert client.call(f"/api/members/{member_id}", "PATCH", correction)[0] == 403
        assert client.call(f"/api/members/{member_id}", "PATCH", correction, {"X-CSRF-Token": "wrong"})[0] == 403
        assert client.call(f"/api/members/{member_id}", "PATCH", {**correction, "member_code": "changed"}, {"X-CSRF-Token": csrf})[0] == 422
        assert client.call(f"/api/members/{member_id}", "PATCH", correction, {"X-CSRF-Token": csrf, "Origin": "https://foreign.invalid"})[0] == 403
        assert client.call(f"/api/members/{member_id}")[1] == member
        status, corrected, _ = client.call(f"/api/members/{member_id}", "PATCH", correction, {"X-CSRF-Token": csrf})
        assert status == 200 and corrected["full_name"] == correction["full_name"]
        assert corrected["member_id"] == member_id and corrected["member_code"] == member["member_code"]
        assert corrected["created_at"] == member["created_at"] and corrected["updated_at"] != member["updated_at"]
        assert client.call(f"/api/members/{member_id}", "PATCH", correction, {"X-CSRF-Token": csrf})[0] == 409
        assert client.call(f"/api/members/{member_id}")[1] == corrected
        passed("authorized_correction_immutable_identity_csrf_origin_and_stale_version")

        staff_key = inside("import os\nfrom pathlib import Path\nprint(Path(os.environ['MEMBER_STAFF_KEY_FILE']).read_text().strip())").strip()
        staff = {"X-Staff-Key": staff_key}
        assert anonymous.call(f"/api/members/{member_id}", headers={"X-Staff-Key": "wrong"})[0] == 401
        status, final_member, _ = anonymous.call(f"/api/members/{member_id}", "PATCH",
            {**correction, "full_name": "Staff Corrected Test", "expected_updated_at": corrected["updated_at"]}, staff)
        assert status == 200 and final_member["member_code"] == member["member_code"]
        passed("explicit_authorized_staff_correction")

        shared_key = key()
        with ThreadPoolExecutor(max_workers=6) as pool:
            responses = list(pool.map(lambda _: Client().call("/api/members", "POST", {"full_name": "Concurrent Retry", "age": 25}, shared_key), range(6)))
        assert sorted(r[0] for r in responses) == [200] * 5 + [201]
        assert len({r[1]["member"]["member_id"] for r in responses}) == 1
        distinct_keys = [key() for _ in range(8)]
        with ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(lambda h: Client().call("/api/members", "POST", {"full_name": "Parallel Test", "age": 26}, h), distinct_keys))
        assert all(r[0] == 201 for r in responses), [(r[0], r[1]) for r in responses if r[0] != 201]
        assert len({r[1]["member"]["member_id"] for r in responses}) == 8
        assert len({r[1]["member"]["member_code"] for r in responses}) == 8
        passed("concurrent_retries_and_distinct_registrations")

        collision_key = key()["Idempotency-Key"]
        inside(CONNECTION + f"""
from application.profiles import RegistrationService
from infrastructure.repository import SqlMemberStore
from domain.models import CodeAllocationUnavailable, Registration
with settings.connect() as c:
    before = c.execute("SELECT last_sequence FROM registration_feed_state").fetchone()[0]
try:
    RegistrationService(SqlMemberStore(settings), lambda: {member['member_code']!r}).register(Registration('Collision Test', 20), UUID({collision_key!r}))
except CodeAllocationUnavailable:
    pass
else:
    raise AssertionError('Expected code collision failure')
with settings.connect() as c:
    assert c.execute("SELECT last_sequence FROM registration_feed_state").fetchone()[0] == before
    assert c.execute("SELECT count(*) FROM member_registration_requests WHERE request_id=%s", (UUID({collision_key!r}),)).fetchone()[0] == 0
""")
        passed("code_collision_rolls_back_feed_and_profile_atomically")

        cursor, sequences, ids = 0, [], []
        while True:
            status, feed, _ = anonymous.call(f"/api/member-registrations?after={cursor}&limit=2", headers=staff)
            assert status == 200
            for event in feed["events"]:
                assert set(event) == {"event_id", "member_id", "display_name", "sequence"}
                sequences.append(event["sequence"]); ids.append(event["member_id"])
            assert feed["next_cursor"] >= cursor
            cursor = feed["next_cursor"]
            if not feed["has_more"]:
                break
        assert sequences == sorted(set(sequences)) and len(ids) == len(set(ids)) and member_id in ids
        assert anonymous.call("/api/member-registrations?limit=201", headers=staff)[0] == 422
        passed("ordered_paginated_registration_feed_excludes_private_fields")

        assert client.call("/api/member-session", "DELETE")[0] == 204
        assert client.call("/api/member-session")[0] == 401
        assert client.call("/api/member-access", "POST", {"member_code": "wrong"})[0] == 401
        status, restored, _ = client.call("/api/member-access", "POST", {"member_code": member["member_code"].lower().replace("-", " ")})
        assert status == 200 and restored["member"] == final_member
        passed("signout_and_reconfirmation_by_saved_code")

        compose("restart", "member-service")
        for _ in range(30):
            try:
                if client.call("/health/ready")[0] == 200:
                    break
            except (urllib.error.URLError, TimeoutError, ConnectionError, HTTPConnectionError):
                pass
            time.sleep(1)
        else:
            raise AssertionError("Member service did not recover")
        assert client.call("/api/member-session")[1]["member"] == final_member
        status, persisted, _ = client.call("/api/members", "POST", details, registration_key)
        assert status == 200 and persisted["member"] == final_member
        passed("restart_retains_profiles_retry_keys_credentials_and_migration")

        status, html, _ = client.call("/kiosk/")
        assert status == 200 and "GymArena" in html and '/kiosk/assets/' in html
        assert client.call("/api/measurements")[0] == 404
        metadata = client.call("/")[1]
        assert metadata["functional_operations_implemented"] is True and metadata["functional_interface_complete"] is False
        passed("built_kiosk_served_and_partial_scope_metadata_truthful")
    finally:
        inside(CONNECTION + f"""
request_ids = [UUID(v) for v in {request_ids!r}]
with settings.connect() as c:
    c.execute('DELETE FROM member_registered_outbox WHERE member_id IN (SELECT member_id FROM member_registration_requests WHERE request_id = ANY(%s))', (request_ids,))
    c.execute('DELETE FROM members WHERE member_id IN (SELECT member_id FROM member_registration_requests WHERE request_id = ANY(%s))', (request_ids,))
    assert c.execute('SELECT count(*) FROM member_registration_requests WHERE request_id = ANY(%s)', (request_ids,)).fetchone()[0] == 0
""")
    passed("synthetic_records_removed_by_captured_request_ids")
    report = {"scope": "US17_US18_member_registration_and_correction", "project": project,
              "checks": checks, "passed": len(checks), "unit_tests": 10,
              "secrets_or_member_codes_in_report": False}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": len(checks), "unit_tests": 10}))


if __name__ == "__main__":
    main()
