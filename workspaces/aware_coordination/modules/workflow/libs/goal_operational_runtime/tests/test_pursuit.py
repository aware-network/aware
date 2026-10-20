from __future__ import annotations

from dataclasses import dataclass, field, replace

import pytest
from aware_goal_operational_runtime import (
    GoalCheckpointIntent,
    GoalCheckpointKind,
    GoalExecutionReadiness,
    GoalIssueReconciliationAction,
    GoalIssueReconciliationIntent,
    GoalPursuitCurrentnessReceipt,
    GoalPursuitDirectionBindingV1,
    GoalPursuitProjectionV1,
    GoalPursuitReceipt,
    GoalReconciliationAssessmentInput,
    GoalReconciliationRecommendation,
    GoalSuccessorSemantics,
    assess_goal_issue_reconciliation,
    issue_goal_checkpoint_receipt,
    issue_goal_issue_reconciliation_receipt,
    issue_goal_pursuit_receipt,
    issue_goal_pursuit_receipt_v1,
    validate_goal_pursuit_receipt_v1,
    verify_goal_pursuit_currentness,
    verify_goal_pursuit_currentness_v1,
)


def _assessment(**changes: object) -> GoalReconciliationAssessmentInput:
    values: dict[str, object] = {
        "goal_tag": "goal/test",
        "lane_key": "delivery",
        "row_key": "ship",
        "current_issue_ref": "docs/issues/current.md",
        "current_issue_status": "Closed",
    }
    values.update(changes)
    return GoalReconciliationAssessmentInput(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("observed", "recommendation", "reason"),
    (
        (
            _assessment(current_issue_status="In Progress"),
            GoalReconciliationRecommendation.HOLD,
            "current_issue_not_closed",
        ),
        (
            _assessment(
                checkpoint_ref="goal-checkpoint:accepted",
                checkpoint_readiness=GoalExecutionReadiness.ACCEPTED,
                gate_evidence_refs=("acceptance:proof",),
            ),
            GoalReconciliationRecommendation.COMPLETE_ROW,
            "closed_issue_gate_evidence_accepted",
        ),
        (
            _assessment(
                successor_issue_ref="docs/issues/successor.md",
                successor_issue_status="In Progress",
                successor_semantics=GoalSuccessorSemantics.UNCHANGED_GATE,
            ),
            GoalReconciliationRecommendation.CONTINUE_WITH_SUCCESSOR,
            "closed_issue_same_gate_successor_active",
        ),
        (
            _assessment(
                gate_evidence_refs=("settlement:proof",),
                successor_issue_ref="docs/issues/successor.md",
                successor_issue_status="In Progress",
                successor_semantics=GoalSuccessorSemantics.DISTINCT_GATE,
            ),
            GoalReconciliationRecommendation.SPLIT_SUCCESSOR_ROW,
            "settled_predecessor_distinct_gate_successor_active",
        ),
        (
            _assessment(projection_repair_receipt_ref="goal-publication:proof"),
            GoalReconciliationRecommendation.PROJECTION_ONLY,
            "published_semantics_projection_stale",
        ),
    ),
)
def test_reconciliation_assessment_covers_agent_recovery_effects(
    observed: GoalReconciliationAssessmentInput,
    recommendation: GoalReconciliationRecommendation,
    reason: str,
) -> None:
    receipt = assess_goal_issue_reconciliation(observed)

    assert receipt.effect_profile == "read_only_non_authorizing"
    assert receipt.recommendation is recommendation
    assert receipt.reasons == (reason,)
    assert assess_goal_issue_reconciliation(observed) == receipt


def test_reconciliation_assessment_holds_without_distinct_gate_settlement() -> None:
    receipt = assess_goal_issue_reconciliation(
        _assessment(
            successor_issue_ref="docs/issues/successor.md",
            successor_issue_status="In Progress",
            successor_semantics=GoalSuccessorSemantics.DISTINCT_GATE,
        )
    )

    assert receipt.recommendation is GoalReconciliationRecommendation.HOLD
    assert receipt.reasons == ("predecessor_gate_evidence_required",)


