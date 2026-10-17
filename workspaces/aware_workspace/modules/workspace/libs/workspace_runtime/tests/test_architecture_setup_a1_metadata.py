"""The installed A1 selection must exclude artifacts predating its supplier ports."""

import hashlib
import os
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").exists()
)
MANIFESTS = {
    "aware-workspace-sdk": "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/pyproject.toml",
    "aware-workspace-runtime": "workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/pyproject.toml",
    "aware-workspace-fs-adapter": "workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/pyproject.toml",
    "aware-issue-sdk": "workspaces/aware_coordination/modules/workflow/sdks/issue/python/pyproject.toml",
    "aware-issue-operational-runtime": "workspaces/aware_coordination/modules/workflow/libs/issue_operational_runtime/pyproject.toml",
    "aware-issue-fs-adapter": "workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/pyproject.toml",
    "aware-file-system": "workspaces/aware_kernel/modules/filesystem/libs/file_system/python/pyproject.toml",
    "aware-agent-cli": "workspaces/aware_agent/modules/agent/libs/agent_cli/python/pyproject.toml",
}
VERSIONS = {
    "aware-workspace-sdk": "0.2.11",
    "aware-workspace-runtime": "0.2.16",
    "aware-workspace-fs-adapter": "0.1.10",
    "aware-issue-sdk": "0.10.6",
    "aware-issue-operational-runtime": "0.3.4",
    "aware-issue-fs-adapter": "0.9.6",
    "aware-file-system": "0.3.8",
    "aware-agent-cli": "0.2.0a6",
}
OLD = {
    "aware-workspace-sdk": "0.2.7",
    "aware-workspace-runtime": "0.2.10",
    "aware-workspace-fs-adapter": "0.1.5",
    "aware-issue-sdk": "0.10.3",
    "aware-issue-operational-runtime": "0.3.2",
    "aware-issue-fs-adapter": "0.9.4",
    "aware-file-system": "0.3.6",
}


def project(name):
    return tomllib.loads((ROOT / MANIFESTS[name]).read_text())["project"]


@pytest.mark.parametrize("name", tuple(MANIFESTS))
def test_exact_successor_identity_and_unchanged_python_support(name):
    p = project(name)
    assert p["name"] == name and p["version"] == VERSIONS[name]
    assert p["requires-python"] == ">=3.12"


@pytest.mark.parametrize(
    "name,extra",
    (
        ("aware-workspace-sdk", "setup_admission"),
        ("aware-workspace-runtime", "setup_admission"),
        ("aware-issue-sdk", "workspace_setup_admission"),
        ("aware-issue-operational-runtime", "workspace_setup_admission"),
    ),
)
def test_explicit_profile_requires_original_successors_and_excludes_predecessors(
    name, extra
):
    requirements = [
        Requirement(s) for s in project(name)["optional-dependencies"][extra]
    ]
    assert requirements
    for req in requirements:
        assert req.specifier.contains(VERSIONS[req.name], prereleases=True)
        assert not req.specifier.contains(OLD[req.name], prereleases=True)


def test_agent_selects_genuine_admission_profiles_not_only_legacy_setup():
    reqs = {
        r.name: r for r in map(Requirement, project("aware-agent-cli")["dependencies"])
    }
    assert reqs["aware-workspace-sdk"].extras == {
        "preparation",
        "setup",
        "setup_admission",
    }
    assert reqs["aware-workspace-runtime"].extras == {"setup_admission"}
    assert reqs["aware-issue-sdk"].extras == {"workspace_setup_admission"}
    for name in (
        "aware-workspace-sdk",
        "aware-workspace-runtime",
        "aware-issue-sdk",
        "aware-issue-fs-adapter",
    ):
        assert reqs[name].specifier.contains(VERSIONS[name], prereleases=True)
        assert not reqs[name].specifier.contains(OLD[name], prereleases=True)


def test_legacy_workspace_setup_selection_stays_separate():
    assert project("aware-workspace-sdk")["optional-dependencies"]["setup"] == [
        "aware-workspace-fs-adapter>=0.1.5,<0.2.0",
    ]


