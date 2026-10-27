# GitHub foundation delivery

The repository contains the eight-service operational foundation and its Docker/CI configuration. The [foundation workflow](https://github.com/Mahmud-8/GymArena/actions/workflows/foundation.yml) verifies each integrated revision before publishing its images.

The original [successful hosted foundation run](https://github.com/Mahmud-8/GymArena/actions/runs/40543984144) built all eight services, passed all 26 smoke checks and published all eight public packages. The checks include 56 denied cross-service database connections, non-root/read-only service containers, database outage detection, recovery and persistence. Its [PR verification run](https://github.com/Mahmud-8/GymArena/actions/runs/40544061523) passed independently.

## Review and integration

Feature work enters `develop` through a pull request. A separate pull request promotes the agreed integration baseline from `develop` to `main`. GitHub checks identify the tested commit and actual workflow result; an open PR or a source file alone does not establish integration. The initial foundation PR is [PR 1](https://github.com/Mahmud-8/GymArena/pull/1).

This document does not assert an independent teammate approval. Branch protection and collaborator/TA access are separate repository-administration items recorded in [setup status](setup-status.md).

## Public registry packages

| Service | Public GHCR package |
| --- | --- |
| Exercise Tracking | [gymarena-exercise-tracking-service](https://github.com/users/Mahmud-8/packages/container/package/gymarena-exercise-tracking-service) |
| Membership | [gymarena-membership-service](https://github.com/users/Mahmud-8/packages/container/package/gymarena-membership-service) |
| Session Control | [gymarena-session-service](https://github.com/users/Mahmud-8/packages/container/package/gymarena-session-service) |
| Notifications | [gymarena-notification-service](https://github.com/users/Mahmud-8/packages/container/package/gymarena-notification-service) |
| Member Profiles | [gymarena-member-service](https://github.com/users/Mahmud-8/packages/container/package/gymarena-member-service) |
| Face Recognition | [gymarena-recognition-service](https://github.com/users/Mahmud-8/packages/container/package/gymarena-recognition-service) |
| Assessment and Challenges | [gymarena-challenge-service](https://github.com/users/Mahmud-8/packages/container/package/gymarena-challenge-service) |
| Scoring and Leaderboards | [gymarena-scoring-service](https://github.com/users/Mahmud-8/packages/container/package/gymarena-scoring-service) |

Each package has source-commit tags `sha-<full-sha>`. Successful pushes to the foundation branch also publish `foundation`; `develop` pushes publish `develop`; successful `main` pushes publish `latest`. Use the publication artifact's digest reference when an immutable image identity is required.

## Run and inspect

Clone the selected repository branch and run from its root:

```sh
docker compose up
```

The default Compose command builds the source revision. For published-image identifiers and registry digests, download `ghcr-publication-<sha>` from the corresponding successful workflow run. For operational results, download `foundation-evidence-<sha>`. See [Docker setup](docker-foundation.md) and [CI execution](ci-and-ghcr.md).

This is a Docker foundation, not the complete functional GymArena application. Workout processing, registration workflows, scoring policy, reminders, authentication, device integration and monitor animation remain implementation work.