def test_reconciliation_assessment_rejects_partial_evidence() -> None:
    with pytest.raises(ValueError, match="checkpoint ref and readiness"):
        _assessment(checkpoint_ref="goal-checkpoint:partial")
    with pytest.raises(ValueError, match="successor evidence must be complete"):
        _assessment(successor_issue_ref="docs/issues/successor.md")


@dataclass(frozen=True)
class Row:
    row_key: str = "ship"
    step: int = 2
    timestamp: str = "2026-09-12T18:43:18Z"
    tick: str = "[~]"
    issue_ref: str = "docs/issues/ship.md"
    gate: str = "Ship the accepted cut."
    status: str = "In Progress"
    owner: str = "codex-test"
    receipt_ref: str = "issue-receipt:test"


@dataclass(frozen=True)
class Lane:
    lane_key: str = "delivery"
    owner: str = "codex-test"
    lane_status: str = "Active"
    pursuit_state: str = "ready"
    suggested_action: str = "continue_issue"
    completion_gate: str | None = "Ship the accepted cut."
    pursuit_directive: str | None = "Run the focused proof."
    pursuit_directive_source: str = "forward_plan"
    pursuit_row: Row | None = Row()
    drift: tuple[str, ...] = ()


@dataclass(frozen=True)
class Snapshot:
    tag: str = "goal/test"
    sha256: str = "a" * 64
    lanes: dict[str, Lane] = field(default_factory=lambda: {"delivery": Lane()})


def _projection(
    *,
    goal_sha256: str = "a" * 64,
    repository_commit: str = "1" * 40,
    goal_blob_oid: str = "2" * 40,
) -> GoalPursuitProjectionV1:
    return GoalPursuitProjectionV1(
        goal_sha256=goal_sha256,
        repository_ref="refs/heads/main",
        repository_commit=repository_commit,
        goal_blob_oid=goal_blob_oid,
    )


def _binding(**changes: str) -> GoalPursuitDirectionBindingV1:
    values = {
        "goal_tag": "goal/test",
        "lane_key": "delivery",
        "row_key": "ship",
        "goal_global_digest": "sha256:" + "3" * 64,
        "lane_digest": "sha256:" + "4" * 64,
        "row_digest": "sha256:" + "5" * 64,
        "incident_dependency_set_digest": "sha256:" + "6" * 64,
        "incoming_dependency_gate_digest": "sha256:" + "7" * 64,
    }
    values.update(changes)
    return GoalPursuitDirectionBindingV1(**values)


def test_pursuit_receipt_is_deterministic_and_non_authorizing() -> None:
    snapshot = Snapshot()

    first = issue_goal_pursuit_receipt(
        snapshot=snapshot,
        lane_key="delivery",
        row_key="ship",
        expected_goal_sha256="sha256:" + snapshot.sha256,
    )
    second = issue_goal_pursuit_receipt(
        snapshot=snapshot,
        lane_key="delivery",
        row_key="ship",
        expected_goal_sha256=snapshot.sha256,
    )

    assert isinstance(first, GoalPursuitReceipt)
    assert first == second
    assert first.effect_profile == "read_only_non_authorizing"
    assert first.pursuit_ref == (
        "goal-pursuit:sha256:"
        "bec739dbe38068a6fced5e138e0f5df08cdd6d09bffe24293555f4afc18ce69f"
    )
    assert first.completion_gate == first.gate


