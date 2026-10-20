from aware_goal_operational_runtime.projection_advancement import (
    GoalProjectionChange,
    GoalProjectionEvidenceV1,
    GoalProjectionSourceCurrentness,
    assess_goal_projection_advancement,
)


def _evidence(**changes: str) -> GoalProjectionEvidenceV1:
    values = {
        "source_revision": "a" * 40,
        "goal_path": "docs/goals/example.md",
        "goal_sha256": "sha256:" + "b" * 64,
        "projector_ref": "aware.goal.markdown-operational-projector",
        "projector_version": "1",
        "lowered_intent_stream_digest": "sha256:intents",
        "operational_state_digest": "sha256:state",
        "projection_receipt_ref": "goal-projection:sha256:old",
        "source_verification_receipt_ref": "goal-source-verification:sha256:old",
    }
    values.update(changes)
    return GoalProjectionEvidenceV1(**values)


def test_equivalent_current_projection_permits_only_host_rebinding() -> None:
    previous = _evidence()
    candidate = _evidence(
        source_revision="c" * 40,
        goal_sha256="sha256:" + "d" * 64,
        projection_receipt_ref="goal-projection:sha256:new",
        source_verification_receipt_ref="goal-source-verification:sha256:new",
    )
    receipt = assess_goal_projection_advancement(
        previous=previous,
        candidate=candidate,
        observed_current_source_revision=candidate.source_revision,
    )
    assert receipt.source_currentness is GoalProjectionSourceCurrentness.CURRENT
    assert receipt.projection_change is GoalProjectionChange.UNCHANGED
    assert receipt.host_rebinding_eligible
    assert set(receipt.to_wire()["effects"].values()) == {"none"}


def test_semantic_change_requires_full_advancement() -> None:
    candidate = _evidence(
        source_revision="c" * 40,
        lowered_intent_stream_digest="sha256:changed-intents",
    )
    receipt = assess_goal_projection_advancement(
        previous=_evidence(),
        candidate=candidate,
        observed_current_source_revision=candidate.source_revision,
    )
    assert receipt.projection_change is GoalProjectionChange.CHANGED
    assert not receipt.host_rebinding_eligible


def test_stale_source_and_projector_drift_fail_ambiguous() -> None:
    candidate = _evidence(
        source_revision="c" * 40,
        projector_version="2",
    )
    receipt = assess_goal_projection_advancement(
        previous=_evidence(),
        candidate=candidate,
        observed_current_source_revision="d" * 40,
    )
    assert receipt.projection_change is GoalProjectionChange.AMBIGUOUS
    assert receipt.blocker_codes == (
        "projector_identity_changed",
        "candidate_source_stale",
    )
    assert not receipt.host_rebinding_eligible


def test_receipt_is_deterministic() -> None:
    arguments = {
        "previous": _evidence(),
        "candidate": _evidence(source_revision="c" * 40),
        "observed_current_source_revision": "c" * 40,
    }
    assert assess_goal_projection_advancement(**arguments) == (
        assess_goal_projection_advancement(**arguments)
    )
