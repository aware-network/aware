from __future__ import annotations

from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_environment_sdk import (
    EnvironmentSessionClient,
    EnvironmentSessionContext,
    EnvironmentSessionError,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionFocusTransitionPin,
    AttentionSessionPin,
    AttentionTransitionValidationResult,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentSessionRequest,
    DescribeEnvironmentSessionResponse,
    EnvironmentActorAdmissionReceipt,
    EnvironmentSessionAttentionResolution,
    EnvironmentActorAdmissionRoleBinding,
    EnvironmentNavigationCommitReceipt,
    EnvironmentNavigationContextView,
    EnvironmentSessionIdentityEvidence,
    EnvironmentSessionJoinReceipt,
    EnvironmentSessionView,
    JoinEnvironmentSessionRequest,
    JoinEnvironmentSessionResponse,
    MountEnvironmentSessionAttentionRequest,
    MountEnvironmentSessionAttentionResponse,
    ResolveEnvironmentSessionAttentionRequest,
    ResolveEnvironmentSessionAttentionResponse,
    StartEnvironmentSessionRequest,
    StartEnvironmentSessionResponse,
)
from aware_identity_service_dto.session.session import (
    SessionMemberActorRoleSummary,
    SessionMemberSummary,
    SessionSummary,
)


class _RecordingSessionClient:
    def __init__(self, *, accepted: bool = True) -> None:
        self.accepted = accepted
        self.session_id = uuid4()
        self.identity_session_id = uuid4()
        self.default_context_id = uuid4()
        self.default_process_id = uuid4()
        self.default_thread_id = uuid4()
        self.session_thread_id = uuid4()
        self.session_attention_session_id = uuid4()
        self.thread_layout_id = uuid4()
        self.attention_session_id = uuid4()
        self.transition_id = uuid4()
        self.focus_scope_id = uuid4()
        self.start_requests: list[StartEnvironmentSessionRequest] = []
        self.join_requests: list[JoinEnvironmentSessionRequest] = []
        self.describe_requests: list[DescribeEnvironmentSessionRequest] = []
        self.resolve_attention_requests: list[
            ResolveEnvironmentSessionAttentionRequest
        ] = []
        self.mount_attention_requests: list[MountEnvironmentSessionAttentionRequest] = (
            []
        )

    async def start_session(
        self,
        request: StartEnvironmentSessionRequest,
    ) -> StartEnvironmentSessionResponse:
        self.start_requests.append(request)
        identity_session = _identity_session(
            identity_session_id=self.identity_session_id,
            session_config_id=uuid4(),
            key=request.session_key,
        )
        identity_member = _identity_member(
            identity_session_id=identity_session.session_id,
            actor_id=cast(UUID, request.actor_id),
        )
        identity_evidence = _identity_evidence(
            identity_session=identity_session,
            identity_member=identity_member,
        )
        session = _session(
            environment_session_id=self.session_id,
            environment_session_config_id=request.environment_session_config_id,
            identity_session=identity_session,
            environment_id=request.environment_id,
            environment_profile_id=request.environment_profile_id,
            session_key=request.session_key,
        )
        receipt = EnvironmentSessionJoinReceipt(
            accepted=self.accepted,
            status="joined" if self.accepted else "blocked",
            error=None if self.accepted else "environment_admission_not_accepted",
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            environment_profile_id=request.environment_profile_id,
            environment_session_id=self.session_id if self.accepted else None,
            environment_session_key=request.session_key if self.accepted else None,
            identity_evidence=identity_evidence if self.accepted else None,
            blockers=[] if self.accepted else ["environment_admission_not_accepted"],
            evidence=cast(Any, {"source": "recording-session"}),
        )
        return StartEnvironmentSessionResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            request_id=request.request_id,
            accepted=self.accepted,
            status="started" if self.accepted else "blocked",
            error=None if self.accepted else "environment_admission_not_accepted",
            session=session if self.accepted else None,
            join_receipt=receipt,
            default_navigation_context=(
                _default_navigation_context(
                    environment_navigation_context_id=self.default_context_id,
                    environment_session_id=self.session_id,
                    environment_id=request.environment_id,
                    process_id=self.default_process_id,
                    thread_id=self.default_thread_id,
                )
                if self.accepted and request.resolve_default_navigation_context
                else None
            ),
            default_navigation_receipt=(
                _default_navigation_receipt(
                    environment_navigation_context_id=self.default_context_id,
                    environment_session_id=self.session_id,
                    environment_id=request.environment_id,
                    process_id=self.default_process_id,
                    thread_id=self.default_thread_id,
                )
                if self.accepted and request.resolve_default_navigation_context
                else None
            ),
            evidence=cast(Any, {"source": "recording-session"}),
        )

    async def join_session(
        self,
        request: JoinEnvironmentSessionRequest,
    ) -> JoinEnvironmentSessionResponse:
        self.join_requests.append(request)
        identity_session = _identity_session(
            identity_session_id=self.identity_session_id,
            session_config_id=uuid4(),
            key="shared",
        )
        identity_member = _identity_member(
            identity_session_id=identity_session.session_id,
            actor_id=cast(UUID, request.actor_id),
        )
        receipt = EnvironmentSessionJoinReceipt(
            accepted=True,
            status="joined",
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            environment_profile_id=request.environment_profile_id,
            environment_session_id=request.environment_session_id,
            environment_session_key="shared",
            identity_evidence=_identity_evidence(
                identity_session=identity_session,
                identity_member=identity_member,
            ),
            evidence=cast(Any, {"source": "recording-session"}),
        )
        return JoinEnvironmentSessionResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            request_id=request.request_id,
            accepted=True,
            status="joined",
            session=_session(
                environment_session_id=request.environment_session_id,
                environment_session_config_id=uuid4(),
                identity_session=identity_session,
                environment_id=request.environment_id,
                environment_profile_id=request.environment_profile_id,
                session_key="shared",
            ),
            receipt=receipt,
            default_navigation_context=(
                _default_navigation_context(
                    environment_navigation_context_id=self.default_context_id,
                    environment_session_id=request.environment_session_id,
                    environment_id=request.environment_id,
                    process_id=self.default_process_id,
                    thread_id=self.default_thread_id,
                )
                if request.resolve_default_navigation_context
                else None
            ),
            default_navigation_receipt=(
                _default_navigation_receipt(
                    environment_navigation_context_id=self.default_context_id,
                    environment_session_id=request.environment_session_id,
                    environment_id=request.environment_id,
                    process_id=self.default_process_id,
                    thread_id=self.default_thread_id,
                )
                if request.resolve_default_navigation_context
                else None
            ),
            evidence=cast(Any, {"source": "recording-session"}),
        )

    async def describe_session(
        self,
        request: DescribeEnvironmentSessionRequest,
    ) -> DescribeEnvironmentSessionResponse:
        self.describe_requests.append(request)
        identity_session = _identity_session(
            identity_session_id=self.identity_session_id,
            session_config_id=uuid4(),
            key="shared",
        )
        return DescribeEnvironmentSessionResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            status="described",
            session=_session(
                environment_session_id=request.environment_session_id,
                environment_session_config_id=uuid4(),
                identity_session=identity_session,
                environment_id=request.environment_id,
                environment_profile_id=uuid4(),
                session_key="shared",
            ),
            evidence=cast(Any, {"source": "recording-session"}),
        )

    async def resolve_attention(
        self,
        request: ResolveEnvironmentSessionAttentionRequest,
    ) -> ResolveEnvironmentSessionAttentionResponse:
        self.resolve_attention_requests.append(request)
        transition = _attention_transition(
            attention_session_id=self.attention_session_id,
            transition_id=(request.attention_focus_transition_id or self.transition_id),
            focus_scope_id=request.expected_focus_scope_id or self.focus_scope_id,
        )
        return ResolveEnvironmentSessionAttentionResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            request_id=request.request_id,
            status="resolved",
            resolution=EnvironmentSessionAttentionResolution(
                environment_session_id=request.environment_session_id,
                environment_navigation_context_id=(
                    request.environment_navigation_context_id or self.default_context_id
                ),
                environment_session_thread_id=(
                    request.environment_session_thread_id or self.session_thread_id
                ),
                environment_session_attention_session_id=(
                    request.environment_session_attention_session_id
                    or self.session_attention_session_id
                ),
                environment_id=request.environment_id,
                environment_profile_id=uuid4(),
                thread_id=self.default_thread_id,
                thread_layout_id=self.thread_layout_id,
                attention_session_id=self.attention_session_id,
                identity_session_id=self.identity_session_id,
                attention_session=AttentionSessionPin(
                    attention_session_id=self.attention_session_id,
                    identity_session_id=self.identity_session_id,
                    key="shared-attention",
                ),
                active_transition=transition,
                validation=AttentionTransitionValidationResult(
                    exists=True,
                    valid=True,
                    transition=transition,
                ),
                transitions=[transition] if request.include_transition_list else [],
                status="resolved",
                evidence=cast(Any, {"source": "recording-session"}),
            ),
            evidence=cast(Any, {"source": "recording-session"}),
        )

    async def mount_attention_session(
        self,
        request: MountEnvironmentSessionAttentionRequest,
    ) -> MountEnvironmentSessionAttentionResponse:
        self.mount_attention_requests.append(request)
        return MountEnvironmentSessionAttentionResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            request_id=request.request_id,
            environment_session_attention_session_id=(
                self.session_attention_session_id
            ),
            environment_session_id=request.environment_session_id,
            attention_session_id=request.attention_session_id,
            key=request.key,
            title=request.title,
            status=request.status.strip().lower(),
            metadata=request.metadata,
            domain_commit_id=uuid4(),
            object_instance_graph_commit_id=uuid4(),
            graph_hash_post="sha256:environment-attention-portal",
        )


