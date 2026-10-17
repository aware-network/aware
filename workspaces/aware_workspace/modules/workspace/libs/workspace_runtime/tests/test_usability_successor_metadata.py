"""Successor compatibility for the existing registrar and optional A1 profile."""

import tomllib
from pathlib import Path

from packaging.requirements import Requirement

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").is_file()
)
RUNTIME = ROOT / "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime"


def test_runtime_successor_keeps_original_launchers_and_packaging():
    manifest = tomllib.loads((RUNTIME / "pyproject.toml").read_text())
    project = manifest["project"]
    assert project["name"] == "aware-workspace-runtime"
    assert project["version"] == "0.2.15"
    assert (
        project["scripts"]["aware-workspace"]
        == "aware_workspace_command.architecture_setup_command:main"
    )
    assert (
        project["entry-points"]["aware_cli.command_packs"]["workspace"]
        == "aware_workspace_command.pack:get_command_specs"
    )
    assert (
        "aware_workspace_command"
        in manifest["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]
    )
    assert (
        RUNTIME / "aware_workspace_command/architecture_setup_a1_presentation.py"
    ).is_file()


def test_original_consumers_admit_runtime_patch_without_requiring_grammar():
    paths = [
        "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/pyproject.toml",
        "workspaces/aware_agent/modules/agent/libs/agent_cli/python/pyproject.toml",
    ]
    for name in paths:
        project = tomllib.loads((ROOT / name).read_text())["project"]
        declared = list(project["dependencies"])
        declared.extend(
            r
            for values in project.get("optional-dependencies", {}).values()
            for r in values
        )
        requirements = [
            r
            for raw in declared
            if (r := Requirement(raw)).name == "aware-workspace-runtime"
        ]
        assert requirements
        for requirement in requirements:
            assert requirement.specifier.contains("0.2.15")
            assert not requirement.specifier.contains("0.3.0")
            assert not any("grammar" in extra for extra in requirement.extras)


def test_original_profile_selects_a1_without_new_catalog_or_setup_grammar():
    repository = tomllib.loads((ROOT / "aware.repo.toml").read_text())
    profiles = {p["key"]: p for p in repository["checkout_profile_sets"]}
    assert "portable_workspace" in profiles["portable_protocols"]["include_profiles"]
    workspace = next(
        p
        for p in profiles["portable_workspace"]["package_selections"]
        if p.get("package") == "workspace_sdk_python"
    )
    assert "setup_admission" in workspace["extras"]
    project = tomllib.loads((RUNTIME / "pyproject.toml").read_text())["project"]
    req = next(
        Requirement(raw)
        for raw in project["optional-dependencies"]["setup_admission"]
        if Requirement(raw).name == "aware-issue-sdk"
    )
    assert req.specifier.contains("0.10.6") and not req.specifier.contains("0.11.0")
