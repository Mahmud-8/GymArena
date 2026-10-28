"""Run inside member-service with: docker compose exec -T member-service python - < tests/member_unit.py."""
import base64
import hashlib
import hmac
import json
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException, Request, Response
from application.profiles import RegistrationService
from domain.models import AuthContext, Registration, new_member_code, normalize_code
from infrastructure.security import COOKIE, MemberConfirmation, b64


def request(cookie="", headers=()):
    return Request({"type": "http", "headers": [(b"cookie", f"{COOKIE}={cookie}".encode()), *headers]})


class MemberRules(unittest.TestCase):
    def test_unicode_name_and_whitespace(self):
        self.assertEqual(Registration("  محمود   عماد  ", 23).full_name, "محمود عماد")
        self.assertEqual(Registration("Jose\u0301 O’Neil", 25).full_name, "José O’Neil")

    def test_invalid_profiles(self):
        for name in ("", "   ", "---", "A<script>", "A1", "A\x00B", "A" * 121):
            with self.subTest(name=name), self.assertRaises(ValueError):
                Registration(name, 20)
        for age in (0, -1, 121, True, 20.5, "20", None):
            with self.subTest(age=age), self.assertRaises(ValueError):
                Registration("Test Member", age)

    def test_private_code_format_and_normalization(self):
        codes = {new_member_code() for _ in range(1000)}
        self.assertEqual(len(codes), 1000)
        for code in codes:
            self.assertRegex(code, r"^GA(?:-[A-Z2-7]{4}){4}$")
            self.assertEqual(normalize_code(code.lower().replace("-", " ")), code)
        with self.assertRaises(ValueError):
            normalize_code("GA0107")

    def test_ownership(self):
        own, other = uuid4(), uuid4()
        self.assertTrue(AuthContext("member", own).may_access(own))
        self.assertFalse(AuthContext("member", own).may_access(other))
        self.assertTrue(AuthContext("staff").may_access(other))
        self.assertFalse(AuthContext("unknown", own).may_access(own))

    def test_canonical_retry_fingerprint(self):
        store = Mock()
        service = RegistrationService(store)
        key = uuid4()
        service.register(Registration(" Test   Member ", 25), key)
        first = store.commit_profile_and_event.call_args.args
        service.register(Registration("Test Member", 25), key)
        self.assertEqual(first[:3], store.commit_profile_and_event.call_args.args[:3])
        service.register(Registration("Test Member", 26), key)
        self.assertNotEqual(first[1], store.commit_profile_and_event.call_args.args[1])

    def test_bad_code_never_queries_store(self):
        store = Mock()
        self.assertIsNone(RegistrationService(store).resolve("invalid"))
        store.by_code.assert_not_called()


class ConfirmationRules(unittest.TestCase):
    def setUp(self):
        self.auth = MemberConfirmation(b"x" * 32, "s" * 64)
        self.member = uuid4()
        response = Response()
        with patch("infrastructure.security.time.time", return_value=1000):
            self.csrf = self.auth.issue(response, self.member)
        self.cookie = response.headers["set-cookie"].split(";", 1)[0].split("=", 1)[1]

    def test_confirmation_cookie_and_csrf(self):
        with patch("infrastructure.security.time.time", return_value=1001):
            context = self.auth.authorize(request(self.cookie))
        self.assertEqual(context.member_id, self.member)
        self.auth.require_csrf(request(headers=[(b"x-csrf-token", self.csrf.encode())]), context)
        with self.assertRaises(HTTPException) as failure:
            self.auth.require_csrf(request(), context)
        self.assertEqual(failure.exception.status_code, 403)

    def test_tampered_missing_and_expired_cookie(self):
        for token, now in (("", 1001), (self.cookie + "x", 1001), (self.cookie, 1900), ("💪", 1001)):
            with self.subTest(token=token[:4]), patch("infrastructure.security.time.time", return_value=now):
                with self.assertRaises(HTTPException) as failure:
                    self.auth.authorize(request(token))
                self.assertEqual(failure.exception.status_code, 401)

    def test_signed_invalid_payload_is_rejected(self):
        for data in ({"sub": str(self.member), "exp": True, "nonce": "x" * 32}, {"sub": "bad", "exp": 2000, "nonce": "x" * 32}):
            payload = b64(json.dumps(data).encode())
            signature = b64(hmac.new(self.auth.key, payload.encode(), hashlib.sha256).digest())
            with self.assertRaises(HTTPException), patch("infrastructure.security.time.time", return_value=1001):
                self.auth.authorize(request(payload + "." + signature))

    def test_explicit_staff_key(self):
        self.assertEqual(self.auth.authorize(request(headers=[(b"x-staff-key", b"s" * 64)])).role, "staff")
        with self.assertRaises(HTTPException):
            self.auth.authorize(request(headers=[(b"x-staff-key", b"wrong")]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