class _RecordingEnvironmentApi:
    def __init__(self, *, accepted: bool = True) -> None:
        self.session = _RecordingSessionClient(accepted=accepted)


class _RecordingGeneratedApiClient:
    def __init__(self, *, accepted: bool = True) -> None:
        self.environment = _RecordingEnvironmentApi(accepted=accepted)


def _context() -> EnvironmentSessionContext:
    return EnvironmentSessionContext(
        actor_id=uuid4(),
        environment_id=uuid4(),
    )


def _admission_receipt(
    *,
    actor_id: UUID,
    environment_id: UUID,
    environment_profile_id: UUID,
) -> EnvironmentActorAdmissionReceipt:
    role_config_id = uuid4()
    binding = EnvironmentActorAdmissionRoleBinding(
        environment_profile_actor_config_id=uuid4(),
        actor_config_role_config_id=uuid4(),
        role_config_id=role_config_id,
        role_config_name="aware.environment.member",
        actor_id=actor_id,
        role_id=uuid4(),
        actor_role_id=uuid4(),
        role_class_instance_id=uuid4(),
        class_instance_identity_id=uuid4(),
        role_config_class_config_id=uuid4(),
        object_instance_graph_identity_id=uuid4(),
        object_instance_graph_branch_key="all",
    )
    return EnvironmentActorAdmissionReceipt(
        accepted=True,
        status="admitted",
        actor_id=actor_id,
        environment_id=environment_id,
        environment_profile_id=environment_profile_id,
        environment_profile_actor_config_id=binding.environment_profile_actor_config_id,
        actor_config_id=uuid4(),
        class_instance_identity_id=binding.class_instance_identity_id,
        object_instance_graph_branch_key="all",
        requested_role_config_ids=[role_config_id],
        bindings=[binding],
        evidence=cast(Any, {"source": "test"}),
    )


