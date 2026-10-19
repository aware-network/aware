"""Explicit fs_v4 location admission; never Goal origin or creation authority."""

import copy
import os
import pickle

import pytest
from aware_protocol_fs_adapter import (
    NativeGoalResolverCapability,
    NativeGoalResolverError,
    ProjectResolverError,
    admit_native_goal_resolver,
    admit_project_resolver,
    require_project_resolver,
)
from aware_protocol_fs_adapter.manifest import (
    COLLABORATION_PLANNING_FS_PROFILE,
    PLANNING_GOAL_RECORD_PROFILE,
    validate_protocol_manifest_content,
)
from aware_protocol_fs_adapter.native_goal_resolver import (
    require_native_goal_resolver,
    require_planning_goal_resolver,
)
from aware_protocol_fs_adapter.project_bootstrap import (
    prepare_planning_project_configuration,
    prepare_project_configuration,
    require_project_configuration,
)
from aware_protocol_runtime import ProtocolAdmissionOutcomeKind


def source(root, *, planning=True):
    prepare = (
        prepare_planning_project_configuration
        if planning
        else prepare_project_configuration
    )
    return require_project_configuration(
        prepare(
            repository_root=str(root),
            issue_root="customer/issues",
            goal_root="customer/goals",
            project_root="customer/projects",
        )
    ).content


def issue(root, *, planning=True):
    manifest = root / "aware.protocol.toml"
    manifest.write_bytes(source(root, planning=planning))
    admitted = admit_project_resolver(repository_root=root, manifest_path=manifest)
    assert admitted.capability is not None
    return admitted.capability


def test_fresh_fs_v4_retains_exact_project_and_planning_goal_admission(tmp_path):
    project = issue(tmp_path)
    assert require_project_resolver(project) is project
    assert project.protocol_profile == COLLABORATION_PLANNING_FS_PROFILE
    goal = require_planning_goal_resolver(project.goal_capability)
    assert type(goal) is NativeGoalResolverCapability
    assert goal.goal_record_profile == PLANNING_GOAL_RECORD_PROFILE
    assert goal.protocol_profile == project.protocol_profile
    assert goal.protocol_digest == project.protocol_digest
    assert goal.manifest_sha256 == project.manifest_sha256
    assert (
        goal.resolve_goal_path(
            "customer/goals/2026/10/17/goal-2026-10-17-first.md"
        ).location_slug
        == "first"
    )
    assert (
        project.resolve_project_path(
            "customer/projects/project-first.toml"
        ).location_slug
        == "first"
    )
    assert sorted(path.name for path in tmp_path.iterdir()) == ["aware.protocol.toml"]
    # This capability admits locations only; no Goal/Project records were made.
    assert not hasattr(goal, "publish")
    assert not hasattr(goal, "origin_ref")


def test_old_native_token_cannot_substitute_for_planning_profile(tmp_path):
    project = issue(tmp_path, planning=False)
    assert project.protocol_profile == "aware.collaboration.fs_v3"
    assert project.goal_capability.goal_record_profile == "aware.goal.phase.markdown.v1"
    with pytest.raises(NativeGoalResolverError, match="planning_goal_profile_required"):
        require_planning_goal_resolver(project.goal_capability)


def test_existing_phase_reader_entrance_does_not_silently_widen_to_fs_v4(tmp_path):
    goal = issue(tmp_path).goal_capability
    assert require_planning_goal_resolver(goal) is goal
    with pytest.raises(
        NativeGoalResolverError, match="native_goal_reader_profile_required"
    ):
        require_native_goal_resolver(goal)


@pytest.mark.parametrize(
    "old,new",
    [
        (b"semantic_version = 4", b"semantic_version = 3"),
        (b"semantic_version = 4", b"semantic_version = true"),
        (b"fs_v4", b"fs_v3"),
        (b"fs_v4", b"fs_v2"),
        (b"fs_v4", b"fs_v1"),
        (b"aware.goal.native.markdown.v2", b"aware.goal.phase.markdown.v1"),
        (b"aware.goal.native.markdown.v2", b"aware.goal.markdown.v1"),
        (b"aware.goal.native.markdown.v2", b"aware.goal.native.markdown.v3"),
        (b"aware.project.context.toml.v1", b"aware.project.context.toml.v2"),
    ],
)
def test_wrong_profile_version_and_record_pairs_refuse(tmp_path, old, new):
    candidate = source(tmp_path).replace(old, new)
    manifest = tmp_path / "aware.protocol.toml"
    manifest.write_bytes(candidate)
    admitted = admit_project_resolver(repository_root=tmp_path, manifest_path=manifest)
    assert admitted.admission.outcome is not ProtocolAdmissionOutcomeKind.CANONICAL_V1
    assert admitted.capability is None
    assert (
        admit_native_goal_resolver(
            repository_root=tmp_path, manifest_path=manifest
        ).capability
        is None
    )


