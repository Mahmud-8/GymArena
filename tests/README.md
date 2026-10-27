# Foundation verification

`smoke_foundation.py` checks actual HTTP operational endpoints, database isolation and container process restrictions. Its extended mode briefly stops this Compose project's database to verify honest readiness failure, recovery and persisted synthetic data. Run it only against an independent local Compose project. See [the Docker guide](../docs/docker-foundation.md).

Functional acceptance tests will be added with the corresponding features. A passing foundation check does not establish working registration, exercise tracking, scoring, messaging or monitor animation.