def test_pursuit_rejects_stale_digest_wrong_row_and_gate_drift() -> None:
    snapshot = Snapshot()
    with pytest.raises(ValueError, match="digest mismatch"):
        _ = issue_goal_pursuit_receipt(
            snapshot=snapshot,
            lane_key="delivery",
            row_key="ship",
            expected_goal_sha256="b" * 64,
        )
    with pytest.raises(ValueError, match="row mismatch"):
        _ = issue_goal_pursuit_receipt(
            snapshot=snapshot,
            lane_key="delivery",
            row_key="other",
            expected_goal_sha256=snapshot.sha256,
        )
    drifted_lane = replace(Lane(), completion_gate="Different gate")
    with pytest.raises(ValueError, match="completion gate differs"):
        _ = issue_goal_pursuit_receipt(
            snapshot=replace(snapshot, lanes={"delivery": drifted_lane}),
            lane_key="delivery",
            row_key="ship",
            expected_goal_sha256=snapshot.sha256,
        )
    blocked_lane = replace(Lane(), pursuit_state="blocked", drift=("blocked",))
    with pytest.raises(ValueError, match="cannot issue a ready pursuit receipt"):
        _ = issue_goal_pursuit_receipt(
            snapshot=replace(snapshot, lanes={"delivery": blocked_lane}),
            lane_key="delivery",
            row_key="ship",
            expected_goal_sha256=snapshot.sha256,
        )


def test_currentness_distinguishes_digest_change_and_unavailable_pursuit() -> None:
    snapshot = Snapshot()
    receipt = issue_goal_pursuit_receipt(
        snapshot=snapshot,
        lane_key="delivery",
        row_key="ship",
        expected_goal_sha256=snapshot.sha256,
    )

    current = verify_goal_pursuit_currentness(
        snapshot=snapshot,
        lane_key="delivery",
        row_key="ship",
        expected_goal_sha256=snapshot.sha256,
        pursuit_ref=receipt.pursuit_ref,
    )
    changed = verify_goal_pursuit_currentness(
        snapshot=replace(snapshot, sha256="b" * 64),
        lane_key="delivery",
        row_key="ship",
        expected_goal_sha256=snapshot.sha256,
        pursuit_ref=receipt.pursuit_ref,
    )
    blocked_lane = replace(Lane(), pursuit_state="blocked", drift=("blocked",))
    unavailable = verify_goal_pursuit_currentness(
        snapshot=replace(snapshot, lanes={"delivery": blocked_lane}),
        lane_key="delivery",
        row_key="ship",
        expected_goal_sha256=snapshot.sha256,
        pursuit_ref=receipt.pursuit_ref,
    )
    receipt_changed = verify_goal_pursuit_currentness(
        snapshot=snapshot,
        lane_key="delivery",
        row_key="ship",
        expected_goal_sha256=snapshot.sha256,
        pursuit_ref=f"goal-pursuit:sha256:{'0' * 64}",
    )

    assert isinstance(current, GoalPursuitCurrentnessReceipt)
    assert current.status == "current"
    assert current.reasons == ()
    assert changed.status == "stale"
    assert changed.reasons == ("goal_digest_changed",)
    assert unavailable.status == "stale"
    assert unavailable.reasons == ("pursuit_unavailable",)
    assert receipt_changed.status == "stale"
    assert receipt_changed.reasons == ("pursuit_receipt_changed",)


def test_v1_receipt_is_deterministic_integrity_bound_and_non_authorizing() -> None:
    first = issue_goal_pursuit_receipt_v1(
        snapshot=Snapshot(),
        lane_key="delivery",
        row_key="ship",
        expected_goal_sha256="a" * 64,
        projection=_projection(),
        direction_binding=_binding(),
    )
    second = issue_goal_pursuit_receipt_v1(
        snapshot=Snapshot(),
        lane_key="delivery",
        row_key="ship",
        expected_goal_sha256="sha256:" + "a" * 64,
        projection=_projection(),
        direction_binding=_binding(),
    )

    assert first == second
    assert first.schema_id == "aware.goal.pursuit.receipt.v1"
    assert first.effect_profile == "read_only_non_authorizing"
    assert first.direction_ref.startswith("goal-pursuit-direction:sha256:")
    assert first.pursuit_ref.startswith("goal-pursuit:sha256:")
    validate_goal_pursuit_receipt_v1(first)

    with pytest.raises(ValueError, match="direction_ref"):
        validate_goal_pursuit_receipt_v1(
            replace(first, direction_ref="goal-pursuit-direction:sha256:" + "0" * 64)
        )
    with pytest.raises(ValueError, match="pursuit_ref"):
        validate_goal_pursuit_receipt_v1(
            replace(first, pursuit_ref="goal-pursuit:sha256:" + "0" * 64)
        )


