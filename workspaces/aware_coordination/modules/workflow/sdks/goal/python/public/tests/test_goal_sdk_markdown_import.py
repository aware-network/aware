from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest

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

from aware_goal_sdk import (  # noqa: E402
    load_goal_markdown_import_plan,
    parse_goal_markdown_import_plan,
)
from aware_goal_service_view_compat import (  # noqa: E402
    GoalSdkClient,
    apply_goal_markdown_import_plan,
    goal_home_view_state_from_markdown_import_plan,
)
from aware_goal_service_dto.goal.goal_service_operation import (  # noqa: E402
    ActivateGoalRequest,
)
from aware_goal_service_dto.goal.goal_service_operation import (  # noqa: E402
    ActivateGoalResponse,
)
from aware_goal_service_dto.goal.goal_service_operation import (  # noqa: E402
    EnsureGoalLaneIssueRequest,
)
from aware_goal_service_dto.goal.goal_service_operation import (  # noqa: E402
    EnsureGoalLaneIssueResponse,
)
from aware_goal_service_dto.goal.goal_service_operation import (  # noqa: E402
    EnsureGoalLaneRequest,
)
from aware_goal_service_dto.goal.goal_service_operation import (  # noqa: E402
    EnsureGoalLaneResponse,
)
from aware_goal_service_dto.goal.goal_service_operation import (  # noqa: E402
    EnsureGoalRequest,
)
from aware_goal_service_dto.goal.goal_service_operation import (  # noqa: E402
    EnsureGoalResponse,
)
from aware_goal_service_dto.goal.goal_service_operation import (  # noqa: E402
    GoalLaneIssueSnapshot,
)
from aware_goal_service_dto.goal.goal_service_operation import (  # noqa: E402
    GoalLaneSnapshot,
)
from aware_goal_service_dto.goal.goal_service_operation import (  # noqa: E402
    GoalSnapshot,
)


def test_goal_markdown_import_plan_parses_lane_aware_goal() -> None:
    plan = parse_goal_markdown_import_plan(
        _goal_markdown(),
        source_path=(
            "docs/goals/2026/06/05/"
            "goal-2026-06-05-coordination-interface-goal-issue-native-pane-v0.md"
        ),
    )

    assert plan.goal_tag == "goal/coordination/interface"
    assert plan.title == "Coordination Interface"
    assert plan.status_snapshot == "Active"
    assert plan.priority_level_token == "P0"
    assert plan.source_sha256 is not None
    assert [lane.lane_key for lane in plan.lanes] == [
        "sdk-view-seed",
        "aware-run-mount",
    ]
    assert plan.lanes[0].current_issue_tag == (
        "fb/2026-06-05/goal-sdk-public-markdown-import-view-seed-v0"
    )
    assert [issue.row_key for issue in plan.lane_issues] == [
        "goal-sdk-public-markdown-import-view-seed-v0",
        "aware-run-goal-lane-issue-board-v0",
    ]
    assert plan.lane_issues[0].planned_issue_tag == (
        "fb/2026-06-05/goal-sdk-public-markdown-import-view-seed-v0"
    )
    assert plan.lane_issues[0].tick_token == "[~]"
    assert [issue.row_number for issue in plan.lane_issues] == [1, 1]


def test_goal_markdown_import_plan_builds_seed_view_state() -> None:
    plan = parse_goal_markdown_import_plan(_goal_markdown())

    state = goal_home_view_state_from_markdown_import_plan(plan)
    state_again = goal_home_view_state_from_markdown_import_plan(plan)

    assert state.goal_id == state_again.goal_id
    assert state.provenance["source_kind"] == "markdown_seed"
    assert state.provenance["service_resolved"] is False
    assert state.provenance["lane_count"] == 2
    assert state.provenance["lane_issue_count"] == 2
    assert state.status_tone == "pending"
    assert state.priority_tone == "warning"
    lanes = {lane.lane_key: lane for lane in state.lanes}
    assert lanes["sdk-view-seed"].status_tone == "pending"
    sdk_issue = lanes["sdk-view-seed"].issues[0]
    assert sdk_issue.title == "Public SDK turns Goal Markdown into typed view seed."
    assert sdk_issue.summary == "Public SDK turns Goal Markdown into typed view seed."
    assert sdk_issue.status == "In Progress"
    assert sdk_issue.status_token == "in_progress"
    assert sdk_issue.status_tone == "pending"
    assert sdk_issue.issue_ref == (
        "fb/2026-06-05/goal-sdk-public-markdown-import-view-seed-v0"
    )
    assert sdk_issue.display_ref == "goal-sdk-public-markdown-import-view-seed-v0"
    assert lanes["aware-run-mount"].issues[0].planned_issue_tag == (
        "TBD:aware-run-goal-lane-issue-board-v0"
    )
    assert (
        lanes["aware-run-mount"].issues[0].display_ref
        == "aware-run-goal-lane-issue-board-v0"
    )


