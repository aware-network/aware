from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from aware_environment_sdk import view_state_providers
from aware_environment_sdk import (
    EnvironmentViewsV1ProviderInput,
    ViewProviderProvenanceV1,
    environment_navigator_view_state,
    environment_navigator_view_state_from_input,
    environment_views_v1_provider_input,
    environment_views_v1_provider_input_from_api,
    process_workspace_view_state,
    thread_layout_view_state,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentRequest,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentResponse,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentStatusRequest,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentStatusResponse,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyAttachment,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyLane,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyLayout,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyProcess,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyRequest,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyResponse,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologySection,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyThread,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentStatusAuthority,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentStatusAuthorityKind,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentStatusBlock,
)
from aware_environment_service_dto.environment.view import (
    EnvironmentNavigatorViewStateV1,
    ProcessWorkspaceViewStateV1,
    ThreadLayoutViewStateV1,
)


def test_environment_model_rebuild_namespace_covers_nested_api_forward_refs() -> None:
    namespace = view_state_providers._ENVIRONMENT_MODEL_TYPES_NAMESPACE

    assert (
        namespace["DescribeEnvironmentTopologyLayout"].__name__
        == "DescribeEnvironmentTopologyLayout"
    )
    assert (
        namespace["DescribeEnvironmentTopologyThread"].__name__
        == "DescribeEnvironmentTopologyThread"
    )


def test_environment_navigator_provider_resolves_topology_selection() -> None:
    env_id = uuid4()
    provider_input = _provider_input(env_id=env_id, selected_thread_key="main")

    state = environment_navigator_view_state_from_input(provider_input)

    assert isinstance(state, EnvironmentNavigatorViewStateV1)
    assert state.environment_id == env_id
    assert state.title == "Kernel Environment"
    assert state.status == "materialized"
    assert state.ready is True
    assert state.selected_process_key == "control"
    assert state.selected_thread_key == "main"
    assert state.processes[0].is_selected is True
    assert state.processes[0].threads[0].attachment_count == 1
    assert state.status_blocks[0].authority_kind == "commit_truth"
    assert state.provenance["projection_view_key"] == "environment.navigator.v1"
    assert state.provenance["process_count"] == 1
    assert (
        state.model_dump(mode="json")["processes"][0]["threads"][0]["thread_key"]
        == "main"
    )


def test_process_workspace_provider_resolves_selected_process_threads() -> None:
    provider_input = _provider_input(selected_thread_key="main")

    state = process_workspace_view_state(provider_input=provider_input)

    assert isinstance(state, ProcessWorkspaceViewStateV1)
    assert state.status == "materialized"
    assert state.process_key == "control"
    assert state.selected_thread_key == "main"
    assert state.threads[0].lane_count == 1
    assert state.threads[0].active_attachment_count == 1
    assert state.threads[0].layout_count == 1
    assert state.provenance["projection_view_key"] == "process.workspace.v1"


def test_thread_layout_provider_resolves_lane_attachments() -> None:
    provider_input = _provider_input(selected_thread_key="main")

    state = thread_layout_view_state(provider_input=provider_input)

    assert isinstance(state, ThreadLayoutViewStateV1)
    assert state.status == "materialized"
    assert state.thread_key == "main"
    assert state.active_layout_key == "coordination"
    assert state.layouts[0].layout_key == "coordination"
    assert state.layouts[0].sections[0].section_key == "conversation"
    assert state.sections[0].section_key == "conversation"
    assert state.sections[0].view_ref == "aware_conversations.chat.home.v1"
    assert state.sections[0].view_key == "chat.home.v1"
    assert state.sections[0].package_name == "aware_conversations"
    assert state.attachments[0].title == "Conversation lane"
    assert state.attachments[0].lanes[0].opg_name == "conversation"
    assert state.provenance["layout_source"] == "environment_topology"


def test_environment_provider_input_resolver_uses_host_context() -> None:
    env_id = uuid4()
    provider_context = SimpleNamespace(
        environment_description=lambda: _description(env_id=env_id),
        environment_status=lambda: _status(env_id=env_id),
        environment_topology=lambda: _topology(env_id=env_id),
        selected_process_key="control",
        selected_thread_key="main",
        provenance={"source_kind": "interface_host", "environment_id": str(env_id)},
    )

    provider_input = environment_views_v1_provider_input(provider_context)
    state = environment_navigator_view_state(provider_input=provider_input)

    assert provider_input.topology is not None
    assert state.environment_id == env_id
    assert state.provenance["source_kind"] == "interface_host"


def test_environment_providers_expose_input_resolver() -> None:
    assert (
        getattr(environment_navigator_view_state, "provider_input_resolver")
        is environment_views_v1_provider_input
    )
    assert (
        getattr(process_workspace_view_state, "provider_input_resolver")
        is environment_views_v1_provider_input
    )
    assert (
        getattr(thread_layout_view_state, "provider_input_resolver")
        is environment_views_v1_provider_input
    )


@pytest.mark.asyncio
async def test_environment_provider_input_from_api_uses_generated_client() -> None:
    env_id = uuid4()
    api_client = _RecordingGeneratedApiClient(env_id=env_id)

    provider_input = await environment_views_v1_provider_input_from_api(
        api_client=api_client,
        environment_id=env_id,
        process_key="control",
        thread_key="main",
    )

    assert provider_input.description is not None
    assert provider_input.status is not None
    assert provider_input.topology is not None
    assert api_client.environment.describe.requests[0].environment_id == env_id
    assert api_client.environment.topology.requests[0].process_key == "control"
    assert provider_input.provenance.environment_id == str(env_id)


