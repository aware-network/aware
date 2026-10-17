"""Review-profile successors exclude earlier refusal semantics without widening extras."""

import json
import subprocess
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").is_file()
)
INPUTS = json.loads(
    (
        ROOT / "docs/reports/workspace-reviewed-refusal-artifact-inputs-20261017.json"
    ).read_text()
)
PREVIOUS = "5ecb9539f53e21ddcfbb88a6422ff6a162e7d7aa"
VERSIONS = {row["package"]: row for row in INPUTS["versions"]}


def project(row):
    return tomllib.loads((ROOT / row["home"] / "pyproject.toml").read_text())["project"]


@pytest.mark.parametrize("row", INPUTS["versions"], ids=lambda row: row["package"])
def test_review_profile_excludes_predecessor_and_next_minor(row):
    current = project(row)
    declarations = current["dependencies"] + current.get(
        "optional-dependencies", {}
    ).get("setup_review", [])
    for raw in declarations:
        req = Requirement(raw)
        name = canonicalize_name(req.name)
        if name in VERSIONS:
            selected = VERSIONS[name]
            assert selected["candidate"] in req.specifier
            assert selected["current"] not in req.specifier
            ceiling = "0.2.0" if name.endswith("fs-adapter") else "0.3.0"
            assert ceiling not in req.specifier


@pytest.mark.parametrize("row", INPUTS["versions"], ids=lambda row: row["package"])
def test_unrelated_dependencies_extras_and_launchers_preserved(row):
    """Compare declarations to the original qualified metadata, not a duplicate list."""
    previous = tomllib.loads(
        subprocess.check_output(
            ["git", "show", PREVIOUS + ":" + row["home"] + "/pyproject.toml"],
            cwd=ROOT,
            text=True,
        )
    )["project"]
    current = project(row)
    assert current["name"] == previous["name"]
    assert current["requires-python"] == previous["requires-python"]
    assert current.get("scripts") == previous.get("scripts")
    assert current.get("entry-points") == previous.get("entry-points")
    assert current["version"] == row["candidate"]
    assert set(current.get("optional-dependencies", {})) == set(
        previous.get("optional-dependencies", {})
    )
    groups = [(previous["dependencies"], current["dependencies"])]
    groups.extend(
        (old, current["optional-dependencies"][extra])
        for extra, old in previous.get("optional-dependencies", {}).items()
    )
    for before, after in groups:
        assert len(before) == len(after)
        for old, new in zip(before, after, strict=True):
            old_req, new_req = Requirement(old), Requirement(new)
            assert old_req.name == new_req.name
            assert old_req.extras == new_req.extras
            assert old_req.marker == new_req.marker
            if old != new:
                assert canonicalize_name(old_req.name) in VERSIONS
                assert {str(s) for s in new_req.specifier if s.operator == "<"} == {
                    str(s) for s in old_req.specifier if s.operator == "<"
                }


def test_existing_registration_homes_and_old_freeze_stay_separate():
    module = tomllib.loads(
        (
            ROOT / "workspaces/aware_workspace/modules/workspace/aware.module.toml"
        ).read_text()
    )
    text = json.dumps(module)
    for row in INPUTS["versions"]:
        assert row["home"].split("modules/workspace/", 1)[1] in text
    original = json.loads(
        (
            ROOT
            / "docs/reports/workspace-a1-reviewed-workflow-interface-inputs-20261016-r2.json"
        ).read_text()
    )
    old_versions = {row["package"]: row for row in original["versions"]}
    for name, row in VERSIONS.items():
        assert old_versions[name]["candidate"] == row["current"]
