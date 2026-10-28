# Foundation CI and GHCR publication

`.github/workflows/foundation.yml` builds all eight services, runs operational and member acceptance checks, and publishes the exact tested images on configured release branches. The member suite verifies registration/profile correction. Exercise tracking, scoring, reminders and animation remain later work.

## Execution

Pushes to `main`, `develop` and `feature/docker-foundation` run verification followed by publication. Pull requests targeting `main` or `develop` run verification with no package publication. Manual runs are supported once the workflow exists on the default branch. No automatic merge is configured.

The verification job has read-only repository permission. It starts a unique Compose project on an Ubuntu runner, waits for all services and PostgreSQL, and runs `tests/smoke_foundation.py --exercise-recovery` followed by `tests/smoke_members.py`. The operational checks include 56 denied cross-service connections, non-root processes, read-only filesystems, readiness 503 during a database outage, recovery and synthetic persistence. The Member suite covers domain/confirmation rules, real registration/correction transactions, access controls, retries, concurrency, feed pagination and restart persistence. Both JSON reports are retained with the run evidence.

After verification, `scripts/ci_images.py export` checks the source/revision labels and exports all eight tested image IDs into one compressed Docker archive with a SHA256 manifest. The temporary image-transfer artifact lasts seven days; smoke results and logs last 90 days. Ephemeral runner databases and generated credentials are removed after each verification job.

The publication job runs only after successful verification and only for the configured repository and branches. It has `packages: write`, authenticates with the short-lived repository `GITHUB_TOKEN`, verifies and loads the transferred images, and checks every image ID and revision. It publishes without rebuilding the images. Personal access tokens and real gym credentials are not required.

## Images and evidence

Images use the form `ghcr.io/mahmud-8/gymarena-member-service:sha-<full-commit-sha>`, with corresponding names for the other seven service folders. A moving tag identifies the branch channel: `foundation` for the foundation branch, `develop` for the integration branch, or `latest` for `main`. The commit tag identifies the source revision; deployment references should use the recorded registry digest when an immutable image identity is required.

Each image carries the source repository and full Git revision as OCI labels. The publisher reads each registry digest back and checks that the commit and channel tags agree. It retains `published-images.json` as a 90-day artifact, containing the image IDs, digests, registry references, workflow URL and package visibility when the package metadata endpoint is accessible. A failed partial publication retains the images recorded before that failure.

Package visibility follows GitHub's registry defaults. A public source repository does not itself prove that a newly published package can be pulled anonymously. Inspect the package's access settings before giving an unauthenticated pull command to a reviewer. The pipeline records actual visibility where available and does not claim anonymous access from a successful authenticated push.

Open the repository Actions tab, select `GymArena Foundation CI and GHCR`, and inspect both jobs. Download `foundation-evidence-<sha>` for the smoke report and logs, and `ghcr-publication-<sha>` for registry publication evidence. A passing verification job without a successful publication job does not establish completion of this step.

The original `docker-foundation-verification.json` is a dated local test snapshot from before publication. Hosted CI results and publication artifacts identify the newly tested commit separately.

## References

- [GitHub publishing Docker images](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images)
- [GitHub Container registry authentication and package visibility](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker registry manifest inspection](https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/)
