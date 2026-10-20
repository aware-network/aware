from dataclasses import replace
from pathlib import Path

import pytest

from aware_goal_operational_runtime.dependencies import (
    GoalDependency,
    GoalDependencyRelation,
    validate_dependency_set,
)


def edge() -> GoalDependency:
    return GoalDependency(
        owner_goal_tag="goal/test", dependency_key="delivery-needs-review",
        dependent_lane_key="delivery", dependent_row_key="ship",
        prerequisite_goal_tag="goal/external", prerequisite_lane_key="review",
        prerequisite_row_key="accept", relation=GoalDependencyRelation.REQUIRES_ACCEPTANCE,
        reason="Independent acceptance required",
    )


def test_unresolved_external_coordinates_survive_without_satisfaction():
    dependency = edge()
    validate_dependency_set((dependency,))
    assert dependency.prerequisite.goal_tag == "goal/external"
    assert dependency.to_wire()["relation"] == "requires_acceptance"
    assert "satisfied" not in dependency.to_wire()


def test_rejects_self_edges_and_malformed_declarations():
    with pytest.raises(ValueError, match="own row"):
        replace(edge(), prerequisite_goal_tag="goal/test", prerequisite_lane_key="delivery", prerequisite_row_key="ship")
    with pytest.raises(ValueError):
        replace(edge(), reason=" ")
    with pytest.raises(TypeError):
        replace(edge(), relation="requires_acceptance")


def test_duplicates_and_cross_goal_cycles_fail():
    dependency = edge()
    with pytest.raises(ValueError, match="duplicate"):
        validate_dependency_set((dependency, replace(dependency, dependency_key="other")))
    reverse = GoalDependency(
        owner_goal_tag="goal/external", dependency_key="reverse",
        dependent_lane_key="review", dependent_row_key="accept",
        prerequisite_goal_tag="goal/test", prerequisite_lane_key="delivery",
        prerequisite_row_key="ship", relation=GoalDependencyRelation.REQUIRES_COMPLETION,
        reason="Cycle example",
    )
    with pytest.raises(ValueError, match="cycle"):
        validate_dependency_set((dependency, reverse))


def test_authored_fields_match_neutral_wire_contract():
    workflow = Path(__file__).resolve().parents[3]
    source = (workflow / "ontology/structure/aware/goal/goal_dependency.aware").read_text()
    for name in edge().to_wire().keys() - {"owner_goal_tag"}:
        assert f"    {name} " in source
    for relation in GoalDependencyRelation:
        assert f"    {relation.value}\n" in source
    assert "dependencies GoalDependency[]" in (
        workflow / "ontology/structure/aware/goal/goal.aware"
    ).read_text()
