from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest
from _goal_sdk_public_test_paths import (  # noqa: E402
    AWARE_GOALS_LANGUAGE_ROOT,
    CONTENT_SERVICE_DTO_ROOT,
    GOAL_SDK_TOML,
    GOAL_SERVICE_API_ROOT,
    GOAL_SERVICE_DTO_ROOT,
    PUBLIC_SDK_ROOT,
    REPO_ROOT,
    SDK_RUNTIME_ROOT,
)

for _path in (
    PUBLIC_SDK_ROOT,
    GOAL_SERVICE_API_ROOT,
    GOAL_SERVICE_DTO_ROOT,
    CONTENT_SERVICE_DTO_ROOT,
    AWARE_GOALS_LANGUAGE_ROOT,
    SDK_RUNTIME_ROOT,
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_content_service_dto.content.content_service_operation import (  # noqa: E402
    ContentPackageMaterializationResultV1,
    MaterializeContentPackageResponse,
)
from aware_goal_service_view_compat import (  # noqa: E402
    ContentPackageMaterializer,
    GoalHandle,
    GoalLaneHandle,
    GoalLaneIssueHandle,
    GoalSdkClient,
    GoalSdkError,
    goal_content_export_to_content_package_export,
)
from aware_goal_sdk.phase_direction import (  # noqa: E402
    GoalPhaseDirectionClient,
    GoalPhaseDirectionCurrentnessRequestV1,
    GoalPhaseDirectionError,
    GoalPhaseDirectionObserveRequestV1,
)
from aware_goal_service_dto.goal.goal_service_operation import (
    ActivateGoalRequest,
    ActivateGoalResponse,
    EnsureGoalLaneIssueRequest,
    EnsureGoalLaneIssueResponse,
    EnsureGoalLaneRequest,
    EnsureGoalLaneResponse,
    EnsureGoalRequest,
    EnsureGoalResponse,
    GoalContentExportDocumentV1,
    GoalContentExportPartV1,
    GoalLaneIssueSnapshot,
    GoalLaneSnapshot,
    GoalServiceResponse,
    GoalSnapshot,
    GoalWorkspaceArtifactProjectionV1,
    ResolveGoalContentExportRequest,
    ResolveGoalContentExportResponse,
    ResolveGoalHomeViewRequest,
    ResolveGoalHomeViewResponse,
)  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402  # noqa: E402
from aware_goals.views.workflow.goal.v1 import GoalHomeViewStateV1  # noqa: E402


class _RecordingEnsureGoalClient:
    def __init__(self, *, response: EnsureGoalResponse | None = None) -> None:
        self.requests: list[EnsureGoalRequest] = []
        self.response = response

    async def ensure_goal(self, request: EnsureGoalRequest) -> EnsureGoalResponse:
        self.requests.append(request)
        if self.response is not None:
            return self.response
        return EnsureGoalResponse(
            request_id=request.request_id,
            goal=_goal_snapshot(
                tag=request.tag,
                title=request.title,
                status="proposed",
                priority_level=request.priority_level_token,
                overview_content_id=request.overview_content_id,
                definition_of_done_content_id=request.definition_of_done_content_id,
                evidence_chain_id=request.evidence_chain_id,
            ),
        )


class _RecordingEnsureGoalLaneClient:
    def __init__(
        self,
        *,
        response: EnsureGoalLaneResponse | None = None,
    ) -> None:
        self.requests: list[EnsureGoalLaneRequest] = []
        self.response = response

    async def ensure_goal_lane(
        self,
        request: EnsureGoalLaneRequest,
    ) -> EnsureGoalLaneResponse:
        self.requests.append(request)
        if self.response is not None:
            return self.response
        return EnsureGoalLaneResponse(
            request_id=request.request_id,
            goal_lane=_goal_lane_snapshot(
                goal_id=request.goal_id,
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
    def __init__(
        self,
        *,
        response: EnsureGoalLaneIssueResponse | None = None,
    ) -> None:
        self.requests: list[EnsureGoalLaneIssueRequest] = []
        self.response = response

    async def ensure_goal_lane_issue(
        self,
        request: EnsureGoalLaneIssueRequest,
    ) -> EnsureGoalLaneIssueResponse:
        self.requests.append(request)
        if self.response is not None:
            return self.response
        return EnsureGoalLaneIssueResponse(
            request_id=request.request_id,
            goal_lane_issue=_goal_lane_issue_snapshot(
                goal_id=request.goal_id,
                goal_lane_id=request.goal_lane_id,
                row_key=request.row_key,
                gate=request.gate,
                row_number=request.row_number,
                sync_time_snapshot=request.sync_time_snapshot,
                issue_id=request.issue_id,
                planned_issue_tag=request.planned_issue_tag,
                tick=request.tick_token,
                status_snapshot=request.status_snapshot,
                owner_execution_id=request.owner_execution_id,
                owner_actor_id=request.owner_actor_id,
                owner_actor_role_id=request.owner_actor_role_id,
                receipt_ref=request.receipt_ref,
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
            goal=_goal_snapshot(
                goal_id=request.goal_id,
                tag="goal/sdk/activate",
                title="SDK activate",
                status="active",
            ),
        )


class _RecordingResolveGoalHomeViewClient:
    def __init__(self) -> None:
        self.requests: list[ResolveGoalHomeViewRequest] = []

    async def resolve_goal_home_view(
        self,
        request: ResolveGoalHomeViewRequest,
    ) -> ResolveGoalHomeViewResponse:
        self.requests.append(request)
        tag = request.tag or "goal/sdk/live-view"
        goal_id = request.goal_id or uuid4()
        return ResolveGoalHomeViewResponse(
            request_id=request.request_id,
            view_ref=GoalHomeViewStateV1.VIEW_REF,
            view_state={
                "goal_id": str(goal_id),
                "tag": tag,
                "title": "SDK live view",
                "status": "active",
                "priority": "high",
                "lanes": [
                    {
                        "goal_lane_id": str(uuid4()),
                        "lane_key": "workflow-agent-ux",
                        "owner_execution_id": (
                            "codex-019e86af-72bd-7880-8a18-79dc6cb9acbe"
                        ),
                        "status": "active",
                        "issues": [
                            {
                                "goal_lane_issue_id": str(uuid4()),
                                "row_key": "goal-service-view",
                                "row_number": 11,
                                "title": "Goal service resolves the board view live.",
                                "gate": "Goal service resolves the board view live.",
                                "tick": "active",
                                "status": "In Progress",
                                "status_token": "in_progress",
                            }
                        ],
                    }
                ],
                "provenance": {
                    "source_kind": "service_resolved",
                    "service_resolved": True,
                    "branch_id": str(request.branch_id),
                },
            },
            provenance={
                "source_kind": "service_resolved",
                "service_resolved": True,
            },
        )


class _RecordingResolveGoalContentExportClient:
    def __init__(self) -> None:
        self.requests: list[ResolveGoalContentExportRequest] = []

    async def resolve_goal_content_export(
        self,
        request: ResolveGoalContentExportRequest,
    ) -> ResolveGoalContentExportResponse:
        self.requests.append(request)
        tag = request.tag or "goal/sdk/content-export"
        goal_id = request.goal_id or uuid4()
        markdown = "# Goal: SDK content export\n\n## Lane Map\n"
        digest = "sha256:fixture"
        return ResolveGoalContentExportResponse(
            request_id=request.request_id,
            content_export=GoalContentExportDocumentV1(
                goal_id=goal_id,
                tag=tag,
                title="SDK content export",
                target_path=request.target_path,
                digest=digest,
                size_bytes=len(markdown.encode("utf-8")),
                content_text=markdown,
                parts=[
                    GoalContentExportPartV1(
                        part_key="goal_markdown",
                        text=markdown,
                        digest=digest,
                        size_bytes=len(markdown.encode("utf-8")),
                    )
                ],
                workspace_artifact=GoalWorkspaceArtifactProjectionV1(
                    artifact_key="goal_latest_markdown",
                    workspace_relative_path=request.target_path,
                    digest=digest,
                    size_bytes=len(markdown.encode("utf-8")),
                ),
                provenance={"source_kind": "service_resolved"},
            ),
            provenance={"source_kind": "service_resolved"},
        )


class _RecordingContentSdk:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def materialize_content_package(
        self,
        *,
        package_export,
        actor_id: UUID | None = None,
        branch_id: UUID | None = None,
    ) -> MaterializeContentPackageResponse:
        self.calls.append(
            {
                "package_export": package_export,
                "actor_id": actor_id,
                "branch_id": branch_id,
            }
        )
        return MaterializeContentPackageResponse(
            success=True,
            materialization=ContentPackageMaterializationResultV1(
                content_package_id=uuid4(),
                content_id=uuid4(),
                package_name=package_export.package_name,
                content_key=package_export.content_key,
                source_provider_key=package_export.source_provider_key,
                source_ref=package_export.source_ref,
                target_path=package_export.target_path,
                digest=package_export.digest,
                size_bytes=package_export.size_bytes,
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
    def __init__(self, *, ensure_response: EnsureGoalResponse | None = None) -> None:
        self.ensure_goal = _RecordingEnsureGoalClient(response=ensure_response)
        self.ensure_goal_lane = _RecordingEnsureGoalLaneClient()
        self.ensure_goal_lane_issue = _RecordingEnsureGoalLaneIssueClient()
        self.activate_goal = _RecordingActivateGoalClient()
        unsupported = _UnsupportedCapabilityClient()
        self.block_goal = unsupported
        self.park_goal = unsupported
        self.resume_goal = unsupported
        self.achieve_goal = unsupported
        self.supersede_goal = unsupported
        self.resolve_goal_home_view = _RecordingResolveGoalHomeViewClient()
        self.resolve_goal_content_export = _RecordingResolveGoalContentExportClient()


class _RecordingGeneratedGoalApiClient:
    def __init__(self, *, ensure_response: EnsureGoalResponse | None = None) -> None:
        self.goal = _RecordingGoalApiNamespace(ensure_response=ensure_response)


@pytest.mark.asyncio
async def test_goal_sdk_ensure_builds_generated_goal_request() -> None:
    api_client = _RecordingGeneratedGoalApiClient()
    sdk = GoalSdkClient(api_client=api_client)
    request_id = uuid4()
    branch_id = uuid4()
    overview_content_id = uuid4()
    definition_of_done_content_id = uuid4()
    evidence_chain_id = uuid4()

    handle = await sdk.ensure_goal(
        request_id=request_id,
        tag=" goal/sdk/ensure ",
        title=" SDK ensure ",
        priority_level_token=" high ",
        branch_id=branch_id,
        overview_content_id=overview_content_id,
        definition_of_done_content_id=definition_of_done_content_id,
        evidence_chain_id=evidence_chain_id,
    )

    request = api_client.goal.ensure_goal.requests[0]
    assert request.request_id == request_id
    assert request.tag == "goal/sdk/ensure"
    assert request.title == "SDK ensure"
    assert request.priority_level_token == "high"
    assert request.branch_id == branch_id
    assert request.overview_content_id == overview_content_id
    assert request.definition_of_done_content_id == definition_of_done_content_id
    assert request.evidence_chain_id == evidence_chain_id

    assert isinstance(handle, GoalHandle)
    assert handle.snapshot.tag == "goal/sdk/ensure"
    assert handle.snapshot.title == "SDK ensure"
    assert handle.snapshot.priority_level == "high"
    assert handle.snapshot.evidence_chain_id == evidence_chain_id


@pytest.mark.asyncio
async def test_goal_sdk_resolve_home_view_calls_generated_service_view() -> None:
    api_client = _RecordingGeneratedGoalApiClient()
    sdk = GoalSdkClient(api_client=api_client)
    request_id = uuid4()
    branch_id = uuid4()

    state = await sdk.resolve_goal_home_view(
        request_id=request_id,
        tag=" goal/sdk/live-view ",
        branch_id=branch_id,
    )

    request = api_client.goal.resolve_goal_home_view.requests[0]
    assert request.request_id == request_id
    assert request.tag == "goal/sdk/live-view"
    assert request.branch_id == branch_id
    assert isinstance(state, GoalHomeViewStateV1)
    assert state.title == "SDK live view"
    assert state.provenance["source_kind"] == "service_resolved"
    assert state.lanes[0].issues[0].status_token == "in_progress"


@pytest.mark.asyncio
async def test_goal_sdk_exports_goal_content_document_from_generated_api() -> None:
    api_client = _RecordingGeneratedGoalApiClient()
    sdk = GoalSdkClient(api_client=api_client)
    request_id = uuid4()
    branch_id = uuid4()

    content_export = await sdk.export_goal_content_document(
        request_id=request_id,
        tag=" goal/sdk/content-export ",
        target_path=" docs/goals/LATEST.md ",
        branch_id=branch_id,
    )

    request = api_client.goal.resolve_goal_content_export.requests[0]
    assert request.request_id == request_id
    assert request.tag == "goal/sdk/content-export"
    assert request.target_path == "docs/goals/LATEST.md"
    assert request.branch_id == branch_id
    assert isinstance(content_export, GoalContentExportDocumentV1)
    assert content_export.tag == "goal/sdk/content-export"
    assert content_export.content_text == "# Goal: SDK content export\n\n## Lane Map\n"
    assert content_export.parts[0].part_key == "goal_markdown"
    assert content_export.workspace_artifact is not None
    assert (
        content_export.workspace_artifact.workspace_relative_path
        == "docs/goals/LATEST.md"
    )


def test_goal_content_export_maps_to_generic_content_package_export() -> None:
    goal_id = uuid4()
    markdown = "# Goal\n"
    content_export = GoalContentExportDocumentV1(
        goal_id=goal_id,
        tag="goal/sdk/content-export",
        title="SDK content export",
        target_path="docs/goals/LATEST.md",
        media_type="text/markdown",
        digest="sha256:fixture",
        size_bytes=len(markdown.encode("utf-8")),
        content_text=markdown,
        parts=[
            GoalContentExportPartV1(
                part_key="goal_markdown",
                text=markdown,
                digest="sha256:fixture",
                size_bytes=len(markdown.encode("utf-8")),
            )
        ],
        workspace_artifact=GoalWorkspaceArtifactProjectionV1(
            artifact_key="goal_latest_markdown",
            workspace_relative_path="docs/goals/LATEST.md",
            digest="sha256:fixture",
            size_bytes=len(markdown.encode("utf-8")),
        ),
        aware_content_mapping={"content": "Content"},
        provenance={"source_kind": "service_resolved"},
    )

    package_export = goal_content_export_to_content_package_export(content_export)

    assert package_export.package_name == "aware_goal/goal/sdk/content-export/latest"
    assert package_export.package_kind == "coordination_content"
    assert package_export.source_provider_key == "aware_goal"
    assert package_export.source_ref == "goal:goal/sdk/content-export"
    assert package_export.content_text == markdown
    assert package_export.parts[0].position == 0
    assert package_export.artifact is not None
    assert package_export.artifact.output_key == "goal_content"
    assert package_export.artifact.relative_path == "docs/goals/LATEST.md"
    assert package_export.provider_payload["goal_id"] == str(goal_id)
    assert package_export.aware_content_mapping["content"] == "Content"


@pytest.mark.asyncio
async def test_goal_sdk_materializes_goal_export_through_content_sdk() -> None:
    api_client = _RecordingGeneratedGoalApiClient()
    sdk = GoalSdkClient(api_client=api_client)
    content_sdk = cast(ContentPackageMaterializer, _RecordingContentSdk())
    request_id = uuid4()
    actor_id = uuid4()
    branch_id = uuid4()

    response = await sdk.materialize_goal_content_package(
        content_sdk=content_sdk,
        tag=" goal/sdk/content-export ",
        package_name="aware_goal/current",
        target_path=" docs/goals/LATEST.md ",
        actor_id=actor_id,
        branch_id=branch_id,
        request_id=request_id,
    )

    assert response.materialization is not None
    assert response.materialization.package_name == "aware_goal/current"
    request = api_client.goal.resolve_goal_content_export.requests[0]
    assert request.request_id == request_id
    assert request.tag == "goal/sdk/content-export"
    assert request.branch_id == branch_id
    recording_content_sdk = cast(_RecordingContentSdk, content_sdk)
    package_call = recording_content_sdk.calls[0]
    package_export = package_call["package_export"]
    assert package_call["actor_id"] == actor_id
    assert package_call["branch_id"] == branch_id
    assert package_export.package_name == "aware_goal/current"
    assert package_export.source_provider_key == "aware_goal"
    assert package_export.target_path == "docs/goals/LATEST.md"


@pytest.mark.asyncio
async def test_goal_sdk_ensure_goal_lane_builds_generated_request() -> None:
    api_client = _RecordingGeneratedGoalApiClient()
    sdk = GoalSdkClient(api_client=api_client)
    request_id = uuid4()
    goal_id = uuid4()
    branch_id = uuid4()
    actor_id = uuid4()
    actor_role_id = uuid4()
    issue_id = uuid4()

    handle = await sdk.ensure_goal_lane(
        request_id=request_id,
        goal_id=goal_id,
        lane_key=" Goal-Ontology-Service-SDK ",
        role_key=" Implementation ",
        role_label=" Goal ontology service SDK ",
        owner_execution_id=" codex-019e86af-72bd-7880-8a18-79dc6cb9acbe ",
        owner_actor_id=actor_id,
        owner_actor_role_id=actor_role_id,
        status_token=" active ",
        current_issue_id=issue_id,
        current_issue_tag=" fb/2026-06-03/goal-sdk-lane-surface-v0 ",
        since_snapshot=" 2026-06-03T08:40Z ",
        last_receipt_ref=" docs/issues/2026/06/03/fb-2026-06-03-goal-sdk-lane-surface-v0.md ",
        scope=" Goal SDK lane surface ",
        branch_id=branch_id,
    )

    request = api_client.goal.ensure_goal_lane.requests[0]
    assert request.request_id == request_id
    assert request.goal_id == goal_id
    assert request.lane_key == "Goal-Ontology-Service-SDK"
    assert request.role_key == "Implementation"
    assert request.role_label == "Goal ontology service SDK"
    assert request.owner_execution_id == "codex-019e86af-72bd-7880-8a18-79dc6cb9acbe"
    assert request.owner_actor_id == actor_id
    assert request.owner_actor_role_id == actor_role_id
    assert request.status_token == "active"
    assert request.current_issue_id == issue_id
    assert request.current_issue_tag == "fb/2026-06-03/goal-sdk-lane-surface-v0"
    assert request.since_snapshot == "2026-06-03T08:40Z"
    assert request.last_receipt_ref == (
        "docs/issues/2026/06/03/fb-2026-06-03-goal-sdk-lane-surface-v0.md"
    )
    assert request.scope == "Goal SDK lane surface"
    assert request.branch_id == branch_id

    assert isinstance(handle, GoalLaneHandle)
    assert handle.goal_id == goal_id
    assert handle.lane_key == "Goal-Ontology-Service-SDK"
    assert handle.status == "active"


@pytest.mark.asyncio
async def test_goal_sdk_ensure_goal_lane_issue_builds_generated_request() -> None:
    api_client = _RecordingGeneratedGoalApiClient()
    sdk = GoalSdkClient(api_client=api_client)
    request_id = uuid4()
    goal_id = uuid4()
    goal_lane_id = uuid4()
    branch_id = uuid4()
    issue_id = uuid4()
    actor_id = uuid4()
    actor_role_id = uuid4()

    handle = await sdk.ensure_goal_lane_issue(
        request_id=request_id,
        goal_id=goal_id,
        goal_lane_id=goal_lane_id,
        row_key=" P0-SDK-Local-Host ",
        gate=" P0 ",
        row_number=6,
        sync_time_snapshot=" 2026-06-03T08:41Z ",
        issue_id=issue_id,
        planned_issue_tag=" fb/2026-06-03/goal-sdk-lane-surface-v0 ",
        tick_token=" active ",
        status_snapshot=" In Progress ",
        owner_execution_id=" codex-019e86af-72bd-7880-8a18-79dc6cb9acbe ",
        owner_actor_id=actor_id,
        owner_actor_role_id=actor_role_id,
        receipt_ref=" docs/issues/2026/06/03/fb-2026-06-03-goal-sdk-lane-surface-v0.md ",
        branch_id=branch_id,
    )

    request = api_client.goal.ensure_goal_lane_issue.requests[0]
    assert request.request_id == request_id
    assert request.goal_id == goal_id
    assert request.goal_lane_id == goal_lane_id
    assert request.row_key == "P0-SDK-Local-Host"
    assert request.gate == "P0"
    assert request.row_number == 6
    assert request.sync_time_snapshot == "2026-06-03T08:41Z"
    assert request.issue_id == issue_id
    assert request.planned_issue_tag == "fb/2026-06-03/goal-sdk-lane-surface-v0"
    assert request.tick_token == "active"
    assert request.status_snapshot == "In Progress"
    assert request.owner_execution_id == "codex-019e86af-72bd-7880-8a18-79dc6cb9acbe"
    assert request.owner_actor_id == actor_id
    assert request.owner_actor_role_id == actor_role_id
    assert request.receipt_ref == (
        "docs/issues/2026/06/03/fb-2026-06-03-goal-sdk-lane-surface-v0.md"
    )
    assert request.branch_id == branch_id

    assert isinstance(handle, GoalLaneIssueHandle)
    assert handle.goal_id == goal_id
    assert handle.goal_lane_id == goal_lane_id
    assert handle.row_key == "P0-SDK-Local-Host"
    assert handle.tick == "active"


@pytest.mark.asyncio
async def test_goal_handle_lifecycle_uses_generated_activate_endpoint() -> None:
    api_client = _RecordingGeneratedGoalApiClient()
    sdk = GoalSdkClient(api_client=api_client)
    goal_id = uuid4()
    branch_id = uuid4()
    request_id = uuid4()
    handle = GoalHandle(
        client=sdk,
        snapshot=_goal_snapshot(goal_id=goal_id, status="proposed"),
    )

    updated = await handle.activate(branch_id=branch_id, request_id=request_id)

    request = api_client.goal.activate_goal.requests[0]
    assert request.request_id == request_id
    assert request.goal_id == goal_id
    assert request.branch_id == branch_id
    assert updated.goal_id == goal_id
    assert updated.status == "active"


@pytest.mark.asyncio
async def test_goal_handle_ensure_lane_uses_generated_goal_lane_endpoint() -> None:
    api_client = _RecordingGeneratedGoalApiClient()
    sdk = GoalSdkClient(api_client=api_client)
    goal_id = uuid4()
    handle = GoalHandle(
        client=sdk,
        snapshot=_goal_snapshot(goal_id=goal_id, status="active"),
    )

    lane = await handle.ensure_lane(
        lane_key="goal-ontology-service-sdk",
        current_issue_tag="fb/2026-06-03/goal-sdk-lane-surface-v0",
    )

    request = api_client.goal.ensure_goal_lane.requests[0]
    assert request.goal_id == goal_id
    assert request.lane_key == "goal-ontology-service-sdk"
    assert lane.goal_id == goal_id
    assert lane.snapshot.current_issue_tag == ("fb/2026-06-03/goal-sdk-lane-surface-v0")


@pytest.mark.asyncio
async def test_goal_lane_handle_ensure_issue_uses_generated_lane_issue_endpoint() -> (
    None
):
    api_client = _RecordingGeneratedGoalApiClient()
    sdk = GoalSdkClient(api_client=api_client)
    goal_id = uuid4()
    goal_lane_id = uuid4()
    handle = GoalLaneHandle(
        client=sdk,
        snapshot=_goal_lane_snapshot(
            goal_id=goal_id,
            goal_lane_id=goal_lane_id,
            lane_key="goal-ontology-service-sdk",
            status="active",
        ),
    )

    row = await handle.ensure_issue(
        row_key="sdk-local-host",
        gate="P0",
        planned_issue_tag="fb/2026-06-03/goal-sdk-lane-surface-v0",
    )

    request = api_client.goal.ensure_goal_lane_issue.requests[0]
    assert request.goal_id == goal_id
    assert request.goal_lane_id == goal_lane_id
    assert request.row_key == "sdk-local-host"
    assert request.gate == "P0"
    assert row.goal_id == goal_id
    assert row.goal_lane_id == goal_lane_id
    assert row.snapshot.planned_issue_tag == "fb/2026-06-03/goal-sdk-lane-surface-v0"


@pytest.mark.asyncio
async def test_goal_sdk_surfaces_generated_failure_response() -> None:
    api_client = _RecordingGeneratedGoalApiClient(
        ensure_response=cast(
            EnsureGoalResponse,
            GoalServiceResponse(
                operation="ensure_goal",
                success=False,
                error="goal service unavailable",
            ),
        )
    )
    sdk = GoalSdkClient(api_client=api_client)

    with pytest.raises(GoalSdkError, match="goal service unavailable"):
        await sdk.ensure_goal(tag="goal/sdk/fail", title="Fail")


@pytest.mark.asyncio
async def test_goal_sdk_rejects_empty_tag_before_api_call() -> None:
    api_client = _RecordingGeneratedGoalApiClient()
    sdk = GoalSdkClient(api_client=api_client)

    with pytest.raises(GoalSdkError, match="tag"):
        await sdk.ensure_goal(tag=" ", title="No tag")

    assert api_client.goal.ensure_goal.requests == []


@pytest.mark.asyncio
async def test_goal_sdk_rejects_empty_goal_lane_before_api_call() -> None:
    api_client = _RecordingGeneratedGoalApiClient()
    sdk = GoalSdkClient(api_client=api_client)

    with pytest.raises(GoalSdkError, match="lane_key"):
        await sdk.ensure_goal_lane(goal_id=uuid4(), lane_key=" ")

    assert api_client.goal.ensure_goal_lane.requests == []


@pytest.mark.asyncio
async def test_goal_sdk_rejects_empty_goal_lane_issue_before_api_call() -> None:
    api_client = _RecordingGeneratedGoalApiClient()
    sdk = GoalSdkClient(api_client=api_client)
    goal_id = uuid4()
    goal_lane_id = uuid4()

    with pytest.raises(GoalSdkError, match="row_key"):
        await sdk.ensure_goal_lane_issue(
            goal_id=goal_id,
            goal_lane_id=goal_lane_id,
            row_key=" ",
            gate="P0",
        )

    with pytest.raises(GoalSdkError, match="gate"):
        await sdk.ensure_goal_lane_issue(
            goal_id=goal_id,
            goal_lane_id=goal_lane_id,
            row_key="p0",
            gate=" ",
        )

    assert api_client.goal.ensure_goal_lane_issue.requests == []


def test_goal_sdk_manifest_compiles_to_expected_operations() -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace  # noqa: WPS433

    result = compile_sdk_workspace(
        toml_path=GOAL_SDK_TOML,
        repo_root=REPO_ROOT,
    )

    assert result.compile_plan is not None
    assert result.compile_plan.package_name == "goal-sdk"
    assert result.compile_plan.fqn_prefix == "aware_goal_sdk"
    assert result.compile_plan.source_files == (
        "goal_contracts.aware",
        "goal_sdk.aware",
    )

    sdk_config = result.compile_plan.sdk_configs[0]
    assert sdk_config.name == "goal_sdk"
    assert sdk_config.apis[0].api_ref == "goal"
    operations = {operation.name: operation for operation in sdk_config.operations}
    assert set(operations) == {
        "achieve_goal",
        "activate_goal",
        "block_goal",
        "ensure_goal",
        "ensure_goal_lane",
        "ensure_goal_lane_issue",
        "issue_goal_pursuit",
        "observe_phase_eligibility",
        "observe_phase_direction",
        "park_goal",
        "resolve_goal_home_view",
        "resume_goal",
        "supersede_goal",
        "verify_goal_pursuit_currentness",
        "verify_phase_direction_currentness",
    }
    assert operations["ensure_goal"].api_endpoints[0].endpoint_ref == (
        "goal.ensure_goal.ensure_goal"
    )
    assert operations["ensure_goal_lane"].api_endpoints[0].endpoint_ref == (
        "goal.ensure_goal_lane.ensure_goal_lane"
    )
    assert operations["ensure_goal_lane_issue"].api_endpoints[0].endpoint_ref == (
        "goal.ensure_goal_lane_issue.ensure_goal_lane_issue"
    )
    assert operations["achieve_goal"].api_endpoints[0].endpoint_ref == (
        "goal.achieve_goal.achieve_goal"
    )
    assert operations["resolve_goal_home_view"].api_endpoints[0].endpoint_ref == (
        "goal.resolve_goal_home_view.resolve_goal_home_view"
    )
    assert operations["issue_goal_pursuit"].provider_operation_ref == (
        "workflow.goal.pursuit.issue"
    )
    assert operations["issue_goal_pursuit"].request_type_ref == (
        "aware_goal_sdk.GoalPursuitIssueRequest"
    )
    assert operations["issue_goal_pursuit"].result_type_ref == (
        "aware_goal_sdk.GoalPursuitIssueResult"
    )
    assert operations["issue_goal_pursuit"].error_type_refs == (
        "aware_goal_sdk.GoalPursuitIssueError",
    )
    assert operations["issue_goal_pursuit"].api_endpoints == ()
    assert operations["verify_goal_pursuit_currentness"].provider_operation_ref == (
        "workflow.goal.pursuit.currentness.verify"
    )
    assert operations["verify_goal_pursuit_currentness"].request_type_ref == (
        "aware_goal_sdk.GoalPursuitCurrentnessVerifyRequest"
    )
    assert operations["verify_goal_pursuit_currentness"].result_type_ref == (
        "aware_goal_sdk.GoalPursuitCurrentnessVerifyResult"
    )
    assert operations["verify_goal_pursuit_currentness"].error_type_refs == (
        "aware_goal_sdk.GoalPursuitCurrentnessVerifyError",
    )
    assert operations["verify_goal_pursuit_currentness"].api_endpoints == ()
    assert operations["observe_phase_eligibility"].provider_operation_ref == (
        "workflow.goal.phase.eligibility.observe"
    )
    assert operations["observe_phase_eligibility"].request_type_ref == (
        "aware_goal_sdk.phase_operation.GoalPhaseObserveEligibilityRequestV1"
    )
    assert operations["observe_phase_eligibility"].result_type_ref == (
        "aware_goal_sdk.phase_operation.GoalPhaseObserveEligibilityResultV1"
    )
    assert operations["observe_phase_eligibility"].error_type_refs == (
        "aware_goal_sdk.phase_operation.GoalPhaseObserveEligibilityError",
    )
    assert operations["observe_phase_eligibility"].api_endpoints == ()
    assert operations["observe_phase_direction"].provider_operation_ref == (
        "workflow.goal.phase.direction.observe"
    )
    assert operations["observe_phase_direction"].request_type_ref == (
        "aware_goal_sdk.phase_direction.GoalPhaseDirectionObserveRequestV1"
    )
    assert operations["observe_phase_direction"].result_type_ref == (
        "aware_goal_sdk.phase_direction.GoalPhaseDirectionReceiptV1"
    )
    assert operations["observe_phase_direction"].error_type_refs == (
        "aware_goal_sdk.phase_direction.GoalPhaseDirectionError",
    )
    assert operations["observe_phase_direction"].api_endpoints == ()
    assert operations["verify_phase_direction_currentness"].provider_operation_ref == (
        "workflow.goal.phase.direction.currentness.verify"
    )
    assert operations["verify_phase_direction_currentness"].request_type_ref == (
        "aware_goal_sdk.phase_direction.GoalPhaseDirectionCurrentnessRequestV1"
    )
    assert operations["verify_phase_direction_currentness"].result_type_ref == (
        "aware_goal_sdk.phase_direction.GoalPhaseDirectionCurrentnessV1"
    )
    assert operations["verify_phase_direction_currentness"].error_type_refs == (
        "aware_goal_sdk.phase_direction.GoalPhaseDirectionError",
    )
    assert operations["verify_phase_direction_currentness"].api_endpoints == ()

    observation = next(
        surface for surface in sdk_config.surfaces if surface.name == "observation"
    )
    methods = {method.name: method for method in observation.methods}
    for method_name in (
        "issue_pursuit", "verify_pursuit_currentness", "observe_phase_eligibility",
        "observe_phase_direction", "verify_phase_direction_currentness",
    ):
        method = methods[method_name]
        assert method.effect == "read"
        assert method.mutation_scope == "none"
        assert method.runtime_binding_kind == "provider"
        if method_name in {
            "observe_phase_direction", "verify_phase_direction_currentness"
        }:
            assert method.confirmation_policy == "none"
            assert method.execution_mode == "request_response"


def test_goal_sdk_does_not_import_protocol_service_or_runtime_internals() -> None:
    source = (Path(__file__).parents[2] / "service_view_compat" / "aware_goal_service_view_compat" / "client.py").read_text(
        encoding="utf-8"
    )

    forbidden_imports = (
        "aware_goal_service_protocol",
        "from aware_goal_service ",
        "from aware_goal_service.",
        "import aware_goal_service\n",
        "from aware_runtime",
        "import aware_runtime",
        "graph_gateway",
        "runtime_index",
    )
    for forbidden in forbidden_imports:
        assert forbidden not in source


def _goal_snapshot(
    *,
    goal_id: UUID | None = None,
    tag: str = "goal/sdk/test",
    title: str = "SDK Goal",
    status: str = "proposed",
    priority_level: str = "medium",
    overview_content_id: UUID | None = None,
    definition_of_done_content_id: UUID | None = None,
    evidence_chain_id: UUID | None = None,
) -> GoalSnapshot:
    return GoalSnapshot(
        goal_id=goal_id or uuid4(),
        tag=tag,
        title=title,
        status=status,
        priority_level=priority_level,
        overview_content_id=overview_content_id,
        definition_of_done_content_id=definition_of_done_content_id,
        evidence_chain_id=evidence_chain_id,
    )


def _goal_lane_snapshot(
    *,
    goal_id: UUID,
    goal_lane_id: UUID | None = None,
    lane_key: str = "goal-ontology-service-sdk",
    role_key: str | None = None,
    role_label: str | None = None,
    owner_execution_id: str | None = None,
    owner_actor_id: UUID | None = None,
    owner_actor_role_id: UUID | None = None,
    status: str = "planned",
    current_issue_id: UUID | None = None,
    current_issue_tag: str | None = None,
    since_snapshot: str | None = None,
    last_receipt_ref: str | None = None,
    scope: str | None = None,
) -> GoalLaneSnapshot:
    return GoalLaneSnapshot(
        goal_id=goal_id,
        goal_lane_id=goal_lane_id or uuid4(),
        lane_key=lane_key,
        role_key=role_key,
        role_label=role_label,
        owner_execution_id=owner_execution_id,
        owner_actor_id=owner_actor_id,
        owner_actor_role_id=owner_actor_role_id,
        status=status,
        current_issue_id=current_issue_id,
        current_issue_tag=current_issue_tag,
        since_snapshot=since_snapshot,
        last_receipt_ref=last_receipt_ref,
        scope=scope,
    )


def _goal_lane_issue_snapshot(
    *,
    goal_id: UUID,
    goal_lane_id: UUID,
    goal_lane_issue_id: UUID | None = None,
    row_key: str = "p0-sdk",
    gate: str = "P0",
    row_number: int = 0,
    sync_time_snapshot: str | None = None,
    issue_id: UUID | None = None,
    planned_issue_tag: str | None = None,
    tick: str = "planned",
    status_snapshot: str = "Planned",
    owner_execution_id: str | None = None,
    owner_actor_id: UUID | None = None,
    owner_actor_role_id: UUID | None = None,
    receipt_ref: str | None = None,
) -> GoalLaneIssueSnapshot:
    return GoalLaneIssueSnapshot(
        goal_id=goal_id,
        goal_lane_id=goal_lane_id,
        goal_lane_issue_id=goal_lane_issue_id or uuid4(),
        row_key=row_key,
        row_number=row_number,
        sync_time_snapshot=sync_time_snapshot,
        gate=gate,
        issue_id=issue_id,
        planned_issue_tag=planned_issue_tag,
        tick=tick,
        status_snapshot=status_snapshot,
        owner_execution_id=owner_execution_id,
        owner_actor_id=owner_actor_id,
        owner_actor_role_id=owner_actor_role_id,
        receipt_ref=receipt_ref,
    )


def _phase_direction_test_ref(body: dict[str, object], domain: str) -> str:
    encoded = json.dumps(
        body, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return f"{domain}:sha256:" + hashlib.sha256(encoded).hexdigest()


def _phase_direction_test_receipt() -> dict[str, object]:
    body: dict[str, object] = {
        "schema_id": "aware.goal.phase-pursuit.v1",
        "effect_profile": "direction_only_non_authorizing",
        "coordinate": {
            "goal_tag": "goal/2026-09-27/client-proof",
            "lane_key": "runtime",
            "phase_key": "first",
        },
        "ordinal": 1,
        "definition_ref": "goal-phase-definition:sha256:" + "1" * 64,
        "gate_digest": "sha256:" + "2" * 64,
        "document_ref": "goal-phase-document:sha256:" + "3" * 64,
        "compatibility_profile": "phase_native_v2",
        "source": {
            "repository_revision_ref": "a" * 40,
            "goal_sha256": "sha256:" + "4" * 64,
            "goal_blob_oid": "b" * 40,
        },
    }
    return {**body, "pursuit_ref": _phase_direction_test_ref(body, "goal-phase-pursuit")}


def _phase_direction_test_currentness(receipt: dict[str, object]) -> dict[str, object]:
    source = receipt["source"]
    assert isinstance(source, dict)
    revision = source["repository_revision_ref"]
    lineage: dict[str, object] = {
        "schema_id": "aware.goal.phase-revision-lineage.v1",
        "authority_profile": "repository_revision_lineage_v1",
        "expected_revision_ref": revision,
        "observed_revision_ref": revision,
        "relation": "equal",
    }
    body: dict[str, object] = {
        "schema_id": "aware.goal.phase-pursuit-currentness.v1",
        "effect_profile": "read_only_non_authorizing",
        "expected_pursuit_ref": receipt["pursuit_ref"],
        "observed_pursuit_ref": receipt["pursuit_ref"],
        "status": "current",
        "projection_currentness": "current",
        "replay_disposition": "exact",
        "reasons": [],
        "expected_document_ref": receipt["document_ref"],
        "observed_document_ref": receipt["document_ref"],
        "expected_source_revision_ref": revision,
        "observed_source_revision_ref": revision,
        "source_revision_lineage": "equal",
        "source_revision_lineage_ref": _phase_direction_test_ref(
            lineage, "goal-phase-revision-lineage"
        ),
    }
    return {
        **body,
        "currentness_ref": _phase_direction_test_ref(body, "goal-phase-pursuit-currentness"),
    }


class _FakePhaseDirectionProvider:
    def __init__(self, receipt: dict[str, object], currentness: dict[str, object]) -> None:
        self.receipt = receipt
        self.currentness = currentness

    def observe_phase_direction(
        self, request: GoalPhaseDirectionObserveRequestV1
    ) -> dict[str, object]:
        del request
        return deepcopy(self.receipt)

    def verify_phase_direction_currentness(
        self, request: GoalPhaseDirectionCurrentnessRequestV1
    ) -> dict[str, object]:
        del request
        return deepcopy(self.currentness)


class _FakeStringSubclass(str):
    pass


def _phase_direction_test_request() -> GoalPhaseDirectionObserveRequestV1:
    return GoalPhaseDirectionObserveRequestV1(
        goal_path="customer/objectives/2026/09/27/goal-2026-09-27-client-proof.md",
        goal_tag="goal/2026-09-27/client-proof",
        lane_key="runtime",
        phase_key="first",
    )


def test_phase_direction_fake_provider_valid_wire_round_trip() -> None:
    receipt = _phase_direction_test_receipt()
    currentness = _phase_direction_test_currentness(receipt)
    client = GoalPhaseDirectionClient(_FakePhaseDirectionProvider(receipt, currentness))
    assert client.observe_phase_direction(_phase_direction_test_request()) == receipt
    assert client.verify_phase_direction_currentness(
        GoalPhaseDirectionCurrentnessRequestV1(
            _phase_direction_test_request().goal_path, receipt
        )
    ) == currentness


def test_phase_direction_fake_provider_cannot_mutate_request_binding() -> None:
    receipt = _phase_direction_test_receipt()
    currentness = _phase_direction_test_currentness(receipt)

    class _MutatingProvider(_FakePhaseDirectionProvider):
        def observe_phase_direction(
            self, request: GoalPhaseDirectionObserveRequestV1
        ) -> dict[str, object]:
            object.__setattr__(request, "phase_key", "substituted")
            changed = deepcopy(self.receipt)
            coordinate = changed["coordinate"]
            assert isinstance(coordinate, dict)
            coordinate["phase_key"] = "substituted"
            body = {key: item for key, item in changed.items() if key != "pursuit_ref"}
            changed["pursuit_ref"] = _phase_direction_test_ref(body, "goal-phase-pursuit")
            return changed

        def verify_phase_direction_currentness(
            self, request: GoalPhaseDirectionCurrentnessRequestV1
        ) -> dict[str, object]:
            supplied = request.expected_receipt
            assert isinstance(supplied, dict)
            supplied["pursuit_ref"] = "goal-phase-pursuit:sha256:" + "f" * 64
            changed = deepcopy(self.currentness)
            changed["expected_pursuit_ref"] = supplied["pursuit_ref"]
            body = {key: item for key, item in changed.items() if key != "currentness_ref"}
            changed["currentness_ref"] = _phase_direction_test_ref(
                body, "goal-phase-pursuit-currentness"
            )
            return changed

    client = GoalPhaseDirectionClient(_MutatingProvider(receipt, currentness))
    with pytest.raises(GoalPhaseDirectionError):
        client.observe_phase_direction(_phase_direction_test_request())
    with pytest.raises(GoalPhaseDirectionError):
        client.verify_phase_direction_currentness(
            GoalPhaseDirectionCurrentnessRequestV1(
                _phase_direction_test_request().goal_path, deepcopy(receipt)
            )
        )


@pytest.mark.parametrize(
    "fault",
    ["ordinal_bool", "gate_null", "source_digest", "source_revision",
     "source_blob", "nested_extra", "invalid_reference", "schema_subclass"],
)
def test_phase_direction_fake_provider_rejects_malformed_receipt(fault: str) -> None:
    receipt = _phase_direction_test_receipt()
    currentness = _phase_direction_test_currentness(receipt)
    if fault == "ordinal_bool":
        receipt["ordinal"] = True
    elif fault == "gate_null":
        receipt["gate_digest"] = None
    elif fault in {"source_digest", "source_revision", "source_blob", "nested_extra"}:
        source = receipt["source"]
        assert isinstance(source, dict)
        source[{
            "source_digest": "goal_sha256",
            "source_revision": "repository_revision_ref",
            "source_blob": "goal_blob_oid",
            "nested_extra": "invented",
        }[fault]] = "invalid"
    elif fault == "invalid_reference":
        receipt["pursuit_ref"] = "goal-phase-pursuit:sha256:" + "0" * 64
    elif fault == "schema_subclass":
        receipt["schema_id"] = _FakeStringSubclass("aware.goal.phase-pursuit.v1")
    if fault != "invalid_reference":
        body = {key: item for key, item in receipt.items() if key != "pursuit_ref"}
        receipt["pursuit_ref"] = _phase_direction_test_ref(body, "goal-phase-pursuit")
    client = GoalPhaseDirectionClient(_FakePhaseDirectionProvider(receipt, currentness))
    with pytest.raises(GoalPhaseDirectionError):
        client.observe_phase_direction(_phase_direction_test_request())


@pytest.mark.parametrize(
    "fault",
    ["contradictory_projection", "contradictory_replay", "current_with_reason",
     "invalid_reference", "invalid_lineage_reference", "foreign_document",
     "observed_bool", "document_reason_mismatch", "reasons_bool",
     "expected_ref_subclass"],
)
def test_phase_direction_fake_provider_rejects_contradictory_currentness(
    fault: str,
) -> None:
    receipt = _phase_direction_test_receipt()
    currentness = _phase_direction_test_currentness(receipt)
    if fault == "contradictory_projection":
        currentness["projection_currentness"] = "stale"
        currentness["replay_disposition"] = "refuse"
    elif fault == "contradictory_replay":
        currentness["replay_disposition"] = "refuse"
    elif fault == "current_with_reason":
        currentness["reasons"] = ["document_advanced"]
    elif fault == "invalid_reference":
        currentness["currentness_ref"] = "goal-phase-pursuit-currentness:sha256:" + "0" * 64
    elif fault == "invalid_lineage_reference":
        currentness["source_revision_lineage_ref"] = "goal-phase-revision-lineage:sha256:" + "0" * 64
    elif fault == "foreign_document":
        currentness["expected_document_ref"] = "goal-phase-document:sha256:" + "f" * 64
    elif fault == "observed_bool":
        currentness["observed_pursuit_ref"] = True
    elif fault == "document_reason_mismatch":
        currentness["observed_document_ref"] = "goal-phase-document:sha256:" + "e" * 64
    elif fault == "reasons_bool":
        currentness["reasons"] = [True]
    elif fault == "expected_ref_subclass":
        currentness["expected_pursuit_ref"] = _FakeStringSubclass(
            str(receipt["pursuit_ref"])
        )
    if fault != "invalid_reference":
        body = {key: item for key, item in currentness.items() if key != "currentness_ref"}
        currentness["currentness_ref"] = _phase_direction_test_ref(
            body, "goal-phase-pursuit-currentness"
        )
    client = GoalPhaseDirectionClient(_FakePhaseDirectionProvider(receipt, currentness))
    with pytest.raises(GoalPhaseDirectionError):
        client.verify_phase_direction_currentness(
            GoalPhaseDirectionCurrentnessRequestV1(
                _phase_direction_test_request().goal_path, receipt
            )
        )