def _identity_session(
    *,
    identity_session_id: UUID,
    session_config_id: UUID,
    key: str,
) -> SessionSummary:
    return SessionSummary(
        session_id=identity_session_id,
        session_config_id=session_config_id,
        key=key,
        title="Shared",
        member_count=1,
        metadata_json=cast(Any, {"source": "recording-session"}),
    )


def _identity_member(
    *,
    identity_session_id: UUID,
    actor_id: UUID,
) -> SessionMemberSummary:
    return SessionMemberSummary(
        session_member_id=uuid4(),
        session_id=identity_session_id,
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
        metadata_json=cast(Any, {"source": "recording-session"}),
    )


def _identity_evidence(
    *,
    identity_session: SessionSummary,
    identity_member: SessionMemberSummary,
) -> EnvironmentSessionIdentityEvidence:
    return EnvironmentSessionIdentityEvidence(
        identity_session=identity_session,
        identity_member=identity_member,
        identity_actor_roles=identity_member.actor_roles,
        evidence=cast(Any, {"source": "recording-session"}),
    )


def _default_navigation_context(
    *,
    environment_navigation_context_id: UUID,
    environment_session_id: UUID,
    environment_id: UUID,
    process_id: UUID,
    thread_id: UUID,
) -> EnvironmentNavigationContextView:
    return EnvironmentNavigationContextView(
        environment_navigation_context_id=environment_navigation_context_id,
        environment_session_id=environment_session_id,
        environment_id=environment_id,
        key="default",
        title="Default",
        is_default=True,
        selected_process_id=process_id,
        selected_thread_id=thread_id,
        branch_id=uuid4(),
        projection_hash="EnvironmentNavigationContext",
        root_object_id=environment_navigation_context_id,
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
        graph_hash_post="hash-default",
        evidence=cast(Any, {"source": "recording-session"}),
    )


