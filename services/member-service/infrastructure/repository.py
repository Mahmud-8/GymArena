"""SQL transactions connect only to the Member database."""
import hashlib
from pathlib import Path
from uuid import uuid4

from psycopg.rows import dict_row

from domain.models import CodeAllocationUnavailable, MemberProfile, MemberRegistered, RegistrationConflict, StaleProfile

PROFILE_COLUMNS = "member_id, full_name, age, member_code, created_at, updated_at"


class SqlMemberStore:
    def __init__(self, settings):
        self.settings = settings

    def migrate(self):
        migration = Path(__file__).resolve().parents[1] / "db/002_registration_requests.sql"
        with self.settings.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (1196573001,))
            connection.execute(migration.read_text(encoding="utf-8"))

    def commit_profile_and_event(self, request_id, payload_hash, registration, code_factory):
        lock = int.from_bytes(hashlib.sha256(request_id.bytes).digest()[:8], "big", signed=True)
        with self.settings.connect() as connection, connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", (lock,))
            existing = cursor.execute(
                "SELECT payload_hash, member_id FROM member_registration_requests WHERE request_id = %s",
                (request_id,),
            ).fetchone()
            if existing:
                if existing["payload_hash"] != payload_hash:
                    raise RegistrationConflict
                row = cursor.execute("SELECT " + PROFILE_COLUMNS + " FROM members WHERE member_id = %s",
                                     (existing["member_id"],)).fetchone()
                return MemberProfile(**row), False

            # This row lock is held through commit, so a feed cursor cannot skip
            # a slower transaction whose sequence was allocated earlier.
            sequence = cursor.execute(
                "UPDATE registration_feed_state SET last_sequence = last_sequence + 1 "
                "WHERE feed_name = 'registrations' RETURNING last_sequence"
            ).fetchone()["last_sequence"]
            member_id = uuid4()
            for _ in range(5):
                row = cursor.execute(
                    "INSERT INTO members (member_id, full_name, age, member_code) VALUES (%s, %s, %s, %s) "
                    "ON CONFLICT (member_code) DO NOTHING RETURNING " + PROFILE_COLUMNS,
                    (member_id, registration.full_name, registration.age, code_factory()),
                ).fetchone()
                if row:
                    break
            else:
                raise CodeAllocationUnavailable
            cursor.execute(
                "INSERT INTO member_registered_outbox (event_id, feed_sequence, member_id, display_name) "
                "VALUES (%s, %s, %s, %s)", (uuid4(), sequence, member_id, registration.full_name),
            )
            cursor.execute(
                "INSERT INTO member_registration_requests (request_id, payload_hash, member_id) VALUES (%s, %s, %s)",
                (request_id, payload_hash, member_id),
            )
            return MemberProfile(**row), True

    def find(self, member_id):
        with self.settings.connect() as connection, connection.cursor(row_factory=dict_row) as cursor:
            row = cursor.execute("SELECT " + PROFILE_COLUMNS + " FROM members WHERE member_id = %s", (member_id,)).fetchone()
            return MemberProfile(**row) if row else None

    def by_code(self, code):
        with self.settings.connect() as connection, connection.cursor(row_factory=dict_row) as cursor:
            row = cursor.execute("SELECT " + PROFILE_COLUMNS + " FROM members WHERE member_code = %s", (code,)).fetchone()
            return MemberProfile(**row) if row else None

    def correct(self, member_id, registration, expected_updated_at):
        with self.settings.connect() as connection, connection.cursor(row_factory=dict_row) as cursor:
            row = cursor.execute(
                "UPDATE members SET full_name = %s, age = %s, updated_at = clock_timestamp() "
                "WHERE member_id = %s AND updated_at = %s RETURNING " + PROFILE_COLUMNS,
                (registration.full_name, registration.age, member_id, expected_updated_at),
            ).fetchone()
            if row:
                return MemberProfile(**row)
            if cursor.execute("SELECT 1 FROM members WHERE member_id = %s", (member_id,)).fetchone():
                raise StaleProfile
            return None

    def registered(self, after, limit):
        with self.settings.connect() as connection, connection.cursor(row_factory=dict_row) as cursor:
            rows = cursor.execute(
                "SELECT event_id, member_id, display_name, feed_sequence AS sequence "
                "FROM member_registered_outbox WHERE feed_sequence > %s ORDER BY feed_sequence LIMIT %s",
                (after, limit),
            ).fetchall()
            return [MemberRegistered(**row) for row in rows]