def test_goal_markdown_import_plan_loads_from_file(tmp_path: Path) -> None:
    goal_path = (
        tmp_path
        / "docs"
        / "goals"
        / "2026"
        / "06"
        / "05"
        / "goal-2026-06-05-coordination-interface-goal-issue-native-pane-v0.md"
    )
    goal_path.parent.mkdir(parents=True)
    goal_path.write_text(_goal_markdown(include_tag=False), encoding="utf-8")

    plan = load_goal_markdown_import_plan(goal_path)

    assert plan.goal_tag == (
        "goal/2026-06-05/coordination-interface-goal-issue-native-pane-v0"
    )
    assert plan.source_path == goal_path.as_posix()


def test_goal_markdown_import_plan_supports_lane_issues_projection_table() -> None:
    plan = parse_goal_markdown_import_plan(
        "\n".join(
            [
                "# Goal: Projected Goal",
                "",
                "- Tag: `goal/projected`",
                "",
                "## Lane Issues",
                "",
                "### workflow-agent-ux",
                "",
                "| Row | Tick | Status | Gate | Issue | Owner | Receipt |",
                "| --- | --- | --- | --- | --- | --- | --- |",
                "| 15. goal-view | [x] | Closed | Add view | "
                "fb/2026-06-03/goal-experience-view-markdown-projection-v0 | "
                "codex-thread | commit-1 |",
                "",
            ]
        )
    )

    assert [lane.lane_key for lane in plan.lanes] == ["workflow-agent-ux"]
    assert plan.lane_issues[0].row_number == 1
    assert plan.lane_issues[0].row_key == "goal-view"
    assert plan.lane_issues[0].planned_issue_tag == (
        "fb/2026-06-03/goal-experience-view-markdown-projection-v0"
    )


def test_goal_markdown_import_plan_supports_lane_sequences_projection_table() -> None:
    plan = parse_goal_markdown_import_plan(
        "\n".join(
            [
                "# Goal: Projected Goal",
                "",
                "- Tag: `goal/projected`",
                "",
                "## Lane Sequences",
                "",
                "### workflow-agent-ux",
                "",
                "| Step | Key | Tick | Status | Gate | Issue | Owner | Receipt |",
                "| ---: | --- | --- | --- | --- | --- | --- | --- |",
                "| 1 | goal-view | [x] | Closed | Add view | "
                "fb/2026-06-03/goal-experience-view-markdown-projection-v0 | "
                "codex-thread | commit-1 |",
                "",
            ]
        )
    )

    assert [lane.lane_key for lane in plan.lanes] == ["workflow-agent-ux"]
    assert plan.lane_issues[0].row_number == 1
    assert plan.lane_issues[0].row_key == "goal-view"
    assert plan.lane_issues[0].planned_issue_tag == (
        "fb/2026-06-03/goal-experience-view-markdown-projection-v0"
    )


