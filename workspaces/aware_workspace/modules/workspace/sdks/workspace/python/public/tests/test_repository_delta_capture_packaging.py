"""Producer-only metadata and original resolver qualification."""

import json
import subprocess
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[9]
WORKSPACE = ROOT / "workspaces/aware_workspace/modules/workspace"


@pytest.mark.parametrize(
    "path,name,version",
    [
        ("sdks/workspace/python/public", "aware-workspace-sdk", "0.2.3"),
        ("libs/workspace_runtime", "aware-workspace-runtime", "0.2.3"),
        (
            "sdks/workspace/filesystem_adapter/python",
            "aware-workspace-fs-adapter",
            "0.1.3",
        ),
    ],
)
def test_successor_identity_and_own_owner_floors(path, name, version):
    project = tomllib.loads((WORKSPACE / path / "pyproject.toml").read_text())[
        "project"
    ]
    assert (project["name"], project["version"]) == (name, version)
    for raw in project["dependencies"]:
        requirement = Requirement(raw)
        if requirement.name in {"aware-workspace-sdk", "aware-workspace-runtime"}:
            assert "0.2.3" in requirement.specifier
            assert "0.2.2" not in requirement.specifier
            assert "0.3.0" not in requirement.specifier


def test_capture_extra_selects_only_original_fs_owner():
    project = tomllib.loads(
        (WORKSPACE / "sdks/workspace/python/public/pyproject.toml").read_text()
    )["project"]
    selected = project["optional-dependencies"]["filesystem_delta_capture"]
    assert selected == ["aware-workspace-fs-adapter>=0.1.3,<0.2.0"]
    requirement = Requirement(selected[0])
    assert "0.1.2" not in requirement.specifier


def test_supplier_profile_does_not_change_product_membership():
    profiles = {
        p["key"]: p
        for p in tomllib.loads((ROOT / "aware.repo.toml").read_text())[
            "checkout_profile_sets"
        ]
    }
    assert profiles["workspace_delta_capture"]["package_selections"] == [
        {
            "workspace": "aware_workspace",
            "module": "workspace",
            "package": "workspace_sdk_python",
            "extras": ["filesystem_delta_capture"],
        }
    ]
    assert (
        "workspace_delta_capture"
        not in profiles["portable_protocols"]["include_profiles"]
    )


def test_original_resolver_has_capture_only_registered_closure():
    result = subprocess.run(
        [
            str(ROOT / ".venv/bin/aware-cli"),
            "workspace",
            "checkout",
            "--repo-root",
            str(ROOT),
            "--profile",
            "workspace_delta_capture",
            "--plan",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    plan = json.loads(result.stdout)
    assert plan["profiles"]["requested"] == ["workspace_delta_capture"]
    assert plan["selection"] == ["aware-workspace-sdk[filesystem-delta-capture]"]
    names = {p["name"] for p in plan["packages"]}
    assert {
        "aware-workspace-sdk",
        "aware-workspace-runtime",
        "aware-workspace-fs-adapter",
    } <= names
    assert not any(
        n.startswith(
            (
                "aware-issue",
                "aware-protocol",
                "aware-meta",
                "aware-ontology",
                "aware-service",
            )
        )
        for n in names
    )
    assert all(p["memberships"] for p in plan["packages"])
    assert all(
        not plan["claims"][key]
        for key in (
            "installed",
            "materialized",
            "publication_authorized",
            "registry_locked",
        )
    )
