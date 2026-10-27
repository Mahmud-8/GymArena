"""Transfer tested images between CI jobs, then publish without rebuilding them."""
import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES = json.loads((ROOT / "infra/services.json").read_text(encoding="utf-8"))


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def revision():
    value = os.environ["GITHUB_SHA"]
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("Expected a full Git commit SHA")
    return value


def image_record(service, expected_revision):
    folder = service["folder"]
    if not re.fullmatch(r"[a-z][a-z0-9-]*-service", folder):
        raise ValueError("Invalid service image name")
    local = f"gymarena/{folder}:foundation"
    image = json.loads(run("docker", "image", "inspect", local))[0]
    labels = image["Config"]["Labels"]
    if labels.get("org.opencontainers.image.revision") != expected_revision:
        raise ValueError("Image revision differs from the tested commit")
    if labels.get("org.opencontainers.image.source") != "https://github.com/" + os.environ["GITHUB_REPOSITORY"]:
        raise ValueError("Image repository label differs from the workflow repository")
    return {"service": folder, "local_reference": local, "image_id": image["Id"]}


def export_images(directory):
    commit = revision()
    if len(SERVICES) != 8 or len({s["folder"] for s in SERVICES}) != 8:
        raise ValueError("Expected eight distinct services")
    smoke = json.loads((ROOT / "ci-evidence/smoke.json").read_text(encoding="utf-8"))
    if len(smoke["checks"]) != 26 or not all(c["passed"] for c in smoke["checks"]):
        raise ValueError("The full foundation smoke check did not pass")
    if smoke["cross_database_connections_denied"] != 56:
        raise ValueError("The database ownership check is incomplete")
    records = [image_record(service, commit) for service in SERVICES]
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory / "images.tar.gz"
    with gzip.open(archive, "wb", compresslevel=1) as output:
        with subprocess.Popen(["docker", "image", "save", *[r["local_reference"] for r in records]], stdout=subprocess.PIPE) as process:
            shutil.copyfileobj(process.stdout, output)
            if process.wait() != 0:
                raise RuntimeError("Docker could not export the tested images")
    manifest = {"revision": commit, "archive_sha256": sha256(archive), "images": records,
                "smoke_checks_passed": 26, "cross_database_connections_denied": 56}
    (directory / "images.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(records)} tested images for {commit}")


def package_metadata(owner, name):
    endpoint = f"https://api.github.com/users/{owner}/packages/container/{urllib.parse.quote(name, safe='')}"
    request = urllib.request.Request(endpoint, headers={
        "Authorization": "Bearer " + os.environ["GH_TOKEN"],
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            metadata = json.load(response)
        return {"visibility": metadata["visibility"], "package_url": metadata["html_url"],
                "linked_repository": (metadata.get("repository") or {}).get("full_name")}
    except urllib.error.HTTPError as error:
        if error.code not in (401, 403, 404):
            raise
        return {"visibility": "not_readable_with_workflow_token", "metadata_http_status": error.code}


def publish_images(directory, report):
    commit = revision()
    repository = os.environ["GITHUB_REPOSITORY"]
    if repository != "Mahmud-8/GymArena":
        raise ValueError("Publication is restricted to the configured repository")
    channels = {"main": "latest", "develop": "develop", "feature/docker-foundation": "foundation"}
    channel = channels[os.environ["GITHUB_REF_NAME"]]
    manifest = json.loads((directory / "images.json").read_text(encoding="utf-8"))
    if manifest["revision"] != commit or sha256(directory / "images.tar.gz") != manifest["archive_sha256"]:
        raise ValueError("The transferred image archive or revision is inconsistent")
    if {x["service"] for x in manifest["images"]} != {s["folder"] for s in SERVICES}:
        raise ValueError("The tested image set differs from the service inventory")
    with gzip.open(directory / "images.tar.gz", "rb") as source:
        with subprocess.Popen(["docker", "image", "load"], stdin=subprocess.PIPE) as process:
            shutil.copyfileobj(source, process.stdin)
            process.stdin.close()
            if process.wait() != 0:
                raise RuntimeError("Docker could not load the transferred images")
    owner, project = repository.lower().split("/")
    published = []
    report.parent.mkdir(parents=True, exist_ok=True)
    for service in SERVICES:
        loaded = image_record(service, commit)
        exported = next(x for x in manifest["images"] if x["service"] == service["folder"])
        if loaded != exported:
            raise ValueError("Loaded image differs from the image tested by CI")
        package = f"{project}-{service['folder']}"
        image = f"ghcr.io/{owner}/{package}"
        references = [f"{image}:sha-{commit}", f"{image}:{channel}"]
        for reference in references:
            subprocess.run(["docker", "image", "tag", loaded["local_reference"], reference], check=True)
            subprocess.run(["docker", "image", "push", reference], check=True)
        digests = [run("docker", "buildx", "imagetools", "inspect", reference, "--format", "{{.Manifest.Digest}}") for reference in references]
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", digests[0]) or digests[0] != digests[1]:
            raise ValueError("Registry references do not resolve to the same published digest")
        record = {**loaded, "references": references, "registry_digest": digests[0],
                  "digest_reference": image + "@" + digests[0], **package_metadata(owner, package)}
        published.append(record)
        result = {"revision": commit, "run_url": os.environ["GITHUB_SERVER_URL"] + "/" + repository + "/actions/runs/" + os.environ["GITHUB_RUN_ID"],
                  "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                  "tested_images_rebuilt_for_publication": False,
                  "all_eight_published": len(published) == 8, "images": published,
                  "scope": "Foundation images; functional operations remain unimplemented"}
        report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    summary = Path(os.environ["GITHUB_STEP_SUMMARY"])
    with summary.open("a", encoding="utf-8") as stream:
        stream.write("## Eight tested foundation images published\n\n")
        stream.write(f"Commit `{commit}`. All 26 smoke checks and 56 database access denials passed before publication.\n\n")
        stream.write("The publication job loaded the exact tested images and verified both registry tags resolve to the same digest. Functional application operations remain subsequent work.\n\n")
        stream.write("| Image | Registry digest | Visibility |\n| --- | --- | --- |\n")
        for record in published:
            stream.write(f"| `{record['references'][0]}` | `{record['registry_digest']}` | {record['visibility']} |\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export")
    export.add_argument("--directory", type=Path, required=True)
    publish = commands.add_parser("publish")
    publish.add_argument("--directory", type=Path, required=True)
    publish.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "export":
        export_images(args.directory)
    else:
        publish_images(args.directory, args.report)