@pytest.mark.asyncio
async def test_apply_goal_markdown_import_plan_invokes_typed_goal_sdk_calls() -> None:
    api_client = _RecordingGeneratedGoalApiClient()
    sdk = GoalSdkClient(api_client=api_client)
    branch_id = uuid4()
    plan = parse_goal_markdown_import_plan(_goal_markdown())

    result = await apply_goal_markdown_import_plan(
        sdk,
        plan,
        branch_id=branch_id,
    )

    ensure_goal_request = api_client.goal.ensure_goal.requests[0]
    assert ensure_goal_request.tag == "goal/coordination/interface"
    assert ensure_goal_request.title == "Coordination Interface"
    assert ensure_goal_request.priority_level_token == "P0"
    assert ensure_goal_request.branch_id == branch_id
    activate_request = api_client.goal.activate_goal.requests[0]
    assert activate_request.goal_id == result.goal.goal_id
    assert activate_request.branch_id == branch_id

    lane_request = api_client.goal.ensure_goal_lane.requests[0]
    assert lane_request.lane_key == "sdk-view-seed"
    assert lane_request.current_issue_tag == (
        "fb/2026-06-05/goal-sdk-public-markdown-import-view-seed-v0"
    )
    assert lane_request.branch_id == branch_id

    issue_request = api_client.goal.ensure_goal_lane_issue.requests[0]
    assert issue_request.row_key == "goal-sdk-public-markdown-import-view-seed-v0"
    assert issue_request.planned_issue_tag == (
        "fb/2026-06-05/goal-sdk-public-markdown-import-view-seed-v0"
    )
    assert issue_request.tick_token == "[~]"
    assert issue_request.branch_id == branch_id

    assert result.view_state.provenance["source_kind"] == "service_resolved"
    assert result.view_state.provenance["input_source_kind"] == "markdown_seed"
    assert result.view_state.provenance["service_resolved"] is True
    assert result.view_state.provenance["lane_count"] == 2
    assert result.view_state.provenance["lane_issue_count"] == 2
    service_lanes = {lane.lane_key: lane for lane in result.view_state.lanes}
    assert service_lanes["sdk-view-seed"].issues[0].title == (
        "Public SDK turns Goal Markdown into typed view seed."
    )


def test_goal_markdown_import_boundary_avoids_service_and_renderer_parsing() -> None:
    source = (
        Path(__file__).parents[2] / "service_view_compat" / "aware_goal_service_view_compat" / "markdown_import.py"
    ).read_text(encoding="utf-8")

    assert "aware_goal_service.api_service_protocol" not in source
    assert "aware_workflow_ontology" not in source
    assert "tools.pane_preview" not in source
    assert "aware_run" not in source


def _goal_markdown(*, include_tag: bool = True) -> str:
    tag_line = "- Tag: `goal/coordination/interface`" if include_tag else ""
    return "\n".join(
        [
            "# Goal: Coordination Interface",
            "",
            tag_line,
            "- Status: `Active`",
            "- Priority: `P0`",
            "",
            "## Lane Map",
            "",
            "| Lane | Owner | Status | Current Issue | Since | Last Receipt | Scope |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            "| `sdk-view-seed` | `codex-thread` | Active | "
            "`docs/issues/2026/06/05/"
            "fb-2026-06-05-goal-sdk-public-markdown-import-view-seed-v0.md` | "
            "`2026-06-05` | `Pending` | Public SDK Markdown seed |",
            "| `aware-run-mount` | `claude` | Planned | "
            "`TBD:aware-run-goal-lane-issue-board-v0` | "
            "`2026-06-05` | `Pending` | aware.run board |",
            "",
            "## Issue Matrix",
            "",
            "| Row | Time | Lane | Tick | Issue | Gate | Status | Owner | Receipt |",
            "| ---: | --- | --- | --- | --- | --- | --- | --- | --- |",
            "| 6 | `2026-06-05` | `sdk-view-seed` | `[~]` | "
            "`docs/issues/2026/06/05/"
            "fb-2026-06-05-goal-sdk-public-markdown-import-view-seed-v0.md` | "
            "Public SDK turns Goal Markdown into typed view seed. | "
            "In Progress | `codex-thread` | Pending |",
            "| 7 | `2026-06-05` | `aware-run-mount` | `[ ]` | "
            "`TBD:aware-run-goal-lane-issue-board-v0` | "
            "aware.run renders SDK GoalHomeViewStateV1. | "
            "Planned | `claude` | Pending |",
            "",
        ]
    )


class _RecordingEnsureGoalClient:
    def __init__(self) -> None:
        self.requests: list[EnsureGoalRequest] = []

    async def ensure_goal(self, request: EnsureGoalRequest) -> EnsureGoalResponse:
        self.requests.append(request)
        return EnsureGoalResponse(
            request_id=request.request_id,
            goal=GoalSnapshot(
                goal_id=uuid4(),
                tag=request.tag,
                title=request.title,
                status="proposed",
                priority_level=request.priority_level_token,
            ),
        )


