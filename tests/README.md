# Foundation verification

`smoke_foundation.py` checks actual HTTP operational endpoints, database isolation and container process restrictions. Its extended mode briefly stops this Compose project's database to verify honest readiness failure, recovery and persisted synthetic data. Run it only against an independent local Compose project. See [the Docker guide](../docs/docker-foundation.md).

`unit/` holds the pytest suite that checks the eight service HTTP contracts, readiness logic, database settings and repository agreements without Docker. Every test name carries its report ID (`TC-ETS-01`, `TC-REPO-03`, ...). See [unit and contract testing](../docs/testing.md).

Functional acceptance tests will be added with the corresponding features. A passing foundation check does not establish working registration, exercise tracking, scoring, messaging or monitor animation.
