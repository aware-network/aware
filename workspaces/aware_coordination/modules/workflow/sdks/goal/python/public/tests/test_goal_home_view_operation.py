from __future__ import annotations

import pytest
from aware_goal_service_view_compat.operation import (
    GoalHomeViewResolveOutcome,
    GoalHomeViewResolveRequest,
    GoalHomeViewResolveResult,
    GoalOperationContractError,
    GoalPursuitCurrentnessOutcome,
    GoalPursuitCurrentnessVerifyRequest,
    GoalPursuitCurrentnessVerifyResult,
    GoalPursuitIssueOutcome,
    GoalPursuitIssueRequest,
    GoalPursuitIssueResult,
    GoalSdkOperationClient,
)
from aware_goals.views.workflow.goal.v1 import GoalHomeViewStateV1


class _Provider:
    def resolve_home_view(
        self, request: GoalHomeViewResolveRequest
    ) -> GoalHomeViewResolveResult:
        return GoalHomeViewResolveResult(
            outcome=GoalHomeViewResolveOutcome.FOUND,
            goal_ref=request.goal_ref,
            view=GoalHomeViewStateV1(tag=request.goal_ref, title="Example"),
            provider_ref="test.provider",
            provider_distribution="test-provider",
            provider_version="1.0.0",
        )


def test_client_invokes_injected_provider() -> None:
    request = GoalHomeViewResolveRequest(goal_ref="goal/2026-09-20/example")
    result = GoalSdkOperationClient(provider=_Provider()).resolve_home_view(request)

    assert result.outcome is GoalHomeViewResolveOutcome.FOUND
    assert result.operation_ref == "goal_sdk.resolve_goal_home_view"
    assert result.view is not None
    assert result.view.tag == request.goal_ref


def test_found_requires_matching_view_identity() -> None:
    with pytest.raises(GoalOperationContractError, match="must match goal_ref"):
        GoalHomeViewResolveResult(
            outcome=GoalHomeViewResolveOutcome.FOUND,
            goal_ref="goal/2026-09-20/example",
            view=GoalHomeViewStateV1(
                tag="goal/2026-09-20/different",
                title="Different",
            ),
            provider_ref="test.provider",
            provider_distribution="test-provider",
            provider_version="1.0.0",
        )


def test_refusal_cannot_carry_default_view() -> None:
    with pytest.raises(GoalOperationContractError, match="must not carry a view"):
        GoalHomeViewResolveResult(
            outcome=GoalHomeViewResolveOutcome.ABSENT,
            goal_ref="goal/2026-09-20/example",
            view=GoalHomeViewStateV1(),
            provider_ref="test.provider",
            provider_distribution="test-provider",
            provider_version="1.0.0",
        )


def test_pursuit_requests_validate_digest_and_receipt_coordinates() -> None:
    request = GoalPursuitIssueRequest(
        goal_ref="goal/2026-09-20/example",
        lane_key="delivery",
        row_key="implementation",
        expected_goal_sha256="a" * 64,
    )
    assert request.to_wire()["expected_goal_sha256"] == "a" * 64

    with pytest.raises(GoalOperationContractError, match="lowercase SHA-256"):
        GoalPursuitIssueRequest(
            goal_ref=request.goal_ref,
            lane_key=request.lane_key,
            row_key=request.row_key,
            expected_goal_sha256="A" * 64,
        )
    with pytest.raises(GoalOperationContractError, match="Goal pursuit SHA-256"):
        GoalPursuitCurrentnessVerifyRequest(
            goal_ref=request.goal_ref,
            lane_key=request.lane_key,
            row_key=request.row_key,
            expected_goal_sha256="a" * 64,
            pursuit_ref="not-a-pursuit",
        )


def test_pursuit_results_enforce_receipt_posture() -> None:
    coordinates = {
        "goal_ref": "goal/2026-09-20/example",
        "lane_key": "delivery",
        "row_key": "implementation",
        "provider_ref": "test.provider",
        "provider_distribution": "test-provider",
        "provider_version": "1.0.0",
    }
    with pytest.raises(GoalOperationContractError, match="must be a text-keyed"):
        GoalPursuitIssueResult(
            outcome=GoalPursuitIssueOutcome.ISSUED,
            **coordinates,
        )
    with pytest.raises(GoalOperationContractError, match="must not carry"):
        GoalPursuitIssueResult(
            outcome=GoalPursuitIssueOutcome.REFUSED,
            receipt={"schema_id": "aware.goal.pursuit.receipt.v0"},
            **coordinates,
        )
    with pytest.raises(GoalOperationContractError, match="status must match"):
        GoalPursuitCurrentnessVerifyResult(
            outcome=GoalPursuitCurrentnessOutcome.CURRENT,
            currentness={
                "schema_id": "aware.goal.pursuit.currentness.v0",
                "status": "stale",
                "goal_tag": coordinates["goal_ref"],
                "lane_key": coordinates["lane_key"],
                "row_key": coordinates["row_key"],
            },
            **coordinates,
        )
