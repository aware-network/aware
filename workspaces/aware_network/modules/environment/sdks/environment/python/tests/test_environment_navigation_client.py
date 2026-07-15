from __future__ import annotations

from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_environment_sdk import (
    EnvironmentNavigationClient,
    EnvironmentNavigationClientContext,
    EnvironmentNavigationError,
)
from aware_environment_sdk.session import (
    EnvironmentSessionIdentityEvidence as SdkEnvironmentSessionIdentityEvidence,
    EnvironmentSessionJoinReceipt as SdkEnvironmentSessionJoinReceipt,
    EnvironmentSessionStartResult,
)
from aware_environment_service_dto.environment.environment import (
    CreateEnvironmentNavigationContextRequest,
    CreateEnvironmentNavigationContextResponse,
    DescribeEnvironmentNavigationContextRequest,
    DescribeEnvironmentNavigationContextResponse,
    EnvironmentSessionIdentityEvidence,
    EnvironmentNavigationCommitReceipt,
    EnvironmentNavigationContextView,
    EnvironmentSessionJoinReceipt,
    ListEnvironmentNavigationContextsRequest,
    ListEnvironmentNavigationContextsResponse,
    SelectEnvironmentNavigationTargetRequest,
    SelectEnvironmentNavigationTargetResponse,
)
from aware_identity_service_dto.session.session import (
    SessionMemberActorRoleSummary,
    SessionMemberSummary,
    SessionSummary,
)


class _RecordingNavigationClient:
    def __init__(self, *, accepted: bool = True) -> None:
        self.accepted = accepted
        self.context_id = uuid4()
        self.create_requests: list[CreateEnvironmentNavigationContextRequest] = []
        self.select_requests: list[SelectEnvironmentNavigationTargetRequest] = []
        self.describe_requests: list[DescribeEnvironmentNavigationContextRequest] = []
        self.list_requests: list[ListEnvironmentNavigationContextsRequest] = []
        self.contexts: dict[UUID, EnvironmentNavigationContextView] = {}

    async def create_navigation_context(
        self,
        request: CreateEnvironmentNavigationContextRequest,
    ) -> CreateEnvironmentNavigationContextResponse:
        self.create_requests.append(request)
        context = _navigation_context(
            environment_navigation_context_id=self.context_id,
            environment_session_id=request.environment_session_id,
            environment_id=request.environment_id,
            key=request.key,
            is_default=request.is_default,
            selected_process_id=request.selected_process_id,
            selected_thread_id=request.selected_thread_id,
        )
        self.contexts[self.context_id] = context
        receipt = _navigation_receipt(
            accepted=self.accepted,
            status="created" if self.accepted else "blocked",
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            environment_session_id=request.environment_session_id,
            environment_navigation_context_id=self.context_id,
            is_default=request.is_default,
            selected_process_id=request.selected_process_id,
            selected_thread_id=request.selected_thread_id,
            error=None if self.accepted else "environment_session_join_not_accepted",
        )
        return CreateEnvironmentNavigationContextResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            request_id=request.request_id,
            accepted=self.accepted,
            status="created" if self.accepted else "blocked",
            error=None if self.accepted else "environment_session_join_not_accepted",
            context=context if self.accepted else None,
            receipt=receipt,
            evidence=cast(Any, {"source": "recording-navigation"}),
        )

    async def select_navigation_target(
        self,
        request: SelectEnvironmentNavigationTargetRequest,
    ) -> SelectEnvironmentNavigationTargetResponse:
        self.select_requests.append(request)
        context = self.contexts[request.environment_navigation_context_id].model_copy(
            update={
                "selected_process_id": request.selected_process_id,
                "selected_thread_id": request.selected_thread_id,
                "commit_id": uuid4(),
                "graph_hash_post": "hash-select",
            }
        )
        self.contexts[request.environment_navigation_context_id] = context
        return SelectEnvironmentNavigationTargetResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            request_id=request.request_id,
            accepted=True,
            status="selected",
            context=context,
            receipt=_navigation_receipt(
                accepted=True,
                status="selected",
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                environment_session_id=request.environment_session_id,
                environment_navigation_context_id=request.environment_navigation_context_id,
                selected_process_id=request.selected_process_id,
                selected_thread_id=request.selected_thread_id,
                reason=request.reason,
            ),
            evidence=cast(Any, {"source": "recording-navigation"}),
        )

    async def describe_navigation_context(
        self,
        request: DescribeEnvironmentNavigationContextRequest,
    ) -> DescribeEnvironmentNavigationContextResponse:
        self.describe_requests.append(request)
        return DescribeEnvironmentNavigationContextResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            status="described",
            context=self.contexts.get(request.environment_navigation_context_id),
            evidence=cast(Any, {"source": "recording-navigation"}),
        )

    async def list_navigation_contexts(
        self,
        request: ListEnvironmentNavigationContextsRequest,
    ) -> ListEnvironmentNavigationContextsResponse:
        self.list_requests.append(request)
        return ListEnvironmentNavigationContextsResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            status="listed",
            contexts=list(self.contexts.values()),
            evidence=cast(Any, {"source": "recording-navigation"}),
        )