def test_v1_currentness_allows_only_proven_unrelated_projection_advance() -> None:
    receipt = issue_goal_pursuit_receipt_v1(
        snapshot=Snapshot(),
        lane_key="delivery",
        row_key="ship",
        expected_goal_sha256="a" * 64,
        projection=_projection(),
        direction_binding=_binding(),
    )

    exact = verify_goal_pursuit_currentness_v1(
        receipt=receipt,
        observed_projection=_projection(),
        observed_direction_binding=_binding(),
        observed_descends_from_expected=None,
    )
    advanced = verify_goal_pursuit_currentness_v1(
        receipt=receipt,
        observed_projection=_projection(
            goal_sha256="b" * 64,
            repository_commit="8" * 40,
            goal_blob_oid="9" * 40,
        ),
        observed_direction_binding=_binding(),
        observed_descends_from_expected=True,
    )
    unproven = verify_goal_pursuit_currentness_v1(
        receipt=receipt,
        observed_projection=_projection(
            goal_sha256="b" * 64,
            repository_commit="8" * 40,
            goal_blob_oid="9" * 40,
        ),
        observed_direction_binding=_binding(),
        observed_descends_from_expected=False,
    )

    assert (
        exact.direction_currentness,
        exact.projection_currentness,
        exact.replay_disposition,
        exact.reasons,
    ) == ("current", "current", "exact", ("projection_unchanged",))
    assert (
        advanced.direction_currentness,
        advanced.projection_currentness,
        advanced.replay_disposition,
        advanced.reasons,
    ) == (
        "current",
        "advanced",
        "replayable",
        ("projection_advanced_direction_unchanged",),
    )
    assert unproven.direction_currentness == "ambiguous"
    assert unproven.projection_currentness == "unknown"
    assert unproven.replay_disposition == "refuse"
    assert unproven.reasons == ("projection_lineage_unproven",)


@pytest.mark.parametrize(
    ("field", "reason"),
    (
        ("goal_global_digest", "goal_global_direction_changed"),
        ("lane_digest", "lane_direction_changed"),
        ("row_digest", "row_direction_changed"),
        ("incident_dependency_set_digest", "incident_dependency_set_changed"),
        ("incoming_dependency_gate_digest", "incoming_dependency_gate_changed"),
    ),
)
def test_v1_currentness_refuses_every_relevant_semantic_change(
    field: str, reason: str
) -> None:
    receipt = issue_goal_pursuit_receipt_v1(
        snapshot=Snapshot(),
        lane_key="delivery",
        row_key="ship",
        expected_goal_sha256="a" * 64,
        projection=_projection(),
        direction_binding=_binding(),
    )
    changed = verify_goal_pursuit_currentness_v1(
        receipt=receipt,
        observed_projection=_projection(
            goal_sha256="b" * 64,
            repository_commit="8" * 40,
            goal_blob_oid="9" * 40,
        ),
        observed_direction_binding=_binding(**{field: "sha256:" + "f" * 64}),
        observed_descends_from_expected=True,
    )

    assert changed.direction_currentness == "stale"
    assert changed.projection_currentness == "advanced"
    assert changed.replay_disposition == "refuse"
    assert changed.reasons == (reason,)


