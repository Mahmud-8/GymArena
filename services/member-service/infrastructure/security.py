"""Short-lived member confirmation and explicit local staff credentials."""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, Request, Response

from domain.models import AuthContext

COOKIE = "gymarena_member"
SESSION_SECONDS = 900


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


class MemberConfirmation:
    def __init__(self, signing_key: bytes, staff_key: str):
        if len(signing_key) != 32 or len(staff_key) != 64:
            raise ValueError("Member confirmation credentials are incomplete")
        self.key = signing_key
        self.staff_key = staff_key
        self.secure = os.environ.get("MEMBER_COOKIE_SECURE", "false").lower() == "true"

    @classmethod
    def from_environment(cls):
        secret = Path(os.environ["MEMBER_SESSION_KEY_FILE"]).read_text(encoding="ascii").strip()
        staff = Path(os.environ["MEMBER_STAFF_KEY_FILE"]).read_text(encoding="ascii").strip()
        return cls(bytes.fromhex(secret), staff)

    def csrf(self, context: AuthContext) -> str:
        return hmac.new(self.key, ("csrf:" + context.nonce).encode("ascii"), hashlib.sha256).hexdigest()

    def issue(self, response: Response, member_id: UUID) -> str:
        nonce = secrets.token_hex(16)
        payload = b64(json.dumps({"sub": str(member_id), "exp": int(time.time()) + SESSION_SECONDS,
                                  "nonce": nonce}, separators=(",", ":")).encode("ascii"))
        signature = b64(hmac.new(self.key, payload.encode("ascii"), hashlib.sha256).digest())
        response.set_cookie(COOKIE, payload + "." + signature, max_age=SESSION_SECONDS,
                            httponly=True, secure=self.secure, samesite="strict", path="/api")
        return self.csrf(AuthContext("member", member_id, nonce))

    def authorize(self, request: Request) -> AuthContext:
        staff = request.headers.get("x-staff-key")
        if staff:
            if hmac.compare_digest(staff.encode("utf-8"), self.staff_key.encode("ascii")):
                return AuthContext("staff")
            raise HTTPException(401, "Staff access was not confirmed.")
        token = request.cookies.get(COOKIE, "")
        try:
            payload, signature = token.split(".")
            expected = b64(hmac.new(self.key, payload.encode("ascii"), hashlib.sha256).digest())
            if not hmac.compare_digest(signature, expected):
                raise ValueError
            decoded = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
            if type(decoded["exp"]) is not int or decoded["exp"] <= time.time():
                raise ValueError
            if not isinstance(decoded["nonce"], str) or len(decoded["nonce"]) != 32:
                raise ValueError
            return AuthContext("member", UUID(decoded["sub"]), decoded["nonce"])
        except (ValueError, KeyError, TypeError, UnicodeError):
            raise HTTPException(401, "Confirm your member code to continue.") from None

    def require_csrf(self, request: Request, context: AuthContext):
        if context.role == "staff":
            return
        value = request.headers.get("x-csrf-token", "")
        if not hmac.compare_digest(value.encode("utf-8"), self.csrf(context).encode("ascii")):
            raise HTTPException(403, "Confirm this action from the current kiosk session.")

    def clear(self, response: Response):
        response.delete_cookie(COOKIE, path="/api", httponly=True, secure=self.secure, samesite="strict")
