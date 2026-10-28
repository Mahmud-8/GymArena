"""IMemberProfile registration/correction slice; measurement remains planned."""
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, UUID4, field_validator

from gymarena_runtime import create_app
from gymarena_runtime.app import DatabaseSettings
from application.profiles import RegistrationService
from domain.models import AuthContext, CodeAllocationUnavailable, Registration, RegistrationConflict, StaleProfile, normalize_name
from infrastructure.repository import SqlMemberStore
from infrastructure.security import MemberConfirmation, SESSION_SECONDS

CONFIG = {
    "folder": "member-service", "name": "Member Profiles and Measurements", "interface": "IMemberProfile",
    "requirements": "FR-09, FR-10",
    "tables": ["members", "weight_measurements", "member_registered_outbox", "registration_feed_state", "member_registration_requests"],
    "views": [], "dependencies": {}, "external_interfaces": ["IScaleInput"],
    "implemented_operations": ["register", "resolve", "get", "correct", "registered"],
}


class RegistrationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    full_name: str = Field(min_length=1, max_length=120)
    age: int = Field(strict=True, ge=1, le=120)

    @field_validator("full_name")
    @classmethod
    def valid_name(cls, value):
        return normalize_name(value)


class CorrectionBody(RegistrationBody):
    expected_updated_at: datetime

    @field_validator("expected_updated_at")
    @classmethod
    def timezone_required(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("A timezone is required for the profile version.")
        return value


class AccessBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    member_code: str = Field(min_length=1, max_length=80)


class MemberView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    member_id: UUID
    full_name: str
    age: int
    member_code: str
    created_at: datetime
    updated_at: datetime


class SessionView(BaseModel):
    member: MemberView
    csrf_token: str
    expires_in: int = SESSION_SECONDS


class MemberProfileApi:
    def __init__(self, registration: RegistrationService, confirmation: MemberConfirmation):
        self.registration = registration
        self.confirmation = confirmation
        self.router = router = APIRouter(prefix="/api", tags=["member profiles"])
        principal = Depends(confirmation.authorize)

        @router.post("/members", response_model=SessionView, status_code=201)
        def register(body: RegistrationBody, response: Response,
                     idempotency_key: Annotated[UUID4, Header()]):
            profile, created = self.register(body, idempotency_key)
            if not created:
                response.status_code = 200
            return {"member": profile, "csrf_token": confirmation.issue(response, profile.member_id)}

        @router.post("/member-access", response_model=SessionView)
        def resolve(body: AccessBody, response: Response):
            profile = self.resolve(body.member_code)
            return {"member": profile, "csrf_token": confirmation.issue(response, profile.member_id)}

        @router.get("/member-session", response_model=SessionView)
        def current(context: AuthContext = principal):
            if context.role != "member" or context.member_id is None:
                raise HTTPException(403, "Use a confirmed member session for this endpoint.")
            return {"member": self.get(context.member_id, context), "csrf_token": confirmation.csrf(context)}

        @router.delete("/member-session", status_code=204)
        def leave(response: Response):
            confirmation.clear(response)

        @router.get("/members/{member_id}", response_model=MemberView)
        def get(member_id: UUID, context: AuthContext = principal):
            return self.get(member_id, context)

        @router.patch("/members/{member_id}", response_model=MemberView)
        def correct(member_id: UUID, body: CorrectionBody, request: Request, context: AuthContext = principal):
            confirmation.require_csrf(request, context)
            return self.correct(member_id, body, context)

        @router.get("/member-registrations")
        def registered(after: Annotated[int, Query(ge=0)] = 0,
                       limit: Annotated[int, Query(ge=1, le=200)] = 100,
                       context: AuthContext = principal):
            return self.registered(after, limit, context)

    def register(self, body, request_id):
        return self.registration.register(Registration(body.full_name, body.age), request_id)

    def resolve(self, code):
        profile = self.registration.resolve(code)
        if profile is None:
            raise HTTPException(401, "That member code was not recognized. Check the complete code and try again.")
        return profile

    def get(self, member_id, context):
        if not context.may_access(member_id):
            raise HTTPException(403, "This session cannot access another member's profile.")
        profile = self.registration.get(member_id)
        if profile is None:
            raise HTTPException(404, "Member profile not found.")
        return profile

    def correct(self, member_id, body, context):
        if not context.may_access(member_id):
            raise HTTPException(403, "This session cannot correct another member's profile.")
        profile = self.registration.correct(member_id, Registration(body.full_name, body.age), body.expected_updated_at)
        if profile is None:
            raise HTTPException(404, "Member profile not found.")
        return profile

    def registered(self, after, limit, context):
        if context.role != "staff":
            raise HTTPException(403, "The registration feed requires authorized staff access.")
        batch = self.registration.registered(after, limit + 1)
        events = batch[:limit]
        return {"events": events, "next_cursor": events[-1].sequence if events else after, "has_more": len(batch) > limit}


store = SqlMemberStore(DatabaseSettings.from_environment())


@asynccontextmanager
async def lifespan(_app):
    store.migrate()
    yield


app = create_app(CONFIG, lifespan=lifespan)
app.include_router(MemberProfileApi(RegistrationService(store), MemberConfirmation.from_environment()).router)


@app.middleware("http")
async def privacy_and_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if request.method not in {"GET", "HEAD", "OPTIONS"} and origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
        return JSONResponse(status_code=403, content={"detail": "Use the current GymArena kiosk to submit this request."})
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.exception_handler(RequestValidationError)
async def invalid_fields(_request, error):
    fields = {}
    for detail in error.errors():
        fields[str(detail["loc"][-1])] = detail["msg"].removeprefix("Value error, ")
    return JSONResponse(status_code=422, content={"detail": "Check the highlighted fields.", "fields": fields})


@app.exception_handler(RegistrationConflict)
async def retry_conflict(_request, _error):
    return JSONResponse(status_code=409, content={"detail": "This registration request already saved different details. Retry the original details or start a new registration."})


@app.exception_handler(StaleProfile)
async def stale_profile(_request, _error):
    return JSONResponse(status_code=409, content={"detail": "This profile changed while you were editing. Reload the profile before saving again."})


@app.exception_handler(psycopg.Error)
@app.exception_handler(CodeAllocationUnavailable)
async def unavailable_database(_request, _error):
    return JSONResponse(status_code=503, content={"detail": "Member details are temporarily unavailable. Your form has been kept; please retry."})


web_root = Path(os.environ.get("GYMARENA_WEB_ROOT", "/app/web"))
if web_root.is_dir():
    app.mount("/kiosk", StaticFiles(directory=web_root, html=True), name="kiosk")