def test_v1_rejects_coordinate_drift_and_ambiguous_semantics() -> None:
    receipt = issue_goal_pursuit_receipt_v1(
        snapshot=Snapshot(),
        lane_key="delivery",
        row_key="ship",
        expected_goal_sha256="a" * 64,
        projection=_projection(),
        direction_binding=_binding(),
    )
    changed_identity = verify_goal_pursuit_currentness_v1(
        receipt=receipt,
        observed_projection=_projection(
            goal_sha256="b" * 64,
            repository_commit="8" * 40,
            goal_blob_oid="9" * 40,
        ),
        observed_direction_binding=_binding(row_key="other"),
        observed_descends_from_expected=True,
    )
    ambiguous = verify_goal_pursuit_currentness_v1(
        receipt=receipt,
        observed_projection=_projection(
            goal_sha256="b" * 64,
            repository_commit="8" * 40,
            goal_blob_oid="9" * 40,
        ),
        observed_direction_binding=None,
        observed_descends_from_expected=True,
    )

    assert changed_identity.direction_currentness == "stale"
    assert changed_identity.reasons == ("goal_identity_changed",)
    assert ambiguous.direction_currentness == "ambiguous"
    assert ambiguous.replay_disposition == "refuse"
    assert ambiguous.reasons == ("semantic_projection_ambiguous",)


def test_goal_issue_reconciliation_requires_explicit_distinct_action() -> None:
    intent = GoalIssueReconciliationIntent(
        goal_tag="goal/test",
        lane_key="delivery",
        row_key="ship",
        authority_issue_ref="docs/issues/authority.md",
        action=GoalIssueReconciliationAction.CONTINUE_WITH_SUCCESSOR,
        evidence_refs=("commit:authority-close",),
        successor_issue_ref="docs/issues/implementation.md",
    )

    first = issue_goal_issue_reconciliation_receipt(intent)
    second = issue_goal_issue_reconciliation_receipt(intent)

    assert first == second
    assert first.effect_profile == "direction_only_non_authorizing"
    assert first.reconciliation_ref.startswith("goal-issue-reconciliation:sha256:")
    with pytest.raises(ValueError, match="successor Issue must differ"):
        GoalIssueReconciliationIntent(
            goal_tag="goal/test",
            lane_key="delivery",
            row_key="ship",
            authority_issue_ref="docs/issues/same.md",
            action=GoalIssueReconciliationAction.CONTINUE_WITH_SUCCESSOR,
            evidence_refs=("commit:authority-close",),
            successor_issue_ref="docs/issues/same.md",
        )


@pytest.mark.parametrize(
    ("readiness", "recommended_action"),
    [
        (GoalExecutionReadiness.READY, "continue_issue"),
        (GoalExecutionReadiness.AWAITING_INPUTS, "hold"),
        (GoalExecutionReadiness.BLOCKED, "hold"),
        (GoalExecutionReadiness.ACCEPTED, "evaluate_complete_row"),
    ],
)
def test_goal_checkpoint_is_deterministic_and_non_authorizing(
    readiness: GoalExecutionReadiness,
    recommended_action: str,
) -> None:
    intent = GoalCheckpointIntent(
        goal_tag="goal/test",
        lane_key="delivery",
        row_key="ship",
        pursuit_ref="goal-pursuit:sha256:direction",
        kind=GoalCheckpointKind.READINESS,
        readiness=readiness,
        evidence_refs=("handoff:one", "handoff:two"),
        summary="Record execution readiness without changing the Goal row.",
        timestamp="2026-09-13T20:00:00Z",
    )

    first = issue_goal_checkpoint_receipt(intent)
    second = issue_goal_checkpoint_receipt(intent)

    assert first == second
    assert first.effect_profile == "evidence_only_non_authorizing"
    assert first.recommended_action == recommended_action
    assert first.checkpoint_ref.startswith("goal-checkpoint:sha256:")


def test_goal_checkpoint_requires_evidence() -> None:
    with pytest.raises(ValueError, match="explicit evidence_refs"):
        GoalCheckpointIntent(
            goal_tag="goal/test",
            lane_key="delivery",
            row_key="ship",
            pursuit_ref="goal-pursuit:sha256:direction",
            kind=GoalCheckpointKind.READINESS,
            readiness=GoalExecutionReadiness.AWAITING_INPUTS,
            evidence_refs=(),
            summary="Await inputs.",
            timestamp="2026-09-13T20:00:00Z",
        )