def test_environment_view_provider_boundary_avoids_raw_renderer_graph_reads() -> None:
    provider_source = (
        Path(__file__).parents[1] / "aware_environment_sdk" / "view_state_providers.py"
    ).read_text(encoding="utf-8")

    assert "materialized_lane" not in provider_source
    assert "class_instances" not in provider_source


class _RecordingDescribeClient:
    def __init__(self, *, env_id: UUID) -> None:
        self.env_id = env_id
        self.requests: list[DescribeEnvironmentRequest] = []

    async def describe_environment(
        self,
        request: DescribeEnvironmentRequest,
    ) -> DescribeEnvironmentResponse:
        self.requests.append(request)
        return _description(env_id=self.env_id)


class _RecordingStatusClient:
    def __init__(self, *, env_id: UUID) -> None:
        self.env_id = env_id
        self.requests: list[DescribeEnvironmentStatusRequest] = []

    async def describe_environment_status(
        self,
        request: DescribeEnvironmentStatusRequest,
    ) -> DescribeEnvironmentStatusResponse:
        self.requests.append(request)
        return _status(env_id=self.env_id)


class _RecordingTopologyClient:
    def __init__(self, *, env_id: UUID) -> None:
        self.env_id = env_id
        self.requests: list[DescribeEnvironmentTopologyRequest] = []

    async def describe_environment_topology(
        self,
        request: DescribeEnvironmentTopologyRequest,
    ) -> DescribeEnvironmentTopologyResponse:
        self.requests.append(request)
        return _topology(env_id=self.env_id)


class _RecordingEnvironmentApiClient:
    def __init__(self, *, env_id: UUID) -> None:
        self.describe = _RecordingDescribeClient(env_id=env_id)
        self.status = _RecordingStatusClient(env_id=env_id)
        self.topology = _RecordingTopologyClient(env_id=env_id)


class _RecordingGeneratedApiClient:
    def __init__(self, *, env_id: UUID) -> None:
        self.environment = _RecordingEnvironmentApiClient(env_id=env_id)


def _provider_input(
    *,
    env_id: UUID | None = None,
    selected_thread_key: str | None = None,
) -> EnvironmentViewsV1ProviderInput:
    resolved_env_id = env_id or uuid4()
    return EnvironmentViewsV1ProviderInput(
        description=_description(env_id=resolved_env_id),
        status=_status(env_id=resolved_env_id),
        topology=_topology(env_id=resolved_env_id),
        selected_process_key="control",
        selected_thread_key=selected_thread_key,
        provenance=ViewProviderProvenanceV1(environment_id=str(resolved_env_id)),
    )


def _description(*, env_id: UUID) -> DescribeEnvironmentResponse:
    return DescribeEnvironmentResponse(
        environment_id=env_id,
        status="succeeded",
        environment_title="Kernel Environment",
        environment_config_title="Kernel",
        boot_process_id=_process_id(),
        boot_thread_id=_thread_id(),
    )


def _status(*, env_id: UUID) -> DescribeEnvironmentStatusResponse:
    return DescribeEnvironmentStatusResponse(
        environment_id=env_id,
        status="succeeded",
        status_version="v1",
        blocks=[
            EnvironmentStatusBlock(
                name="commit_truth",
                authority=EnvironmentStatusAuthority(
                    kind=EnvironmentStatusAuthorityKind.commit_truth,
                ),
                payload={"head": "ok"},
                available=True,
            )
        ],
    )


def _topology(*, env_id: UUID) -> DescribeEnvironmentTopologyResponse:
    return DescribeEnvironmentTopologyResponse(
        environment_id=env_id,
        status="succeeded",
        processes=[
            DescribeEnvironmentTopologyProcess(
                process_id=_process_id(),
                process_key="control",
                title="Control",
                description="Control process",
                threads=[
                    DescribeEnvironmentTopologyThread(
                        thread_id=_thread_id(),
                        thread_key="main",
                        title="Main",
                        active_layout_id=_layout_id(),
                        active_layout_key="coordination",
                        layouts=[
                            DescribeEnvironmentTopologyLayout(
                                layout_id=_layout_id(),
                                layout_key="coordination",
                                title="Coordination",
                                description="Conversation plus coordination surfaces",
                                is_active=True,
                                sections=[
                                    DescribeEnvironmentTopologySection(
                                        section_key="conversation",
                                        title="Conversation",
                                        description="Team thread",
                                        order=0,
                                        flex=2.0,
                                        is_visible=True,
                                        view_ref="aware_conversations.chat.home.v1",
                                        view_key="chat.home.v1",
                                        package_name="aware_conversations",
                                    )
                                ],
                            )
                        ],
                        attachments=[
                            DescribeEnvironmentTopologyAttachment(
                                assoc_id=uuid4(),
                                title="Conversation lane",
                                is_active=True,
                                object_instance_graph_branch_id=uuid4(),
                                object_instance_graph_identity_id=uuid4(),
                                domain_branch_id=uuid4(),
                                lanes=[
                                    DescribeEnvironmentTopologyLane(
                                        lane_hash="conversation-hash",
                                        opg_id=uuid4(),
                                        opg_name="conversation",
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )


def _process_id() -> UUID:
    return UUID("11111111-1111-1111-1111-111111111111")


def _thread_id() -> UUID:
    return UUID("22222222-2222-2222-2222-222222222222")


def _layout_id() -> UUID:
    return UUID("33333333-3333-3333-3333-333333333333")