class _RecordingActivateGoalClient:
    def __init__(self) -> None:
        self.requests: list[ActivateGoalRequest] = []

    async def activate_goal(
        self,
        request: ActivateGoalRequest,
    ) -> ActivateGoalResponse:
        self.requests.append(request)
        return ActivateGoalResponse(
            request_id=request.request_id,
            goal=GoalSnapshot(
                goal_id=request.goal_id,
                tag="goal/coordination/interface",
                title="Coordination Interface",
                status="active",
                priority_level="P0",
            ),
        )


class _RecordingEnsureGoalLaneClient:
    def __init__(self) -> None:
        self.requests: list[EnsureGoalLaneRequest] = []

    async def ensure_goal_lane(
        self,
        request: EnsureGoalLaneRequest,
    ) -> EnsureGoalLaneResponse:
        self.requests.append(request)
        return EnsureGoalLaneResponse(
            request_id=request.request_id,
            goal_lane=GoalLaneSnapshot(
                goal_id=request.goal_id,
                goal_lane_id=uuid4(),
                lane_key=request.lane_key,
                role_key=request.role_key,
                role_label=request.role_label,
                owner_execution_id=request.owner_execution_id,
                owner_actor_id=request.owner_actor_id,
                owner_actor_role_id=request.owner_actor_role_id,
                status=request.status_token,
                current_issue_id=request.current_issue_id,
                current_issue_tag=request.current_issue_tag,
                since_snapshot=request.since_snapshot,
                last_receipt_ref=request.last_receipt_ref,
                scope=request.scope,
            ),
        )


class _RecordingEnsureGoalLaneIssueClient:
    def __init__(self) -> None:
        self.requests: list[EnsureGoalLaneIssueRequest] = []

    async def ensure_goal_lane_issue(
        self,
        request: EnsureGoalLaneIssueRequest,
    ) -> EnsureGoalLaneIssueResponse:
        self.requests.append(request)
        return EnsureGoalLaneIssueResponse(
            request_id=request.request_id,
            goal_lane_issue=GoalLaneIssueSnapshot(
                goal_id=request.goal_id,
                goal_lane_id=request.goal_lane_id,
                goal_lane_issue_id=uuid4(),
                row_key=request.row_key,
                row_number=request.row_number,
                sync_time_snapshot=request.sync_time_snapshot,
                issue_id=request.issue_id,
                planned_issue_tag=request.planned_issue_tag,
                gate=request.gate,
                tick=request.tick_token,
                status_snapshot=request.status_snapshot,
                owner_execution_id=request.owner_execution_id,
                owner_actor_id=request.owner_actor_id,
                owner_actor_role_id=request.owner_actor_role_id,
                receipt_ref=request.receipt_ref,
            ),
        )


class _UnsupportedCapabilityClient:
    async def block_goal(self, request):  # noqa: ANN001
        raise AssertionError(f"Unexpected block_goal call: {request!r}")

    async def park_goal(self, request):  # noqa: ANN001
        raise AssertionError(f"Unexpected park_goal call: {request!r}")

    async def resume_goal(self, request):  # noqa: ANN001
        raise AssertionError(f"Unexpected resume_goal call: {request!r}")

    async def achieve_goal(self, request):  # noqa: ANN001
        raise AssertionError(f"Unexpected achieve_goal call: {request!r}")

    async def supersede_goal(self, request):  # noqa: ANN001
        raise AssertionError(f"Unexpected supersede_goal call: {request!r}")


class _RecordingGoalApiNamespace:
    def __init__(self) -> None:
        self.ensure_goal = _RecordingEnsureGoalClient()
        self.ensure_goal_lane = _RecordingEnsureGoalLaneClient()
        self.ensure_goal_lane_issue = _RecordingEnsureGoalLaneIssueClient()
        self.activate_goal = _RecordingActivateGoalClient()
        unsupported = _UnsupportedCapabilityClient()
        self.block_goal = unsupported
        self.park_goal = unsupported
        self.resume_goal = unsupported
        self.achieve_goal = unsupported
        self.supersede_goal = unsupported


class _RecordingGeneratedGoalApiClient:
    def __init__(self) -> None:
        self.goal = _RecordingGoalApiNamespace()