def _default_navigation_receipt(
    *,
    environment_navigation_context_id: UUID,
    environment_session_id: UUID,
    environment_id: UUID,
    process_id: UUID,
    thread_id: UUID,
) -> EnvironmentNavigationCommitReceipt:
    return EnvironmentNavigationCommitReceipt(
        accepted=True,
        status="created",
        environment_id=environment_id,
        environment_session_id=environment_session_id,
        environment_navigation_context_id=environment_navigation_context_id,
        key="default",
        is_default=True,
        branch_id=uuid4(),
        projection_hash="EnvironmentNavigationContext",
        root_object_id=environment_navigation_context_id,
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
        graph_hash_post="hash-default",
        selected_process_id=process_id,
        selected_thread_id=thread_id,
        evidence=cast(Any, {"source": "recording-session"}),
    )


def _attention_transition(
    *,
    attention_session_id: UUID,
    transition_id: UUID,
    focus_scope_id: UUID,
) -> AttentionFocusTransitionPin:
    return AttentionFocusTransitionPin(
        attention_focus_transition_id=transition_id,
        attention_session_section_id=uuid4(),
        attention_session_layout_id=uuid4(),
        attention_session_id=attention_session_id,
        identity_session_id=uuid4(),
        layout_section_id=uuid4(),
        section_id=uuid4(),
        section_key="main",
        layout_id=uuid4(),
        focus_scope_id=focus_scope_id,
        transition_key="focus-main",
        projection_hash="ThreadLayout",
    )


def _session(
    *,
    environment_session_id: UUID,
    environment_session_config_id: UUID,
    identity_session: SessionSummary,
    environment_id: UUID,
    environment_profile_id: UUID,
    session_key: str,
) -> EnvironmentSessionView:
    return EnvironmentSessionView(
        environment_session_id=environment_session_id,
        environment_session_config_id=environment_session_config_id,
        identity_session_id=identity_session.session_id,
        identity_session=identity_session,
        environment_id=environment_id,
        environment_profile_id=environment_profile_id,
        session_key=session_key,
        status="active",
        evidence=cast(Any, {"source": "recording-session"}),
    )


@pytest.mark.asyncio
async def test_environment_session_client_starts_joins_and_describes() -> None:
    api_client = _RecordingGeneratedApiClient()
    context = _context()
    client = EnvironmentSessionClient(api_client=api_client, context=context)
    environment_profile_id = uuid4()
    environment_session_config_id = uuid4()
    admission = _admission_receipt(
        actor_id=context.actor_id,
        environment_id=context.environment_id,
        environment_profile_id=environment_profile_id,
    )

    start = await client.start_session(
        environment_profile_id=str(environment_profile_id),
        environment_session_config_id=environment_session_config_id,
        admission_receipt=admission,
        session_key="goal-run",
        title="Goal run",
        resolve_default_navigation_context=True,
        metadata={"source": "sdk-test"},
    )

    assert start.accepted is True
    assert start.session is not None
    assert start.session.session_key == "goal-run"
    assert start.session.identity_session is not None
    assert start.join_receipt.identity_evidence is not None
    assert start.default_navigation_context is not None
    assert start.default_navigation_context.is_default is True
    assert start.default_navigation_receipt is not None
    assert start.default_navigation_receipt.is_default is True
    assert start.join_receipt.identity_evidence.identity_member is not None
    assert (
        start.join_receipt.identity_evidence.identity_member.actor_id
        == context.actor_id
    )
    start_request = api_client.environment.session.start_requests[0]
    assert start_request.actor_id == context.actor_id
    assert start_request.environment_id == context.environment_id
    assert start_request.environment_profile_id == environment_profile_id
    assert start_request.environment_session_config_id == environment_session_config_id
    assert start_request.admission_receipt is admission
    assert start_request.resolve_default_navigation_context is True
    assert start_request.metadata == {"source": "sdk-test"}

    join = await client.join_session(
        environment_profile_id=environment_profile_id,
        environment_session_id=start.session.environment_session_id,
        admission_receipt=admission,
        reason="join again",
        resolve_default_navigation_context=True,
    )

    assert join.accepted is True
    assert join.session is not None
    assert join.receipt.environment_session_id == start.session.environment_session_id
    assert join.default_navigation_context is not None
    assert join.default_navigation_context.is_default is True
    assert join.receipt.identity_evidence is not None
    assert join.receipt.identity_evidence.identity_member is not None
    join_request = api_client.environment.session.join_requests[0]
    assert join_request.environment_session_id == start.session.environment_session_id
    assert join_request.admission_receipt is admission
    assert join_request.resolve_default_navigation_context is True

    described = await client.describe_session(
        environment_session_id=start.session.environment_session_id,
    )

    assert described.status == "described"
    assert described.session is not None
    assert described.session.identity_session is not None
    describe_request = api_client.environment.session.describe_requests[0]
    assert describe_request.actor_id == context.actor_id
    assert describe_request.environment_id == context.environment_id
    assert (
        describe_request.environment_session_id == start.session.environment_session_id
    )


