from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

from _goal_sdk_public_test_paths import (  # noqa: E402
    AWARE_GOALS_LANGUAGE_ROOT,
    GOAL_SERVICE_DTO_ROOT,
    PUBLIC_SDK_ROOT,
)

for _path in (
    PUBLIC_SDK_ROOT,
    GOAL_SERVICE_DTO_ROOT,
    AWARE_GOALS_LANGUAGE_ROOT,
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_goal_service_view_compat import (  # noqa: E402
    GoalHomeV1ProviderInput,
    GoalServiceDeltaV1,
    ViewProviderProvenanceV1,
    goal_home_v1_provider_input,
    goal_home_view_state,
    goal_home_view_state_from_input,
    render_goal_markdown_from_view,
)
from aware_goal_service_dto.goal.goal_service_operation import (  # noqa: E402
    GoalLaneIssueSnapshot,
)
from aware_goal_service_dto.goal.goal_service_operation import (  # noqa: E402
    GoalLaneSnapshot,
)
from aware_goal_service_dto.goal.goal_service_operation import (
    GoalSnapshot,
)  # noqa: E402
from aware_goals.views.workflow.goal.v1 import GoalHomeViewStateV1  # noqa: E402


def test_goal_home_view_state_provider_resolves_service_snapshots() -> None:
    bundle = _snapshot_bundle()
    provider_input = GoalHomeV1ProviderInput(
        goal=bundle.goal,
        lanes=[bundle.unrelated_lane, bundle.lane],
        lane_issues=[bundle.second_issue, bundle.first_issue],
        service_deltas=[
            GoalServiceDeltaV1(
                delta_id="delta-1",
                commit_id="commit-1",
                kind="goal_service_response",
                payload={"operation": "ensure_goal_lane_issue"},
            )
        ],
        provenance=ViewProviderProvenanceV1(
            branch_id="branch-1",
            head_commit_id="commit-1",
            view_ref=GoalHomeViewStateV1.VIEW_REF,
            service_operation="resolve_goal_home",
        ),
    )

    state = goal_home_view_state_from_input(provider_input)

    assert isinstance(state, GoalHomeViewStateV1)
    assert state.goal_id == str(bundle.goal.goal_id)
    assert state.tag == "goal/coordination/view"
    assert state.status == "active"
    assert state.status_tone == "pending"
    assert state.priority == "high"
    assert state.priority_tone == "warning"
    assert len(state.lanes) == 1
    assert state.lanes[0].lane_key == "workflow-agent-ux"
    assert state.lanes[0].status_tone == "pending"
    assert state.lanes[0].owner_execution_id == "codex-thread-1"
    assert [item.row_key for item in state.lanes[0].issues] == [
        "goal-view",
        "local-fs-sync",
    ]
    first_issue = state.lanes[0].issues[0]
    assert first_issue.title == "Render the Goal board from the service view"
    assert first_issue.summary == "Render the Goal board from the service view"
    assert first_issue.status_token == "planned"
    assert first_issue.status_tone == "neutral"
    assert first_issue.issue_ref == (
        "fb/2026-06-03/goal-experience-view-markdown-projection-v0"
    )
    assert first_issue.display_ref == "goal-experience-view-markdown-projection-v0"
    assert state.provenance["branch_id"] == "branch-1"
    assert state.provenance["lane_count"] == 2
    assert state.provenance["lane_issue_count"] == 2
    assert state.provenance["service_delta_count"] == 1
    assert state.to_json()["lanes"][0]["issues"][0]["row_key"] == "goal-view"


def test_goal_home_view_state_provider_accepts_typed_input_only() -> None:
    bundle = _snapshot_bundle()
    state = goal_home_view_state(
        provider_input=GoalHomeV1ProviderInput(
            goal=bundle.goal,
            lanes=[bundle.lane],
            lane_issues=[bundle.first_issue],
            provenance=ViewProviderProvenanceV1(branch_id="branch-2"),
        )
    )

    assert state.status == "active"
    assert state.provenance["branch_id"] == "branch-2"
    assert state.lanes[0].issues[0].planned_issue_tag == (
        "fb/2026-06-03/goal-experience-view-markdown-projection-v0"
    )


def test_goal_home_view_state_provider_waits_without_service_snapshot() -> None:
    state = goal_home_view_state(
        provider_input=GoalHomeV1ProviderInput(
            provenance=ViewProviderProvenanceV1(branch_id="branch-3"),
        )
    )

    assert state.status == "waiting"
    assert state.title == "Goal"
    assert state.lanes == []
    assert state.provenance["branch_id"] == "branch-3"


def test_goal_home_provider_input_resolver_uses_service_view_context() -> None:
    bundle = _snapshot_bundle()
    provider_context = SimpleNamespace(
        provenance={
            "branch_id": "branch-4",
            "projection_view_key": "workflow.goal.v1",
        },
        latest_goal_snapshot=lambda: bundle.goal.model_dump(mode="json"),
        goal_lane_snapshots=lambda: [bundle.lane.model_dump(mode="json")],
        goal_lane_issue_snapshots=lambda: [bundle.first_issue.model_dump(mode="json")],
        service_deltas=lambda: [
            {
                "delta_id": "delta-2",
                "commit_id": "commit-2",
                "kind": "goal_service_view",
                "payload": {"changed": True},
            }
        ],
    )

    provider_input = goal_home_v1_provider_input(provider_context)
    state = goal_home_view_state(provider_input=provider_input)

    assert provider_input.goal is not None
    assert len(provider_input.lanes) == 1
    assert len(provider_input.lane_issues) == 1
    assert len(provider_input.service_deltas) == 1
    assert state.status == "active"
    assert state.provenance["branch_id"] == "branch-4"
    assert state.provenance["projection_view_key"] == "workflow.goal.v1"


def test_goal_home_provider_exposes_input_resolver() -> None:
    assert (
        getattr(goal_home_view_state, "provider_input_resolver")
        is goal_home_v1_provider_input
    )


def test_goal_markdown_projection_renders_service_view_state() -> None:
    bundle = _snapshot_bundle()
    state = goal_home_view_state(
        provider_input=GoalHomeV1ProviderInput(
            goal=bundle.goal,
            lanes=[bundle.lane],
            lane_issues=[bundle.first_issue],
        )
    )

    markdown = render_goal_markdown_from_view(state)

    assert "# Goal: Service View -> FS projection" in markdown
    assert "- Tag: `goal/coordination/view`" in markdown
    assert "| workflow-agent-ux | codex-thread-1 | active |" in markdown
    assert "fb/2026-06-03/goal-experience-view-markdown-projection-v0" in markdown
    assert "## Lane Sequences" in markdown
    assert "| Step | Key | Tick | Status | Gate | Issue | Owner | Receipt |" in markdown
    assert "| 1 | goal-view | planned | Planned |" in markdown


def test_goal_view_provider_boundary_avoids_raw_graph_and_orm_ontology() -> None:
    provider_source = (
        Path(__file__).parents[2] / "service_view_compat" / "aware_goal_service_view_compat" / "view_state_providers.py"
    ).read_text(encoding="utf-8")

    assert "aware_workflow_ontology." not in provider_source
    assert "latest_ontology" not in provider_source
    assert "materialized_lane" not in provider_source
    assert "class_instances" not in provider_source


class _SnapshotBundle(SimpleNamespace):
    goal: GoalSnapshot
    lane: GoalLaneSnapshot
    unrelated_lane: GoalLaneSnapshot
    first_issue: GoalLaneIssueSnapshot
    second_issue: GoalLaneIssueSnapshot


def _snapshot_bundle() -> _SnapshotBundle:
    goal_id = uuid4()
    lane_id = uuid4()
    unrelated_goal_id = uuid4()
    return _SnapshotBundle(
        goal=GoalSnapshot(
            goal_id=goal_id,
            tag="goal/coordination/view",
            title="Service View -> FS projection",
            status="active",
            priority_level="high",
        ),
        lane=_goal_lane(
            goal_id=goal_id,
            goal_lane_id=lane_id,
            lane_key="workflow-agent-ux",
        ),
        unrelated_lane=_goal_lane(
            goal_id=unrelated_goal_id,
            goal_lane_id=uuid4(),
            lane_key="meta-materialization-truth",
        ),
        first_issue=_goal_lane_issue(
            goal_id=goal_id,
            goal_lane_id=lane_id,
            row_key="goal-view",
            row_number=15,
            planned_issue_tag=(
                "fb/2026-06-03/goal-experience-view-markdown-projection-v0"
            ),
            gate="Render the Goal board from the service view",
        ),
        second_issue=_goal_lane_issue(
            goal_id=goal_id,
            goal_lane_id=lane_id,
            row_key="local-fs-sync",
            row_number=16,
            planned_issue_tag=("fb/2026-06-03/goal-sdk-local-files-view-sync-v0"),
        ),
    )


def _goal_lane(
    *,
    goal_id: UUID,
    goal_lane_id: UUID,
    lane_key: str,
) -> GoalLaneSnapshot:
    return GoalLaneSnapshot(
        goal_id=goal_id,
        goal_lane_id=goal_lane_id,
        lane_key=lane_key,
        role_key="agent",
        role_label="Agent UX",
        owner_execution_id="codex-thread-1",
        status="active",
        current_issue_tag="fb/2026-06-03/goal-experience-view-markdown-projection-v0",
        since_snapshot="2026-06-03T12:00:00Z",
        last_receipt_ref="workspace-materialize:aware-goals",
        scope="Goal service views and SDK projection",
    )


def _goal_lane_issue(
    *,
    goal_id: UUID,
    goal_lane_id: UUID,
    row_key: str,
    row_number: int,
    planned_issue_tag: str,
    gate: str = "P0",
) -> GoalLaneIssueSnapshot:
    return GoalLaneIssueSnapshot(
        goal_id=goal_id,
        goal_lane_id=goal_lane_id,
        goal_lane_issue_id=uuid4(),
        row_key=row_key,
        row_number=row_number,
        gate=gate,
        planned_issue_tag=planned_issue_tag,
        tick="planned",
        status_snapshot="Planned",
        owner_execution_id="codex-thread-1",
        receipt_ref=f"receipt:{row_key}",
    )