@pytest.mark.parametrize(
    "name", ("aware-workspace-fs-adapter", "aware-issue-fs-adapter")
)
def test_physical_adapters_declare_the_repaired_file_sequence_floor(name):
    reqs = {r.name: r for r in map(Requirement, project(name)["dependencies"])}
    req = reqs["aware-file-system"]
    # The reviewed Workspace profile needs the private IO successor; Issue's
    # existing A1 profile retains its independently qualified sequence floor.
    floor, old = (
        ("0.3.8", "0.3.7")
        if name == "aware-workspace-fs-adapter"
        else ("0.3.7", "0.3.6")
    )
    assert req.specifier.contains(floor) and not req.specifier.contains(old)


def test_original_issue_progress_requires_the_same_declared_owner_and_actor(tmp_path):
    from aware_issue_fs_adapter import FilesystemIssueOperationProvider
    from aware_issue_sdk import (
        IssueEnsureSnapshotRequest,
        IssueMutationOutcome,
        IssueSdkOperationClient,
        IssueStartProgressRequest,
    )

    (tmp_path / "docs/goals").mkdir(parents=True)
    (tmp_path / "AGENTS.md").write_text("# Disposable qualification\n")
    (tmp_path / "aware.protocol.toml").write_bytes(
        (ROOT / "aware.protocol.toml").read_bytes()
    )
    execution = "codex-" + os.environ["CODEX_THREAD_ID"]
    client = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(
            repository_root=str(tmp_path), protocol_source_ref="aware.protocol.toml"
        )
    )
    ref = "fb/2026-10-14/qualification-actor"
    client.ensure_issue_snapshot(
        IssueEnsureSnapshotRequest(
            issue_ref=ref,
            title="Qualification actor",
            priority="P1",
            actor_ref=execution,
            actor_evidence_ref="declared:qualification",
            client_intent_id="intent:create",
            owner_ref=execution,
        )
    )
    path = tmp_path / "docs/issues/2026/10/14/fb-2026-10-14-qualification-actor.md"
    before = path.read_bytes()
    guard = "sha256:" + hashlib.sha256(before).hexdigest()
    wrong = client.start_issue_progress(
        IssueStartProgressRequest(
            issue_ref=ref,
            expected_source_sha256=guard,
            client_intent_id="intent:wrong",
            actor_ref="declared:other",
            actor_evidence_ref="declared:qualification",
        )
    )
    assert str(wrong.outcome) == "unauthorized" and path.read_bytes() == before
    correct = client.start_issue_progress(
        IssueStartProgressRequest(
            issue_ref=ref,
            expected_source_sha256=guard,
            client_intent_id="intent:correct",
            actor_ref=execution,
            actor_evidence_ref="declared:qualification",
        )
    )
    assert correct.outcome is IssueMutationOutcome.APPLIED
    assert correct.projection.status == "in_progress"


def test_low_level_sdk_package_request_declares_owner_relative_placement(tmp_path):
    from aware_workspace_sdk.architecture_setup import (
        ArchitectureSetupError,
        ArchitectureSetupRequest,
        WorkspaceSetupClient,
    )

    with WorkspaceSetupClient.filesystem(repository_root=tmp_path) as client:
        repo = client.create_repository("example", license_expression="MIT")
        repo.create_workspace("application").create_module("greeting")
        values = {
            "name": "client",
            "workspace": "application",
            "module": "greeting",
            "distribution": "example-client",
            "import_root": "example_client",
            "owner": "module",
        }
        with pytest.raises(ArchitectureSetupError, match="invalid_relative_path"):
            client.preview(ArchitectureSetupRequest("python_package", **values))
        preview = client.preview(
            ArchitectureSetupRequest(
                "python_package", path="libs/client/python", **values
            )
        )
        assert (
            "workspaces/application/modules/greeting/libs/client/python/pyproject.toml"
            in {change.path for change in preview.changes}
        )
        assert not (
            tmp_path / "workspaces/application/modules/greeting/libs/client"
        ).exists()
