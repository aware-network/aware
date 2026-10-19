"""Planning setup is an explicit retained plan, never an implicit upgrade."""

import copy
import json
import pickle

import pytest
from aware_protocol_fs_adapter import project_bootstrap as owner
from aware_protocol_fs_adapter.project_bootstrap import (
    ProjectConfigurationPlan,
    prepare_planning_project_configuration,
    prepare_project_configuration,
    require_project_configuration,
)


def prepare(root, *, planning=True):
    selected = (
        prepare_planning_project_configuration
        if planning
        else prepare_project_configuration
    )
    return selected(
        repository_root=str(root),
        issue_root="issues",
        goal_root="goals",
        project_root="projects",
    )


def test_opt_in_changes_only_the_two_declared_profile_coordinates(tmp_path):
    original = require_project_configuration(prepare(tmp_path, planning=False))
    planning = require_project_configuration(prepare(tmp_path))
    assert planning.content == original.content.replace(
        b'profile = "aware.collaboration.fs_v3"\nsemantic_version = 3',
        b'profile = "aware.collaboration.fs_v4"\nsemantic_version = 4',
    ).replace(b"aware.goal.phase.markdown.v1", b"aware.goal.native.markdown.v2")
    assert (
        set(planning.to_wire())
        == set(original.to_wire())
        == {
            "repository_root",
            "issue_root",
            "goal_root",
            "project_root",
            "content_utf8",
            "source_sha256",
        }
    )
    assert not list(tmp_path.iterdir())


def test_planning_defaults_are_owned_by_protocol_and_match_explicit_bytes(tmp_path):
    default = require_project_configuration(
        prepare_planning_project_configuration(repository_root=str(tmp_path))
    )
    explicit = require_project_configuration(
        prepare_planning_project_configuration(
            repository_root=str(tmp_path),
            issue_root="docs/issues",
            goal_root="docs/goals",
            project_root="docs/projects",
        )
    )
    assert default == explicit
    assert default.issue_root == "docs/issues"
    assert default.goal_root == "docs/goals"
    assert default.project_root == "docs/projects"
    assert not list(tmp_path.iterdir())


def test_default_planning_roots_still_enforce_overlap_and_original_fs_v3_signature(
    tmp_path,
):
    with pytest.raises(ValueError, match="roots_overlap"):
        prepare_planning_project_configuration(
            repository_root=str(tmp_path), goal_root="docs/projects/child"
        )
    with pytest.raises(TypeError):
        prepare_project_configuration(repository_root=str(tmp_path))
    assert not list(tmp_path.iterdir())


def test_planning_plan_cannot_be_constructed_copied_decoded_or_substituted(tmp_path):
    plan = prepare(tmp_path)
    for operation in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            operation(plan)
    for fake in (
        object.__new__(ProjectConfigurationPlan),
        require_project_configuration(plan),
        require_project_configuration(plan).to_wire(),
    ):
        with pytest.raises(ValueError):
            require_project_configuration(fake)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("planning", [False, True])
def test_redigested_cross_profile_plan_mutation_refuses(tmp_path, planning):
    plan = prepare(tmp_path, planning=planning)
    substitute = require_project_configuration(prepare(tmp_path, planning=not planning))
    state = owner._PLANS[plan]
    retained = state[1]
    object.__setattr__(retained, "content", substitute.content)
    object.__setattr__(retained, "source_sha256", substitute.source_sha256)
    # Even matching the altered configuration fingerprint cannot change the
    # original selected rendering profile retained separately by this issuer.
    owner._PLANS[plan] = (
        state[0],
        retained,
        json.dumps(retained.to_wire(), sort_keys=True),
        state[3],
    )
    for _ in range(2):
        with pytest.raises(ValueError, match="configuration_changed"):
            require_project_configuration(plan)


@pytest.mark.parametrize(
    "roots",
    [
        ("a", "a", "c"),
        ("a", "a/b", "c"),
        ("../escape", "b", "c"),
        ("a", ".git/goals", "c"),
    ],
)
def test_fs_v4_preserves_original_root_refusals(tmp_path, roots):
    with pytest.raises(ValueError):
        prepare_planning_project_configuration(
            repository_root=str(tmp_path),
            issue_root=roots[0],
            goal_root=roots[1],
            project_root=roots[2],
        )
    assert not list(tmp_path.iterdir())
