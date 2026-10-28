"""FR-09 application use cases through a narrow member-owned store port."""
import hashlib
import json
from datetime import datetime
from typing import Callable, Protocol
from uuid import UUID

from domain.models import MemberProfile, MemberRegistered, Registration, new_member_code, normalize_code


class IMemberStore(Protocol):
    def commit_profile_and_event(self, request_id: UUID, payload_hash: str, registration: Registration,
                                 code_factory: Callable[[], str]) -> tuple[MemberProfile, bool]: ...
    def find(self, member_id: UUID) -> MemberProfile | None: ...
    def by_code(self, code: str) -> MemberProfile | None: ...
    def correct(self, member_id: UUID, registration: Registration, expected_updated_at: datetime) -> MemberProfile | None: ...
    def registered(self, after: int, limit: int) -> list[MemberRegistered]: ...


class RegistrationService:
    def __init__(self, store: IMemberStore, code_factory: Callable[[], str] = new_member_code):
        self.store = store
        self.code_factory = code_factory

    def register(self, registration: Registration, request_id: UUID) -> tuple[MemberProfile, bool]:
        canonical = json.dumps({"name": registration.full_name, "age": registration.age},
                               sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return self.store.commit_profile_and_event(request_id, fingerprint, registration, self.code_factory)

    def resolve(self, code: str) -> MemberProfile | None:
        try:
            canonical = normalize_code(code)
        except ValueError:
            return None
        return self.store.by_code(canonical)

    def get(self, member_id: UUID) -> MemberProfile | None:
        return self.store.find(member_id)

    def correct(self, member_id: UUID, registration: Registration, expected_updated_at: datetime) -> MemberProfile | None:
        return self.store.correct(member_id, registration, expected_updated_at)

    def registered(self, after: int, limit: int) -> list[MemberRegistered]:
        return self.store.registered(after, limit)
