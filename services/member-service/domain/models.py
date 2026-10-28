"""Registration invariants independent of HTTP and PostgreSQL."""
import base64
import re
import secrets
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


def normalize_name(value: str) -> str:
    name = " ".join(unicodedata.normalize("NFC", value).split())
    if not 1 <= len(name) <= 120:
        raise ValueError("Enter a name between 1 and 120 characters.")
    if not any(unicodedata.category(c).startswith("L") for c in name):
        raise ValueError("Enter a name containing letters.")
    if any(not (unicodedata.category(c)[0] in "LM" or c in " '-.\u2019" or unicodedata.category(c) == "Pd") for c in name):
        raise ValueError("Use letters, spaces, apostrophes, dots or hyphens in your name.")
    return name


def normalize_code(value: str) -> str:
    compact = re.sub(r"[\s-]", "", value).upper()
    if not re.fullmatch(r"GA[A-Z2-7]{16}", compact):
        raise ValueError("Enter the complete member code shown when you registered.")
    return "GA-" + "-".join(compact[i:i + 4] for i in range(2, 18, 4))


def new_member_code() -> str:
    # 80 random bits, separate from the public UUID; no sequential login codes.
    suffix = base64.b32encode(secrets.token_bytes(10)).decode("ascii")
    return "GA-" + "-".join(suffix[i:i + 4] for i in range(0, 16, 4))


@dataclass(frozen=True)
class Registration:
    full_name: str
    age: int

    def __post_init__(self):
        object.__setattr__(self, "full_name", normalize_name(self.full_name))
        if type(self.age) is not int or not 1 <= self.age <= 120:
            raise ValueError("Enter a whole-number age between 1 and 120.")


@dataclass(frozen=True)
class MemberProfile:
    member_id: UUID
    full_name: str
    age: int
    member_code: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class MemberRegistered:
    event_id: UUID
    member_id: UUID
    display_name: str
    sequence: int


@dataclass(frozen=True)
class AuthContext:
    role: str
    member_id: UUID | None = None
    nonce: str = ""

    def may_access(self, member_id: UUID) -> bool:
        return self.role == "staff" or (self.role == "member" and self.member_id == member_id)


class RegistrationConflict(Exception):
    """A retry key was reused with a different registration."""


class StaleProfile(Exception):
    """Another correction committed after this edit was loaded."""


class CodeAllocationUnavailable(Exception):
    """No unique code was allocated; the registration transaction rolled back."""
