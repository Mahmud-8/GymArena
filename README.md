# GymArena

GymArena combines personalized camera-based fitness challenges with subscription expiry monitoring and WhatsApp reminders. The first prototype supports squats and jumping jacks, one participant or a local 1v1 session, one camera and a shared display.

Alamein International University · CSE454 Advanced Software Engineering

## Project links

- Repository: https://github.com/Mahmud-8/GymArena
- Figma design foundations: https://www.figma.com/design/BLI0uf9XDv3LMcz7EUFYSU
- [26-screen interface source](design/index.html) and [SVG screen files](design/screens/). Download the HTML file and open it in a browser to review the interactive prototype.
- Native Figma screen import is pending because the connected Starter account reached its native-editing tool allowance.
- Jira board: **Pending — the board is being prepared.** Replace this line with the real board URL when available.

## Current status

This local foundation adds eight separately runnable FastAPI services, PostgreSQL schemas with isolated service logins, multi-stage Dockerfiles and Docker Compose. Endpoints currently cover service metadata, liveness and database readiness. Application features, authentication, hardware integration and performance validation remain planned work. Screens and example values are design data, not measured results.

From the repository root, run `docker compose up`. See [Docker setup and current verification](docs/docker-foundation.md).

The [foundation CI and GHCR workflow](.github/workflows/foundation.yml) builds the eight services, runs operational smoke checks, and publishes the tested images after verification. See [CI execution and evidence](docs/ci-and-ghcr.md) for the branch triggers, image tags and retained results. Functional application features remain subsequent work.

## Team

