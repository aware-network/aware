"""Native preparation has no configuration/publication/record creation effects."""

import copy
import pickle

import pytest
from aware_protocol_fs_adapter.project_bootstrap import (
    ProjectConfigurationPlan,
    prepare_project_configuration,
    require_project_configuration,
)


def test_real_native_manifest_without_customer_records(tmp_path):
    plan = prepare_project_configuration(
        repository_root=str(tmp_path),
        issue_root="work/issues",
        goal_root="work/goals",
        project_root="work/projects",
    )
    config = require_project_configuration(plan)
    assert b'profile = "aware.collaboration.fs_v3"' in config.content
    assert b"[records.project]" in config.content
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "roots",
    [
        ("a", "a", "c"),
        ("a", "a/b", "c"),
        ("../escape", "b", "c"),
        ("a", ".git/goals", "c"),
        ("a", "b", "aware.protocol.toml"),
    ],
)
def test_invalid_roots_refuse(tmp_path, roots):
    with pytest.raises(ValueError):
        prepare_project_configuration(
            repository_root=str(tmp_path),
            issue_root=roots[0],
            goal_root=roots[1],
            project_root=roots[2],
        )
    assert not list(tmp_path.iterdir())


def test_copy_decode_and_forgery_do_not_supply_original_plan(tmp_path):
    plan = prepare_project_configuration(
        repository_root=str(tmp_path),
        issue_root="issues",
        goal_root="goals",
        project_root="projects",
    )
    for operation in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            operation(plan)
    for fake in (
        require_project_configuration(plan),
        require_project_configuration(plan).to_wire(),
        object.__new__(ProjectConfigurationPlan),
    ):
        with pytest.raises(ValueError):
            require_project_configuration(fake)


def test_recomputed_mutation_cannot_change_issued_configuration(tmp_path):
    from aware_protocol_fs_adapter import project_bootstrap as owner

    plan = prepare_project_configuration(repository_root=str(tmp_path), issue_root="issues", goal_root="goals", project_root="projects")
    original = require_project_configuration(plan)
    detached = require_project_configuration(plan)
    object.__setattr__(detached, "project_root", "other")
    assert require_project_configuration(plan) == original
    retained = owner._PLANS[plan][1]
    substituted = owner._render(str(tmp_path), "issues", "goals", "other")
    for field in ("project_root", "content", "source_sha256"):
        object.__setattr__(retained, field, getattr(substituted, field))
    with pytest.raises(ValueError, match="configuration_changed"):
        require_project_configuration(plan)
