"""Cross-service contract tests for the GymArena repository.

These tests check the agreements that keep eight independently deployed
services consistent: the service inventory, each service's declared CONFIG,
the Compose topology, the owned SQL schema, the dependency graph, CODEOWNERS
and the committed foundation verification evidence.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SERVICES = json.loads((ROOT / "infra/services.json").read_text(encoding="utf-8"))
REQUIRED_KEYS = {"id", "folder", "name", "owner", "interface", "requirements",
                 "port", "database", "db_user", "tables", "views",
                 "dependencies", "external_interfaces"}


def _compose():
    return yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))


def _readme_table():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| ([\w-]+-service) \| ([^|]+?) \| \[@([\w-]+)\]\([^)]+\) \| (FR-\d\d, FR-\d\d) \|$",
                      text, flags=re.MULTILINE)
    return {folder: (owner.strip(), handle, requirements) for folder, owner, handle, requirements in rows}


def _owner_handle(folder):
    text = (ROOT / "services" / folder / "README.md").read_text(encoding="utf-8")
    match = re.search(r"^Owner: (.+?) \(\[@([\w-]+)\]", text, flags=re.MULTILINE)
    assert match, f"{folder} README does not declare an owner"
    return match.group(1), match.group(2)


def _schema(folder):
    text = (ROOT / "services" / folder / "db" / "001_initial.sql").read_text(encoding="utf-8")
    tables = set(re.findall(r'CREATE TABLE "(\w+)"', text))
    views = set(re.findall(r"CREATE VIEW (\w+) AS", text))
    references = set(re.findall(r'REFERENCES "(\w+)"', text))
    return text, tables, views, references


def test_TC_REPO_01_service_inventory_is_complete_and_unique():
    """TC-REPO-01: eight services with unique identity, port, database and FR pairs."""
    assert len(SERVICES) == 8
    for service in SERVICES:
        assert REQUIRED_KEYS <= set(service), f"{service.get('id')} misses keys"
        assert re.fullmatch(r"FR-\d\d, FR-\d\d", service["requirements"])
        assert service["db_user"] == service["database"]
    for key in ("id", "folder", "port", "database", "requirements"):
        values = [s[key] for s in SERVICES]
        assert len(values) == len(set(values)), f"duplicate {key}"
    assert sorted(s["port"] for s in SERVICES) == list(range(8101, 8109))


def test_TC_REPO_02_each_service_config_matches_the_inventory(service_apps):
    """TC-REPO-02: every shipped CONFIG equals its inventory record."""
    for service in SERVICES:
        _, config = service_apps[service["folder"]]
        assert config == {
            "folder": service["folder"],
            "name": service["name"],
            "interface": service["interface"],
            "requirements": service["requirements"],
            "tables": service["tables"],
            "views": service["views"],
            "dependencies": service["dependencies"],
            "external_interfaces": service["external_interfaces"],
        }, service["folder"]


def test_TC_REPO_03_compose_wires_every_service_to_its_own_database():
    """TC-REPO-03: Compose defines the eight services with isolated credentials."""
    compose = _compose()
    names = set(compose["services"])
    expected = {s["folder"] for s in SERVICES} | {"database", "credentials"}
    assert names == expected
    for service in SERVICES:
        block = compose["services"][service["folder"]]
        assert block["environment"]["DB_NAME"] == service["database"]
        assert block["environment"]["DB_USER"] == service["db_user"]
        assert block["environment"]["DB_PASSWORD_FILE"] == "/credentials/password"
        assert any(str(service["port"]) in str(port) for port in block["ports"])
        assert block["depends_on"]["database"]["condition"] == "service_healthy"
        assert block["read_only"] is True
        assert block["cap_drop"] == ["ALL"]
        assert "no-new-privileges:true" in block["security_opt"]


def test_TC_REPO_04_owned_schema_matches_the_declared_tables_and_views():
    """TC-REPO-04: each schema creates exactly its declared tables and views."""
    for service in SERVICES:
        text, tables, views, references = _schema(service["folder"])
        assert tables == set(service["tables"]), service["folder"]
        assert views == set(service["views"]), service["folder"]
        assert text.lstrip().startswith("--")
        assert "BEGIN;" in text and "COMMIT;" in text
        # Remote IDs are comments only: no foreign key may cross a database.
        assert references <= tables, f"{service['folder']} has a foreign key outside its schema"


def test_TC_REPO_05_service_dependencies_resolve_to_known_services():
    """TC-REPO-05: every dependency URL names the declared interface and service."""
    folders = {s["folder"] for s in SERVICES}
    interfaces = {s["interface"]: s["folder"] for s in SERVICES}
    for service in SERVICES:
        targets = set()
        for interface, url in service["dependencies"].items():
            match = re.fullmatch(r"http://([\w-]+):8000", url)
            assert match, f"{service['folder']} has an invalid dependency URL {url}"
            assert match.group(1) in folders
            assert interface in interfaces, f"{service['folder']} names unknown interface {interface}"
            assert interfaces[interface] == match.group(1)
            targets.add(match.group(1))
        assert service["folder"] not in targets


def test_TC_REPO_06_dependency_cycles_stay_inside_the_documented_trio():
    """TC-REPO-06: the only business cycle is the documented Challenge/Session/Scoring one."""
    documented = {"challenge-service", "session-service", "scoring-service"}
    graph = {s["folder"]: {re.fullmatch(r"http://([\w-]+):8000", url).group(1)
                           for url in s["dependencies"].values()}
             for s in SERVICES}
    cyclic = set()
    for start in graph:
        stack, seen = [(start, [start])], set()
        while stack:
            node, path = stack.pop()
            for target in graph[node]:
                if target == start:
                    cyclic.update(path)
                elif target not in seen:
                    seen.add(target)
                    stack.append((target, path + [target]))
    assert cyclic <= documented, f"undocumented dependency cycle through {sorted(cyclic - documented)}"
    adr = (ROOT / "docs/architecture-decisions/0001-eight-service-runtime.md").read_text(encoding="utf-8")
    assert "startup cycle between Challenge, Session and Scoring" in adr


def test_TC_REPO_07_codeowners_and_readme_agree_with_the_inventory():
    """TC-REPO-07: ownership is consistent across CODEOWNERS and both READMEs."""
    codeowners = (ROOT / ".github/CODEOWNERS").read_text(encoding="utf-8")
    table = _readme_table()
    assert set(table) == {s["folder"] for s in SERVICES}
    for service in SERVICES:
        owner, handle = _owner_handle(service["folder"])
        assert owner == service["owner"]
        assert table[service["folder"]] == (service["owner"], handle, service["requirements"])
        assert f"/services/{service['folder']}/ @{handle}" in codeowners


def test_TC_REPO_08_dockerfiles_build_a_non_root_read_only_runtime():
    """TC-REPO-08: every image runs as UID 10001, exposes 8000 and is health checked."""
    for service in SERVICES:
        text = (ROOT / "services" / service["folder"] / "Dockerfile").read_text(encoding="utf-8")
        assert "USER 10001:10001" in text
        assert "EXPOSE 8000" in text
        assert "HEALTHCHECK" in text and "/health/ready" in text
        assert "ADD http" not in text
        assert "COPY --chown=10001:10001 packages/runtime/gymarena_runtime ./gymarena_runtime" in text
        assert f"COPY --chown=10001:10001 services/{service['folder']}/api ./api" in text


def test_TC_REPO_09_service_readmes_state_their_requirements_and_interface():
    """TC-REPO-09: each service README names its FRs and planned interface."""
    for service in SERVICES:
        text = (ROOT / "services" / service["folder"] / "README.md").read_text(encoding="utf-8")
        assert f"Requirements: {service['requirements']}" in text
        assert service["interface"] in text
        assert "remain planned" in text or "remain subsequent work" in text


def test_TC_REPO_10_committed_foundation_evidence_covers_all_eight_services():
    """TC-REPO-10: the committed verification record reports every service passed."""
    evidence = json.loads((ROOT / "docs/docker-foundation-verification.json").read_text(encoding="utf-8"))
    assert evidence["scope"].startswith("Eight-service Docker foundation")
    smoke = evidence["runtime_smoke_checks"]
    checks = smoke["checks"]
    http_checks = [c for c in checks if c["check"] == "http_and_contract_boundary"]
    assert {c["service"] for c in http_checks} == {s["folder"] for s in SERVICES}
    assert all(c["passed"] for c in checks)
    assert smoke["cross_database_connections_denied"] == 7 * len(SERVICES)
    assert evidence["functional_features_tested"] is False
    assert smoke["functional_features_tested"] is False


def test_TC_REPO_11_schema_fingerprints_match_the_verified_evidence():
    """TC-REPO-11: the SQL schemas are byte-identical to the verified revision."""
    evidence = json.loads((ROOT / "docs/docker-foundation-verification.json").read_text(encoding="utf-8"))
    audit = {row["service"]: row for row in evidence["static_audit"]["services"]}
    assert evidence["static_audit"]["service_count"] == len(SERVICES)
    for service in SERVICES:
        path = ROOT / "services" / service["folder"] / "db" / "001_initial.sql"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == audit[service["folder"]]["schema_sha256"], service["folder"]
        assert audit[service["folder"]]["tables"] == len(service["tables"])
        assert audit[service["folder"]]["views"] == len(service["views"])