class _RecordingEnvironmentApi:
    def __init__(self, *, accepted: bool = True) -> None:
        self.navigation = _RecordingNavigationClient(accepted=accepted)


class _RecordingGeneratedApiClient:
    def __init__(self, *, accepted: bool = True) -> None:
        self.environment = _RecordingEnvironmentApi(accepted=accepted)


def _client_context() -> EnvironmentNavigationClientContext:
    return EnvironmentNavigationClientContext(
        actor_id=uuid4(),
        environment_id=uuid4(),
    )


def _join_receipt(
    *,
    actor_id: UUID,
    environment_id: UUID,
    environment_profile_id: UUID,
    environment_session_id: UUID,
) -> EnvironmentSessionJoinReceipt:
    identity_session = SessionSummary(
        session_id=uuid4(),
        session_config_id=uuid4(),
        key="shared",
        member_count=1,
    )
    identity_member = SessionMemberSummary(
        session_member_id=uuid4(),
        session_id=identity_session.session_id,
        actor_id=actor_id,
        session_actor_config_id=uuid4(),
        actor_roles=[
            SessionMemberActorRoleSummary(
                session_member_actor_role_id=uuid4(),
                session_member_id=uuid4(),
                actor_role_id=uuid4(),
                source_kind="environment_admission",
            )
        ],
    )
    return EnvironmentSessionJoinReceipt(
        accepted=True,
        status="joined",
        actor_id=actor_id,
        environment_id=environment_id,
        environment_profile_id=environment_profile_id,
        environment_session_id=environment_session_id,
        environment_session_key="shared",
        identity_evidence=EnvironmentSessionIdentityEvidence(
            identity_session=identity_session,
            identity_member=identity_member,
            identity_actor_roles=identity_member.actor_roles,
            evidence=cast(Any, {"source": "recording-session"}),
        ),
        evidence=cast(Any, {"source": "recording-session"}),
    )


def _sdk_join_receipt(
    receipt: EnvironmentSessionJoinReceipt,
) -> SdkEnvironmentSessionJoinReceipt:
    identity_evidence = (
        SdkEnvironmentSessionIdentityEvidence(
            identity_session=receipt.identity_evidence.identity_session,
            identity_member=receipt.identity_evidence.identity_member,
            identity_actor_roles=tuple(receipt.identity_evidence.identity_actor_roles),
            evidence=dict(receipt.identity_evidence.evidence),
            dto_evidence=receipt.identity_evidence,
        )
        if receipt.identity_evidence is not None
        else None
    )
    return SdkEnvironmentSessionJoinReceipt(
        accepted=receipt.accepted,
        status=receipt.status,
        error=receipt.error,
        reason=receipt.reason,
        actor_id=receipt.actor_id,
        environment_id=receipt.environment_id,
        environment_profile_id=receipt.environment_profile_id,
        environment_session_id=receipt.environment_session_id,
        environment_session_key=receipt.environment_session_key,
        identity_evidence=identity_evidence,
        blockers=tuple(receipt.blockers),
        evidence=dict(receipt.evidence),
        dto_receipt=receipt,
    )


def _navigation_context(
    *,
    environment_navigation_context_id: UUID,
    environment_session_id: UUID,
    environment_id: UUID,
    key: str,
    selected_process_id: UUID | None,
    selected_thread_id: UUID | None,
    is_default: bool = False,
) -> EnvironmentNavigationContextView:
    return EnvironmentNavigationContextView(
        environment_navigation_context_id=environment_navigation_context_id,
        environment_session_id=environment_session_id,
        environment_id=environment_id,
        key=key,
        is_default=is_default,
        selected_process_id=selected_process_id,
        selected_thread_id=selected_thread_id,
        branch_id=uuid4(),
        projection_hash="EnvironmentNavigationContext",
        root_object_id=environment_navigation_context_id,
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
        graph_hash_post="hash-create",
        evidence=cast(Any, {"source": "recording-navigation"}),
    )


def _navigation_receipt(
    *,
    accepted: bool,
    status: str,
    actor_id: UUID | None,
    environment_id: UUID,
    environment_session_id: UUID,
    environment_navigation_context_id: UUID,
    selected_process_id: UUID | None,
    selected_thread_id: UUID | None,
    is_default: bool = False,
    error: str | None = None,
    reason: str | None = None,
) -> EnvironmentNavigationCommitReceipt:
    return EnvironmentNavigationCommitReceipt(
        accepted=accepted,
        status=status,
        error=error,
        reason=reason,
        actor_id=actor_id,
        environment_id=environment_id,
        environment_session_id=environment_session_id,
        environment_navigation_context_id=environment_navigation_context_id,
        key="main",
        is_default=is_default,
        branch_id=uuid4(),
        projection_hash="EnvironmentNavigationContext",
        root_object_id=environment_navigation_context_id,
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
        graph_hash_post="hash",
        selected_process_id=selected_process_id,
        selected_thread_id=selected_thread_id,
        blockers=[] if accepted else [cast(str, error)],
        evidence=cast(Any, {"source": "recording-navigation"}),
    )