def test_planning_requires_explicit_project_binding_and_authority(tmp_path):
    # Preserve the required non-Project declarations while omitting Project.
    full = source(tmp_path)
    begin, suffix = full.split(b"[records.project]", 1)
    missing = begin + b"[records.feed]" + suffix.split(b"[records.feed]", 1)[1]
    assert validate_protocol_manifest_content(source=missing).diagnostics == (
        "project_record_required_for_fs_v4",
    )
    for record in (b"goal", b"issue", b"project"):
        prefix, tail = full.split(b"[records." + record + b"]", 1)
        candidate = (
            prefix
            + b"[records."
            + record
            + b"]"
            + tail.replace(b'role = "authority"', b'role = "projection"', 1)
        )
        assert (
            validate_protocol_manifest_content(source=candidate).outcome
            is not ProtocolAdmissionOutcomeKind.CANONICAL_V1
        )


@pytest.mark.parametrize("value", [None, {}, "customer/goals"])
def test_caller_data_is_not_planning_capability(value):
    with pytest.raises(NativeGoalResolverError, match="capability_invalid"):
        require_planning_goal_resolver(value)


def test_forged_copied_and_decoded_fs_v4_capabilities_refuse(tmp_path):
    project = issue(tmp_path)
    goal = project.goal_capability
    with pytest.raises(NativeGoalResolverError, match="capability_invalid"):
        require_planning_goal_resolver(object.__new__(NativeGoalResolverCapability))
    for copy_operation in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            copy_operation(goal)
        with pytest.raises(TypeError):
            copy_operation(project)
    with pytest.raises(AttributeError):
        goal.goal_record_profile = "aware.goal.phase.markdown.v1"


@pytest.mark.parametrize("change", [b"\n# byte change\n", b"\n"])
def test_manifest_byte_change_invalidates_both_tokens(tmp_path, change):
    project = issue(tmp_path)
    goal = project.goal_capability
    project.manifest_path.write_bytes(project.manifest_path.read_bytes() + change)
    with pytest.raises(NativeGoalResolverError, match="manifest_changed"):
        require_planning_goal_resolver(goal)
    with pytest.raises(ProjectResolverError, match="project_admission_changed"):
        project.revalidate()


@pytest.mark.parametrize(
    "target",
    [
        "other/goals/2026/10/17/goal-2026-10-17-first.md",
        "customer/goals/2026/10/16/goal-2026-10-17-first.md",
        "customer/goals/../goal-2026-10-17-first.md",
    ],
)
def test_planning_target_requires_retained_root_and_template(tmp_path, target):
    goal = require_planning_goal_resolver(issue(tmp_path).goal_capability)
    with pytest.raises(NativeGoalResolverError, match="outside_binding"):
        goal.resolve_goal_path(target)


@pytest.mark.parametrize("where", ["parent", "leaf"])
def test_fs_v4_refuses_external_goal_symlinks(tmp_path, where):
    project = issue(tmp_path)
    goal = require_planning_goal_resolver(project.goal_capability)
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    relative = "customer/goals/2026/10/17/goal-2026-10-17-first.md"
    if where == "parent":
        (tmp_path / "customer").mkdir()
        (tmp_path / "customer/goals").symlink_to(outside, target_is_directory=True)
    else:
        target = tmp_path / relative
        target.parent.mkdir(parents=True)
        foreign = outside / "foreign.md"
        foreign.write_bytes(b"not qualified Goal authority")
        target.symlink_to(foreign)
    with pytest.raises(NativeGoalResolverError):
        goal.resolve_goal_path(relative)


@pytest.mark.skipif(not hasattr(os, "fork"), reason="requires fork")
def test_fs_v4_token_is_not_inherited_authority(tmp_path):
    goal = issue(tmp_path).goal_capability
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        try:
            require_planning_goal_resolver(goal)
        except NativeGoalResolverError as error:
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
    assert result == b"native_goal_capability_foreign_process"