@pytest.mark.asyncio
async def test_environment_session_client_resolves_attention() -> None:
    api_client = _RecordingGeneratedApiClient()
    context = _context()
    client = EnvironmentSessionClient(api_client=api_client, context=context)
    environment_session_id = uuid4()
    environment_navigation_context_id = uuid4()
    environment_session_thread_id = uuid4()
    expected_attention_session_id = api_client.environment.session.attention_session_id
    transition_id = uuid4()
    focus_scope_id = uuid4()

    result = await client.resolve_attention(
        environment_session_id=str(environment_session_id),
        environment_navigation_context_id=environment_navigation_context_id,
        environment_session_thread_id=environment_session_thread_id,
        expected_attention_session_id=expected_attention_session_id,
        attention_focus_transition_id=transition_id,
        expected_focus_scope_id=focus_scope_id,
        expected_projection_hash="ThreadLayout",
        include_transition_list=True,
        transition_limit=3,
        metadata={"source": "sdk-test"},
    )

    assert result.status == "resolved"
    assert result.resolution is not None
    assert result.resolution.environment_session_id == environment_session_id
    assert result.resolution.environment_navigation_context_id == (
        environment_navigation_context_id
    )
    assert result.resolution.environment_session_thread_id == (
        environment_session_thread_id
    )
    assert result.resolution.attention_session_id == expected_attention_session_id
    assert result.resolution.attention_session is not None
    assert result.resolution.validation is not None
    assert result.resolution.validation.valid is True
    assert result.resolution.active_transition is not None
    assert result.resolution.active_transition.attention_focus_transition_id == (
        transition_id
    )
    assert len(result.resolution.transitions) == 1

    request = api_client.environment.session.resolve_attention_requests[0]
    assert request.actor_id == context.actor_id
    assert request.environment_id == context.environment_id
    assert request.environment_session_id == environment_session_id
    assert request.environment_navigation_context_id == (
        environment_navigation_context_id
    )
    assert request.environment_session_thread_id == environment_session_thread_id
    assert request.expected_attention_session_id == expected_attention_session_id
    assert request.attention_focus_transition_id == transition_id
    assert request.expected_focus_scope_id == focus_scope_id
    assert request.expected_projection_hash == "ThreadLayout"
    assert request.include_transition_list is True
    assert request.transition_limit == 3
    assert request.metadata == {"source": "sdk-test"}


@pytest.mark.asyncio
async def test_environment_session_client_mounts_attention_portal() -> None:
    api_client = _RecordingGeneratedApiClient()
    context = _context()
    client = EnvironmentSessionClient(api_client=api_client, context=context)
    environment_session_id = uuid4()
    attention_session_id = uuid4()

    result = await client.mount_attention_session(
        environment_session_id=str(environment_session_id),
        attention_session_id=attention_session_id,
        key="shared-looking",
        title="Shared looking",
        metadata={"source": "sdk-test"},
    )

    assert result.environment_session_attention_session_id == (
        api_client.environment.session.session_attention_session_id
    )
    assert result.environment_session_id == environment_session_id
    assert result.attention_session_id == attention_session_id
    assert result.status == "active"
    assert result.graph_hash_post == "sha256:environment-attention-portal"

    request = api_client.environment.session.mount_attention_requests[0]
    assert request.actor_id == context.actor_id
    assert request.environment_id == context.environment_id
    assert request.environment_session_id == environment_session_id
    assert request.attention_session_id == attention_session_id
    assert request.key == "shared-looking"
    assert request.metadata == {"source": "sdk-test"}


@pytest.mark.asyncio
async def test_environment_session_client_raises_on_rejected_start() -> None:
    api_client = _RecordingGeneratedApiClient(accepted=False)
    context = _context()
    client = EnvironmentSessionClient(api_client=api_client, context=context)
    environment_profile_id = uuid4()

    with pytest.raises(EnvironmentSessionError) as exc_info:
        await client.start_session(
            environment_profile_id=environment_profile_id,
            environment_session_config_id=uuid4(),
            admission_receipt=_admission_receipt(
                actor_id=context.actor_id,
                environment_id=context.environment_id,
                environment_profile_id=environment_profile_id,
            ),
            session_key="blocked",
        )

    assert exc_info.value.receipt is not None
    assert exc_info.value.receipt.accepted is False
    assert exc_info.value.receipt.blockers == ("environment_admission_not_accepted",)