| Member | GitHub |
| --- | --- |
| Mahmoud Emad | [Mahmud-8](https://github.com/Mahmud-8) |
| Ahmed Ebrahim | [AhmedEbrahem25](https://github.com/AhmedEbrahem25) |
| Mohamed Soliman | [xchan404](https://github.com/xchan404) |
| Mohamed Hegazy | [mohamed-hegazy1](https://github.com/mohamed-hegazy1) |

## Services and owners

| Service folder | Owner | GitHub | Requirements |
| --- | --- | --- | --- |
| exercise-tracking-service | Mahmoud Emad | [@Mahmud-8](https://github.com/Mahmud-8) | FR-01, FR-02 |
| membership-service | Mahmoud Emad | [@Mahmud-8](https://github.com/Mahmud-8) | FR-03, FR-04 |
| session-service | Ahmed Ebrahim | [@AhmedEbrahem25](https://github.com/AhmedEbrahem25) | FR-05, FR-06 |
| notification-service | Ahmed Ebrahim | [@AhmedEbrahem25](https://github.com/AhmedEbrahem25) | FR-07, FR-08 |
| member-service | Mohamed Soliman | [@xchan404](https://github.com/xchan404) | FR-09, FR-10 |
| recognition-service | Mohamed Soliman | [@xchan404](https://github.com/xchan404) | FR-11, FR-12 |
| challenge-service | Mohamed Hegazy | [@mohamed-hegazy1](https://github.com/mohamed-hegazy1) | FR-13, FR-14 |
| scoring-service | Mohamed Hegazy | [@mohamed-hegazy1](https://github.com/mohamed-hegazy1) | FR-15, FR-16 |

The monorepo now has eight separate service foundations, each with its own FastAPI process and Dockerfile, matching the PM1 design and per-service container requirement. Each service uses only its own database login. A notification worker, local device adapters and the web application remain later work. See [the deployment decision](docs/architecture-decisions/0001-eight-service-runtime.md).

## Planned technology stack

| Area | Choice | Reason |
| --- | --- | --- |
| Web interface | React, TypeScript and Vite | One component-based interface for kiosk, trainer and staff views. |
| UI styling and charts | CSS variables, CSS modules and Recharts | Reusable styles and simple charts that match the Figma screens. |
| Routing and API state | React Router and TanStack Query | Keep page navigation and server data handling separate. |
| Backend | Python 3.12 and FastAPI | Share Python data contracts with the vision code; provide REST APIs and WebSocket session updates. |
| Persistence | PostgreSQL, SQLAlchemy and Alembic | Transactions, uniqueness constraints and versioned migrations for results, renewals and reminder records. |
| Exercise tracking | OpenCV and MediaPipe Pose Landmarker | Capture frames and extract pose landmarks for up to two assigned camera positions. |
| Face identification | OpenCV YuNet and SFace | Local enrollment and matching with quality checks, explicit confirmation and code fallback. |
| Scale adapter | pySerial behind IScaleInput | Read a compatible USB/serial scale; implement the selected device protocol behind the adapter. |
| Reminder processing | Python worker with PostgreSQL-backed jobs/outbox | Keep jobs persistent, recheck expiry before delivery and prevent duplicate releases. |
| Messaging | WhatsApp Business Platform Cloud API | Use designated test recipients and record available delivery acknowledgements. |
| Development and checks | Docker Compose, pytest, Vitest and Playwright | Repeatable local setup and domain, UI and integration checks as code is implemented. |

Exact dependency versions will be pinned in lockfiles after a camera, model and scale compatibility check. The pose model does not establish member identity: confirmed floor positions and interruption recovery remain application responsibilities.

## Planned folder structure

| Path | Purpose |
| --- | --- |
| `apps/web/` | React kiosk, session display and staff dashboard. |
| `apps/api/` | Reserved for an optional future gateway; services currently expose separate APIs. |
| `apps/worker/` | Persistent reminders and message delivery jobs. |
| `apps/device-agent/` | Local camera and electronic-scale adapters. |
| `services/` | Eight owned service folders listed above. |
| `packages/contracts/` | Shared API schemas and domain event definitions. |
| `packages/ui/` | Shared interface components and design tokens. |
| `docs/` | Architecture decisions, GUI traceability and setup status. |
| `tests/` | Planned cross-service acceptance and integration checks. |
| `infra/` | Docker bootstrap, dependency pins and service inventory. |
| `.github/` | CODEOWNERS and pull request guidance. |

## Branches and collaboration

- `main`: proposal/release baseline. A protection rule requiring one approved pull request and resolved conversations has been prepared; GitHub is waiting for owner re-authentication before it can be saved. Until that step is confirmed, do not treat `main` as protected.
- `develop`: integration branch for reviewed service work.
- `feature/<service-folder>`: one branch for each service, maintained by its owner in the table above.

Normal flow: update your assigned feature branch from `develop`, implement one story, open a pull request to `develop`, request a teammate review and merge after review. Open a separate reviewed pull request from `develop` to `main` for an agreed baseline. CODEOWNERS maps service folders to their owners; a branch name alone does not restrict who can push to it.

See [CONTRIBUTING.md](CONTRIBUTING.md) for commands and [setup status](docs/setup-status.md) for remaining external links and invitations.

## Rules carried from the proposal

- Loss of reliable tracking for either participant pauses both counters and the common active timer. Paused intervals do not consume active challenge time.
- Unfinished repetitions are discarded on pause. Confirm participant assignments before resuming.
- Incomplete, identity-uncertain and discomfort-stopped attempts have no points change and no automatic winner.
- Only valid finalized outcomes enter scoring and approved history. A result changes points at most once; practice attempts do not enter the leaderboard.
- Challenge targets, point values, levels and winner rules require trainer approval before ranked use. Prototype screen values are illustrative.
- Renewals cancel obsolete pending reminders. Recheck the current expiry date before sending.
- Face enrollment is optional. A code-based alternative remains available. A missing camera-session record does not prove absence from the gym.

## Technical references

- [React documentation](https://react.dev/)
- [FastAPI features](https://fastapi.tiangolo.com/features/) and [WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [MediaPipe Pose Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python)
- [OpenCV face detection and recognition](https://docs.opencv.org/4.x/d0/dd4/tutorial_dnn_face.html)
- [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [WhatsApp developer hub](https://whatsappbusiness.com/developers/developer-hub/)
