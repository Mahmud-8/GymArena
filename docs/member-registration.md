# Member registration and correction

This slice implements US-17/GYM-17 (FR-09.1, FR-09.3) and US-18/GYM-18
(FR-09.2). It is proposed for integration through a feature pull request;
independent teammate acceptance is separate from automated verification.

Run `docker compose up -d --build --wait`, then open
<http://localhost:8105/kiosk/>. The kiosk supports registration, return by saved
code, profile correction and sign-out. Names support Unicode letters, marks,
spaces, apostrophes, dots and hyphens; whitespace is normalized. Age must be a
whole number from 1 through 120. These bounds are explicit prototype policy.

## API

| Method/path | Access and behavior |
| --- | --- |
| POST `/api/members` | Name/age JSON and UUID4 `Idempotency-Key`. Returns 201 for a new registration, 200 for an identical retry, 409 for a changed retry payload. Creates a confirmation cookie. |
| POST `/api/member-access` | Full private member code. Confirms a member and creates a cookie. |
| GET `/api/member-session` | Confirmed member's profile and CSRF token. |
| DELETE `/api/member-session` | Clears the browser confirmation cookie. |
| GET `/api/members/{member_id}` | Own confirmed profile or explicit authorized staff access. |
| PATCH `/api/members/{member_id}` | Valid name/age and `expected_updated_at`. Requires ownership plus `X-CSRF-Token`, or explicit staff authorization. Returns 409 on stale edits. ID/code remain unchanged. |
| GET `/api/member-registrations` | Staff-authorized ordered feed with `after` cursor and `limit` 1–200. Includes event ID, member ID, registration display name and sequence; excludes age/code. |

The feed records the name at registration, not a live projection of later
corrections. Future consumers must use member IDs and refresh authorized current
display data where required. No scoring consumer or zero-point public board is
implemented yet.

## Confirmation and shared kiosk behavior

Each member receives a separate random 80-bit code, formatted
`GA-XXXX-XXXX-XXXX-XXXX`. Treat it as a private credential. Confirmation uses a
signed, HttpOnly, SameSite=Strict cookie scoped to `/api` for 15 minutes; member
corrections require a separate CSRF header. The UI holds profile data in memory,
clears confirmation on reload, and signs out after two idle minutes. Browser
sign-out clears the cookie; it does not revoke a stolen copy server-side.

An explicit `X-Staff-Key` authenticates local prototype staff API use. Bootstrap
generates it in the Member credential volume alongside the session key, with
neither included in the source, UI, logs or test reports. This is not a complete
staff identity/role directory, recovery flow or production login system. Do not
expose the prototype publicly. For an HTTPS deployment, set
`MEMBER_COOKIE_SECURE=true`; localhost HTTP defaults to false. The service rejects
foreign-Origin writes. API responses are not cached.

## Code and persistence traceability

| Design responsibility | Implemented source |
| --- | --- |
| IMemberProfile boundary | `services/member-service/api/routes.py`: MemberProfileApi |
| Registration use cases / IMemberStore port | `application/profiles.py`: RegistrationService, IMemberStore |
| Member profile / registration event invariants | `domain/models.py`: Registration, MemberProfile, MemberRegistered |
| Member-owned SQL store | `infrastructure/repository.py`: SqlMemberStore |
| Confirmation and correction authorization | `infrastructure/security.py`: MemberConfirmation |
| Kiosk forms and profile | `apps/web/src/` |

The shortened application/domain/infrastructure paths above are relative to
`services/member-service/`. The code refines the original design class model;
it does not claim that all planned class names/methods exist.

Original `db/001_initial.sql` is retained. Startup applies additive migration
`db/002_registration_requests.sql` under a PostgreSQL advisory lock. It adds an
idempotency-request table referencing Member-owned profiles: five Member tables,
39 tables across all services and two scoring views. No existing profile or
password is reset. Registration locks its retry key and the feed counter,
then commits profile, request fingerprint and one outbox event in one transaction.
An allocated sequence cannot be observed ahead of an earlier uncommitted event.
Code collisions retry five times, then roll back with a sanitized 503 response.
Corrections use optimistic timestamp matching to prevent silent lost updates.

## Verification

Use a disposable isolated Compose project. The member acceptance runner refuses
the normal project name and removes only its captured synthetic request UUIDs.
It does not reset the feed counter or delete unrelated profiles.

```bash
export COMPOSE_PROJECT_NAME=gymarena-ci-local
docker compose up -d --build --wait
python tests/smoke_foundation.py --exercise-recovery --report ci-evidence/smoke.json
python tests/smoke_members.py --report ci-evidence/members.json
```

On PowerShell use `$env:COMPOSE_PROJECT_NAME='gymarena-ci-local'` and run the
same remaining commands. Choose alternative port overrides if the normal stack
is already running. The workflow executes both suites. The member runner also
runs ten domain/confirmation unit tests inside the actual runtime image, then
exercises invalid inputs, private access, corrections, retries, concurrent
registrations, atomic collision rollback, feed paging and restart persistence.
Browser interaction/layout checks are separate manual evidence, not inferred
from these API checks. No load/performance result is claimed.

## Remaining scope

Member weight measurement (FR-10), recognition, tracking, session/challenge
logic, memberships, notifications, scoring and the animated public leaderboard
remain unimplemented. Their health endpoints and owned schemas remain available.
