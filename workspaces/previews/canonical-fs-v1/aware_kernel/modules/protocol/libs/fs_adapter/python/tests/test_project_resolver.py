"""Retained fs_v3 Project location and participating Goal capabilities."""

import copy
import os
import pickle
from pathlib import Path

import pytest

from aware_protocol_fs_adapter import (
    NativeGoalResolverCapability,
    NativeGoalResolverError,
    ProjectResolverCapability,
    ProjectResolverError,
    admit_project_resolver,
    require_native_goal_resolver,
    require_project_resolver,
)
from aware_protocol_runtime import ProtocolAdmissionOutcomeKind
from test_project_record_admission import MANIFEST


PROJECT = "customer/projects/project-example.toml"
GOAL = "customer/goals/goal-2026-10-04-example.md"


def _issue(root: Path, source: str = MANIFEST) -> ProjectResolverCapability:
    manifest = root / "aware.protocol.toml"
    manifest.write_text(source)
    result = admit_project_resolver(repository_root=root, manifest_path=manifest)
    assert result.admission.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1
    assert result.capability is not None
    return result.capability


def test_fresh_issuance_retains_project_and_genuine_goal_binding(tmp_path: Path) -> None:
    capability = _issue(tmp_path)
    assert require_project_resolver(capability) is capability
    assert capability.repository_root == tmp_path.resolve()
    assert capability.project_root == "customer/projects"
    assert capability.project_template == "project-<slug>.toml"
    assert capability.manifest_sha256.startswith("sha256:")
    assert capability.protocol_digest.startswith("sha256:")
    assert capability.resolve_project_path(PROJECT).location_slug == "example"
    assert not (tmp_path / PROJECT).exists()
    goal = capability.goal_capability
    assert type(goal) is NativeGoalResolverCapability
    assert require_native_goal_resolver(goal) is goal
    assert goal.manifest_sha256 == capability.manifest_sha256
    assert goal.protocol_digest == capability.protocol_digest
    assert goal.resolve_goal_path(GOAL).location_slug == "example"


@pytest.mark.parametrize("value", [None, {}, "customer/projects", MANIFEST])
def test_detached_values_cannot_be_project_capability(value: object) -> None:
    with pytest.raises(ProjectResolverError, match="project_capability_invalid"):
        require_project_resolver(value)


def test_public_construction_forgery_and_copy_refuse(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="use admit_project_resolver"):
        ProjectResolverCapability()
    forged = object.__new__(ProjectResolverCapability)
    with pytest.raises(ProjectResolverError, match="project_capability_invalid"):
        require_project_resolver(forged)
    with pytest.raises(TypeError, match="cannot be subclassed"):
        type("ForgedProject", (ProjectResolverCapability,), {})
    capability = _issue(tmp_path)
    for operation in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError, match="cannot be copied or serialized"):
            operation(capability)
    with pytest.raises(AttributeError):
        capability.project_root = "elsewhere"


@pytest.mark.skipif(not hasattr(os, "fork"), reason="requires fork")
def test_fork_inherited_capability_refuses(tmp_path: Path) -> None:
    capability = _issue(tmp_path)
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        try:
            require_project_resolver(capability)
        except ProjectResolverError as error:
            os.write(write_fd, error.code.encode())
        else:
            os.write(write_fd, b"unexpected_success")
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    try:
        result = os.read(read_fd, 256)
    finally:
        os.close(read_fd)
        os.waitpid(child, 0)
    assert result == b"project_capability_foreign_process"


def test_old_profile_cannot_issue_project_capability(tmp_path: Path) -> None:
    source = MANIFEST.split("[records.project]")[0].replace(
        "aware.collaboration.fs_v3", "aware.collaboration.fs_v2"
    ).replace("semantic_version = 3", "semantic_version = 2")
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(source)
    with pytest.raises(ProjectResolverError, match="project_profile_required"):
        admit_project_resolver(repository_root=tmp_path, manifest_path=manifest)


def test_refused_admission_returns_no_token(tmp_path: Path) -> None:
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_text(MANIFEST.replace("aware.project.context.toml.v1", "aware.project.context.toml.v99"))
    result = admit_project_resolver(repository_root=tmp_path, manifest_path=manifest)
    assert result.admission.outcome is ProtocolAdmissionOutcomeKind.FOREIGN_PROFILE
    assert result.capability is None


@pytest.mark.parametrize("change", ["\n", "\n# semantically identical\n"])
def test_manifest_byte_change_revokes_project_and_goal(tmp_path: Path, change: str) -> None:
    capability = _issue(tmp_path)
    goal = capability.goal_capability
    with capability.manifest_path.open("a") as source:
        source.write(change)
    with pytest.raises(ProjectResolverError, match="project_admission_changed"):
        require_project_resolver(capability)
    with pytest.raises(NativeGoalResolverError, match="native_goal_manifest_changed"):
        require_native_goal_resolver(goal)


def test_manifest_or_repository_substitution_refuses(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    capability = _issue(root)
    original = capability.manifest_path
    second = root / "other" / "aware.protocol.toml"
    second.parent.mkdir()
    second.write_text(MANIFEST)
    original.unlink()
    original.symlink_to(second)
    with pytest.raises(ProjectResolverError, match="project_admission_changed"):
        capability.revalidate()

    root2 = tmp_path / "replacement"
    root2.mkdir()
    replacement = _issue(root2)
    root2.rename(tmp_path / "former")
    root2.mkdir()
    (root2 / "aware.protocol.toml").write_text(MANIFEST)
    with pytest.raises(ProjectResolverError, match="project_admission_changed"):
        replacement.revalidate()


@pytest.mark.parametrize("target", [
    "customer/projects-extra/project-example.toml",
    "other/projects/project-example.toml",
    "customer/projects/sub/project-example.toml",
    "customer/projects/project-Example.toml",
    "customer/projects/project-../escape.toml",
    "customer/projects/project-example.toml\n",
    "/customer/projects/project-example.toml",
])
def test_concrete_target_requires_exact_location_grammar(tmp_path: Path, target: str) -> None:
    capability = _issue(tmp_path)
    assert capability.match_project_path(target) is None
    with pytest.raises(ProjectResolverError, match="project_target_outside_binding"):
        capability.resolve_project_path(target)


@pytest.mark.parametrize("scenario", ["outside", "loop", "broken"])
def test_at_use_target_symlink_refuses(tmp_path: Path, scenario: str) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    capability = _issue(root)
    target = root / PROJECT
    target.parent.mkdir(parents=True)
    outside = tmp_path / "outside.toml"
    outside.write_text("not authority")
    destination = outside if scenario == "outside" else target if scenario == "loop" else root / "missing.toml"
    target.symlink_to(destination)
    with pytest.raises(ProjectResolverError, match="project_target_unresolvable"):
        capability.resolve_project_path(PROJECT)


def test_repeated_location_use_preserves_dirty_work(tmp_path: Path) -> None:
    capability = _issue(tmp_path)
    target = tmp_path / PROJECT
    target.parent.mkdir(parents=True)
    target.write_bytes(b"Project bytes are not parsed by Protocol")
    dirty = tmp_path / "dirty.txt"
    dirty.write_bytes(b"unrelated work")
    before = {path: path.read_bytes() for path in (target, dirty, capability.manifest_path)}
    for _ in range(3):
        capability.resolve_project_path(PROJECT)
    assert all(path.read_bytes() == value for path, value in before.items())
