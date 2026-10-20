from pathlib import Path

ONTOLOGY = Path(__file__).parents[3] / "ontology/structure/aware/goal"


def text(name: str) -> str:
    return (ONTOLOGY / name).read_text(encoding="utf-8")


def test_phase_contract_is_additive_to_existing_goal_lane_issue_model() -> None:
    lane = text("goal_lane.aware")
    goal = text("goal.aware")
    assert "lane_issues GoalLaneIssue[]" in lane
    assert "phases GoalLanePhase[]" in lane
    assert "dependencies GoalDependency[]" in goal
    assert "phase_dependencies GoalPhaseDependency[]" in goal


def test_authored_phase_gate_and_work_types_are_present() -> None:
    phase = text("goal_lane_phase.aware")
    gate = text("goal_lane_phase_gate.aware")
    observation = text("goal_lane_phase_gate_observation.aware")
    work = text("goal_lane_phase_work.aware")
    dependency = text("goal_phase_dependency.aware")
    assert "phase_key String key" in phase
    assert "gate GoalLanePhaseGate" in phase
    assert "gate_digest String" in gate
    assert "not_evaluated" in observation
    assert "issue issue.Issue" in work
    assert "required_gate_digest String" in dependency
    assert "dependent_phase_key String" in dependency