@pytest.mark.asyncio
async def test_environment_navigation_client_uses_session_join_receipt_for_context_flow() -> (
    None
):
    context = _client_context()
    api_client = _RecordingGeneratedApiClient()
    navigation_client = EnvironmentNavigationClient(
        api_client=api_client,
        context=context,
    )
    environment_session_id = uuid4()
    join_receipt = _join_receipt(
        actor_id=context.actor_id,
        environment_id=context.environment_id,
        environment_profile_id=uuid4(),
        environment_session_id=environment_session_id,
    )
    process_id = uuid4()
    thread_id = uuid4()

    create_result = await navigation_client.create_navigation_context(
        environment_session_id=environment_session_id,
        session_join_receipt=_sdk_join_receipt(join_receipt),
        key="main",
        title="Main",
        is_default=True,
        selected_process_id=process_id,
        selected_thread_id=thread_id,
    )

    assert create_result.accepted is True
    assert create_result.context is not None
    assert create_result.context.is_default is True
    assert create_result.context.selected_process_id == process_id
    assert create_result.receipt.environment_session_id == environment_session_id
    assert create_result.receipt.is_default is True
    create_request = api_client.environment.navigation.create_requests[0]
    assert create_request.actor_id == context.actor_id
    assert create_request.environment_id == context.environment_id
    assert create_request.session_join_receipt == join_receipt

    next_process_id = uuid4()
    next_thread_id = uuid4()
    select_result = await navigation_client.select_navigation_target(
        environment_session_id=environment_session_id,
        environment_navigation_context_id=(
            create_result.context.environment_navigation_context_id
        ),
        session_join_receipt=join_receipt,
        selected_process_id=next_process_id,
        selected_thread_id=next_thread_id,
        reason="focus issue",
    )

    assert select_result.accepted is True
    assert select_result.context is not None
    assert select_result.context.selected_thread_id == next_thread_id
    select_request = api_client.environment.navigation.select_requests[0]
    assert select_request.reason == "focus issue"
    assert select_request.session_join_receipt == join_receipt

    describe_result = await navigation_client.describe_navigation_context(
        environment_session_id=environment_session_id,
        environment_navigation_context_id=(
            create_result.context.environment_navigation_context_id
        ),
        session_join_receipt=join_receipt,
    )
    list_result = await navigation_client.list_navigation_contexts(
        environment_session_id=environment_session_id,
        session_join_receipt=join_receipt,
    )

    assert describe_result.status == "described"
    assert describe_result.context is not None
    assert list_result.status == "listed"
    assert [
        item.environment_navigation_context_id for item in list_result.contexts
    ] == [create_result.context.environment_navigation_context_id]


@pytest.mark.asyncio
async def test_environment_navigation_client_accepts_session_start_result() -> None:
    context = _client_context()
    api_client = _RecordingGeneratedApiClient()
    navigation_client = EnvironmentNavigationClient(
        api_client=api_client,
        context=context,
    )
    environment_session_id = uuid4()
    join_receipt = _join_receipt(
        actor_id=context.actor_id,
        environment_id=context.environment_id,
        environment_profile_id=uuid4(),
        environment_session_id=environment_session_id,
    )
    session_start = EnvironmentSessionStartResult(
        accepted=True,
        status="started",
        error=None,
        session=None,
        join_receipt=_sdk_join_receipt(join_receipt),
        default_navigation_context=None,
        default_navigation_receipt=None,
        evidence={"source": "test"},
    )

    result = await navigation_client.create_navigation_context(
        environment_session_id=environment_session_id,
        session_join_receipt=session_start,
        key="main",
    )

    assert result.accepted is True
    assert (
        api_client.environment.navigation.create_requests[0].session_join_receipt
        == join_receipt
    )


@pytest.mark.asyncio
async def test_environment_navigation_client_raises_on_rejected_create() -> None:
    context = _client_context()
    api_client = _RecordingGeneratedApiClient(accepted=False)
    navigation_client = EnvironmentNavigationClient(
        api_client=api_client,
        context=context,
    )
    environment_session_id = uuid4()
    join_receipt = _join_receipt(
        actor_id=context.actor_id,
        environment_id=context.environment_id,
        environment_profile_id=uuid4(),
        environment_session_id=environment_session_id,
    )

    with pytest.raises(EnvironmentNavigationError) as exc:
        await navigation_client.create_navigation_context(
            environment_session_id=environment_session_id,
            session_join_receipt=join_receipt,
            key="main",
        )

    assert exc.value.receipt is not None
    assert exc.value.receipt.accepted is False
    assert exc.value.receipt.error == "environment_session_join_not_accepted"
