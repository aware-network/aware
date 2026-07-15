from __future__ import annotations

from collections.abc import Mapping
from importlib import import_module
from typing import Any, Protocol, cast
from uuid import UUID

from pydantic import BaseModel, Field

from aware_types import JsonObject
from aware_attention_service_dto.attention.session.models import (
    AttentionFocusTransitionPin,
    AttentionSessionPin,
    AttentionTransitionValidationResult,
)
from aware_attention_service_dto.attention.session.service_operation import (
    DescribeAttentionSessionRequest,
    DescribeAttentionSessionResponse,
    ListAttentionTransitionsRequest,
    ListAttentionTransitionsResponse,
    ValidateAttentionTransitionRequest,
    ValidateAttentionTransitionResponse,
)
from aware_environment_service.actor_admission_service import (
    EnvironmentActorAdmissionReceiptSpec,
)
from aware_environment_service.navigation_models import (
    EnvironmentDefaultNavigationContextResolutionSpec,
    EnvironmentNavigationCommitReceiptSpec,
    EnvironmentNavigationContextViewSpec,
)
from aware_identity_service_dto.session.session import (
    SessionConfigActorConfigBindReceipt,
    SessionConfigActorConfigBindRequest,
    SessionJoinReceipt,
    SessionJoinRequest,
    SessionMemberActorRoleRecordReceipt,
    SessionMemberActorRoleRecordRequest,
    SessionMemberActorRoleSummary,
    SessionMemberSummary,
    SessionStartReceipt,
    SessionStartRequest,
    SessionSummary,
)
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)

_IDENTITY_SERVICE_API_PACKAGE_NAME = "identity-service-api"
_ATTENTION_SERVICE_API_PACKAGE_NAME = "attention-service-api"


def _json_object(values: Mapping[str, Any]) -> JsonObject:
    return JsonObject(dict(values))


class StartEnvironmentSessionRequestSpec(BaseModel):
    request_id: UUID | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    environment_profile_id: UUID
    environment_session_config_id: UUID
    admission_receipt: EnvironmentActorAdmissionReceiptSpec
    session_key: str
    title: str | None = None
    description: str | None = None
    purpose: str | None = None
    source_kind: str | None = None
    source_ref: str | None = None
    resolve_default_navigation_context: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class JoinEnvironmentSessionRequestSpec(BaseModel):
    request_id: UUID | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    environment_profile_id: UUID
    environment_session_id: UUID
    admission_receipt: EnvironmentActorAdmissionReceiptSpec
    reason: str | None = None
    resolve_default_navigation_context: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class DescribeEnvironmentSessionRequestSpec(BaseModel):
    actor_id: UUID | None = None
    environment_id: UUID
    environment_session_id: UUID


class ResolveEnvironmentSessionAttentionRequestSpec(BaseModel):
    request_id: UUID | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    branch_id: UUID | None = None
    projection_hash: str | None = None
    environment_session_id: UUID
    environment_navigation_context_id: UUID | None = None
    environment_session_thread_id: UUID | None = None
    environment_session_attention_session_id: UUID | None = None
    expected_attention_session_id: UUID | None = None
    attention_focus_transition_id: UUID | None = None
    expected_attention_session_section_id: UUID | None = None
    expected_focus_scope_id: UUID | None = None
    expected_object_instance_graph_commit_id: UUID | None = None
    expected_projection_hash: str | None = None
    include_attention_session: bool = True
    include_transition_list: bool = False
    transition_limit: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnvironmentSessionConfigViewSpec(BaseModel):
    environment_session_config_id: UUID
    environment_id: UUID
    environment_profile_id: UUID
    identity_session_config_id: UUID
    default_process_config_id: UUID | None = None
    default_thread_config_id: UUID | None = None
    key: str
    title: str | None = None
    description: str | None = None
    purpose: str | None = None
    status: str = "active"
    evidence: dict[str, Any] = Field(default_factory=dict)


class EnvironmentSessionIdentityEvidenceSpec(BaseModel):
    identity_session: SessionSummary | None = None
    identity_member: SessionMemberSummary | None = None
    identity_actor_roles: list[SessionMemberActorRoleSummary] = Field(
        default_factory=list
    )
    evidence: dict[str, Any] = Field(default_factory=dict)


class EnvironmentSessionViewSpec(BaseModel):
    environment_session_id: UUID
    environment_session_config_id: UUID | None = None
    identity_session_id: UUID | None = None
    identity_session: SessionSummary | None = None
    environment_id: UUID
    environment_profile_id: UUID
    session_key: str
    title: str | None = None
    description: str | None = None
    purpose: str | None = None
    status: str = "active"
    created_by_actor_id: UUID | None = None
    source_kind: str | None = None
    source_ref: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class EnvironmentSessionAttentionResolutionSpec(BaseModel):
    environment_session_id: UUID
    environment_navigation_context_id: UUID | None = None
    environment_session_thread_id: UUID | None = None
    environment_session_attention_session_id: UUID | None = None
    environment_id: UUID
    environment_profile_id: UUID | None = None
    thread_id: UUID | None = None
    thread_layout_id: UUID | None = None
    attention_session_id: UUID | None = None
    identity_session_id: UUID | None = None
    attention_session: AttentionSessionPin | None = None
    active_transition: AttentionFocusTransitionPin | None = None
    validation: AttentionTransitionValidationResult | None = None
    transitions: list[AttentionFocusTransitionPin] = Field(default_factory=list)
    status: str = "resolved"
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class EnvironmentSessionJoinReceiptSpec(BaseModel):
    accepted: bool = False
    status: str
    error: str | None = None
    reason: str | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    environment_profile_id: UUID
    environment_session_id: UUID | None = None
    environment_session_key: str | None = None
    identity_evidence: EnvironmentSessionIdentityEvidenceSpec | None = None
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class StartEnvironmentSessionResponseSpec(BaseModel):
    request_id: UUID | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    accepted: bool = False
    status: str
    error: str | None = None
    session: EnvironmentSessionViewSpec | None = None
    join_receipt: EnvironmentSessionJoinReceiptSpec
    default_navigation_context: EnvironmentNavigationContextViewSpec | None = None
    default_navigation_receipt: EnvironmentNavigationCommitReceiptSpec | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class JoinEnvironmentSessionResponseSpec(BaseModel):
    request_id: UUID | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    accepted: bool = False
    status: str
    error: str | None = None
    session: EnvironmentSessionViewSpec | None = None
    receipt: EnvironmentSessionJoinReceiptSpec
    default_navigation_context: EnvironmentNavigationContextViewSpec | None = None
    default_navigation_receipt: EnvironmentNavigationCommitReceiptSpec | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class DescribeEnvironmentSessionResponseSpec(BaseModel):
    actor_id: UUID | None = None
    environment_id: UUID
    status: str
    error: str | None = None
    session: EnvironmentSessionViewSpec | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class ResolveEnvironmentSessionAttentionResponseSpec(BaseModel):
    request_id: UUID | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    status: str
    error: str | None = None
    resolution: EnvironmentSessionAttentionResolutionSpec | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class _IdentityBindSessionConfigActorConfigCapability(Protocol):
    async def bind_session_config_actor_config(
        self,
        request: SessionConfigActorConfigBindRequest,
    ) -> SessionConfigActorConfigBindReceipt: ...


class _IdentityStartSessionCapability(Protocol):
    async def start_session(
        self, request: SessionStartRequest
    ) -> SessionStartReceipt: ...


class _IdentityJoinSessionCapability(Protocol):
    async def join_session(self, request: SessionJoinRequest) -> SessionJoinReceipt: ...


class _IdentityRecordSessionMemberActorRoleCapability(Protocol):
    async def record_session_member_actor_role(
        self,
        request: SessionMemberActorRoleRecordRequest,
    ) -> SessionMemberActorRoleRecordReceipt: ...


class _IdentitySessionApi(Protocol):
    @property
    def bind_session_config_actor_config(
        self,
    ) -> _IdentityBindSessionConfigActorConfigCapability: ...

    @property
    def start_session(self) -> _IdentityStartSessionCapability: ...

    @property
    def join_session(self) -> _IdentityJoinSessionCapability: ...

    @property
    def record_session_member_actor_role(
        self,
    ) -> _IdentityRecordSessionMemberActorRoleCapability: ...


class IdentityEnvironmentSessionApiClient(Protocol):
    @property
    def identity(self) -> _IdentitySessionApi: ...


class _AttentionDescribeSessionCapability(Protocol):
    async def describe_attention_session(
        self,
        request: DescribeAttentionSessionRequest,
    ) -> DescribeAttentionSessionResponse: ...


class _AttentionListTransitionsCapability(Protocol):
    async def list_attention_transitions(
        self,
        request: ListAttentionTransitionsRequest,
    ) -> ListAttentionTransitionsResponse: ...


class _AttentionValidateTransitionCapability(Protocol):
    async def validate_attention_transition(
        self,
        request: ValidateAttentionTransitionRequest,
    ) -> ValidateAttentionTransitionResponse: ...


class _AttentionSessionApi(Protocol):
    @property
    def describe_attention_session(self) -> _AttentionDescribeSessionCapability: ...

    @property
    def list_attention_transitions(self) -> _AttentionListTransitionsCapability: ...

    @property
    def validate_attention_transition(
        self,
    ) -> _AttentionValidateTransitionCapability: ...


class AttentionEnvironmentSessionApiClient(Protocol):
    @property
    def attention(self) -> _AttentionSessionApi: ...


class EnvironmentSessionBackend(Protocol):
    async def describe_environment_session_config(
        self,
        *,
        environment_id: UUID,
        environment_profile_id: UUID,
        environment_session_config_id: UUID,
    ) -> EnvironmentSessionConfigViewSpec | None: ...

    async def start_environment_session(
        self,
        *,
        request: StartEnvironmentSessionRequestSpec,
        session_config: EnvironmentSessionConfigViewSpec,
        identity_session: SessionSummary,
    ) -> EnvironmentSessionViewSpec: ...

    async def describe_environment_session(
        self,
        *,
        request: DescribeEnvironmentSessionRequestSpec,
    ) -> EnvironmentSessionViewSpec | None: ...

    async def resolve_environment_session_attention(
        self,
        *,
        request: ResolveEnvironmentSessionAttentionRequestSpec,
    ) -> EnvironmentSessionAttentionResolutionSpec | None: ...


class EnvironmentSessionAttentionBackend(Protocol):
    async def resolve_environment_session_attention(
        self,
        *,
        request: ResolveEnvironmentSessionAttentionRequestSpec,
    ) -> EnvironmentSessionAttentionResolutionSpec | None: ...


class _EnvironmentDefaultNavigationResolver(Protocol):
    async def ensure_default_navigation_context(
        self,
        *,
        actor_id: UUID | None,
        environment_id: UUID,
        environment_profile_id: UUID,
        session: EnvironmentSessionViewSpec,
        session_config: EnvironmentSessionConfigViewSpec | None,
        join_receipt: EnvironmentSessionJoinReceiptSpec,
        request_id: UUID | None,
        metadata: Mapping[str, Any],
    ) -> EnvironmentDefaultNavigationContextResolutionSpec: ...


async def start_environment_session(
    *,
    request: StartEnvironmentSessionRequestSpec,
    host_context: ServiceApiHostContext,
    session_backend: EnvironmentSessionBackend | None,
    identity_api_client: IdentityEnvironmentSessionApiClient | None = None,
) -> StartEnvironmentSessionResponseSpec:
    actor_id = request.actor_id or host_context.operation_context.actor_id
    validation = _validate_admission(
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        receipt=request.admission_receipt,
    )
    blocker_response = _blocked_start_for_validation(
        request=request,
        actor_id=actor_id,
        validation=validation,
    )
    if blocker_response is not None:
        return blocker_response

    if session_backend is None:
        return _blocked_start_response(
            request=request,
            actor_id=actor_id,
            reason="environment_session_backend_unavailable",
            blockers=["environment_session_backend_unavailable"],
            evidence=validation.evidence,
        )

    identity_client = identity_api_client or _build_identity_service_api_client(
        host_context=host_context,
    )
    identity_blocker = _identity_client_blocker(identity_client)
    if identity_blocker is not None:
        return _blocked_start_response(
            request=request,
            actor_id=actor_id,
            reason=identity_blocker,
            blockers=[identity_blocker],
            evidence=validation.evidence,
        )
    assert identity_client is not None

    session_config = await session_backend.describe_environment_session_config(
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        environment_session_config_id=request.environment_session_config_id,
    )
    config_blockers = _session_config_blockers(
        request_environment_id=request.environment_id,
        request_environment_profile_id=request.environment_profile_id,
        session_config=session_config,
    )
    if config_blockers:
        return _blocked_start_response(
            request=request,
            actor_id=actor_id,
            reason=config_blockers[0],
            blockers=config_blockers,
            evidence=validation.evidence,
        )
    assert session_config is not None

    identity_session = await _start_identity_session(
        request=request,
        actor_id=actor_id,
        identity_client=identity_client,
        session_config=session_config,
    )
    session = await session_backend.start_environment_session(
        request=request,
        session_config=session_config,
        identity_session=identity_session,
    )
    normalized_session = _normalize_session(
        session,
        identity_session=identity_session,
        environment_session_config_id=session_config.environment_session_config_id,
    )
    identity_evidence = await _join_identity_session(
        request_id=request.request_id,
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        environment_session_id=normalized_session.environment_session_id,
        identity_session=identity_session,
        receipt=request.admission_receipt,
        identity_client=identity_client,
        metadata=request.metadata,
        validation_evidence=validation.evidence,
    )
    response = _start_response_from_session(
        request=request,
        actor_id=actor_id,
        session=normalized_session,
        identity_evidence=identity_evidence,
        validation_evidence=validation.evidence,
    )
    default_navigation = await _resolve_default_navigation_context_if_requested(
        requested=request.resolve_default_navigation_context,
        session_backend=session_backend,
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        session=normalized_session,
        session_config=session_config,
        join_receipt=response.join_receipt,
        request_id=request.request_id,
        metadata=request.metadata,
        validation_evidence=validation.evidence,
    )
    return _start_response_with_default_navigation(
        response=response,
        default_navigation=default_navigation,
    )


async def join_environment_session(
    *,
    request: JoinEnvironmentSessionRequestSpec,
    host_context: ServiceApiHostContext,
    session_backend: EnvironmentSessionBackend | None,
    identity_api_client: IdentityEnvironmentSessionApiClient | None = None,
) -> JoinEnvironmentSessionResponseSpec:
    actor_id = request.actor_id or host_context.operation_context.actor_id
    validation = _validate_admission(
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        receipt=request.admission_receipt,
    )
    blocker_response = _blocked_join_for_validation(
        request=request,
        actor_id=actor_id,
        validation=validation,
    )
    if blocker_response is not None:
        return blocker_response

    if session_backend is None:
        return _blocked_join_response(
            request=request,
            actor_id=actor_id,
            reason="environment_session_backend_unavailable",
            blockers=["environment_session_backend_unavailable"],
            evidence=validation.evidence,
        )

    identity_client = identity_api_client or _build_identity_service_api_client(
        host_context=host_context,
    )
    identity_blocker = _identity_client_blocker(identity_client)
    if identity_blocker is not None:
        return _blocked_join_response(
            request=request,
            actor_id=actor_id,
            reason=identity_blocker,
            blockers=[identity_blocker],
            evidence=validation.evidence,
        )
    assert identity_client is not None

    session = await session_backend.describe_environment_session(
        request=DescribeEnvironmentSessionRequestSpec(
            actor_id=actor_id,
            environment_id=request.environment_id,
            environment_session_id=request.environment_session_id,
        )
    )
    if session is None:
        return _blocked_join_response(
            request=request,
            actor_id=actor_id,
            reason="environment_session_not_found",
            blockers=["environment_session_not_found"],
            evidence=validation.evidence,
        )
    normalized_session = _normalize_session(session)
    session_blockers = _session_scope_blockers(
        request_environment_id=request.environment_id,
        request_environment_profile_id=request.environment_profile_id,
        session=normalized_session,
    )
    if session_blockers:
        return _blocked_join_response(
            request=request,
            actor_id=actor_id,
            reason=session_blockers[0],
            blockers=session_blockers,
            evidence=validation.evidence,
        )
    identity_session = normalized_session.identity_session
    if identity_session is None:
        return _blocked_join_response(
            request=request,
            actor_id=actor_id,
            reason="environment_session_identity_session_missing",
            blockers=["environment_session_identity_session_missing"],
            evidence=validation.evidence,
        )

    identity_evidence = await _join_identity_session(
        request_id=request.request_id,
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        environment_session_id=normalized_session.environment_session_id,
        identity_session=identity_session,
        receipt=request.admission_receipt,
        identity_client=identity_client,
        metadata=request.metadata,
        validation_evidence=validation.evidence,
    )
    response = _join_response_from_session(
        request=request,
        actor_id=actor_id,
        session=normalized_session,
        identity_evidence=identity_evidence,
        validation_evidence=validation.evidence,
    )
    session_config = await _describe_session_config_for_session(
        session_backend=session_backend,
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        session=normalized_session,
    )
    default_navigation = await _resolve_default_navigation_context_if_requested(
        requested=request.resolve_default_navigation_context,
        session_backend=session_backend,
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        session=normalized_session,
        session_config=session_config,
        join_receipt=response.receipt,
        request_id=request.request_id,
        metadata=request.metadata,
        validation_evidence=validation.evidence,
    )
    return _join_response_with_default_navigation(
        response=response,
        default_navigation=default_navigation,
    )


async def describe_environment_session(
    *,
    request: DescribeEnvironmentSessionRequestSpec,
    session_backend: EnvironmentSessionBackend | None,
) -> DescribeEnvironmentSessionResponseSpec:
    if session_backend is None:
        return DescribeEnvironmentSessionResponseSpec(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            status="blocked",
            error="environment_session_backend_unavailable",
            evidence={
                "source": "aware_environment_service.session",
                "blocker": "environment_session_backend_unavailable",
            },
        )
    session = await session_backend.describe_environment_session(request=request)
    if session is None:
        return DescribeEnvironmentSessionResponseSpec(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            status="not_found",
            error="environment_session_not_found",
            evidence={
                "source": "aware_environment_service.session",
                "environment_session_id": str(request.environment_session_id),
            },
        )
    normalized = _normalize_session(session)
    return DescribeEnvironmentSessionResponseSpec(
        actor_id=request.actor_id,
        environment_id=request.environment_id,
        status="described",
        session=normalized,
        evidence={
            "source": "aware_environment_service.session",
            "environment_session_id": str(normalized.environment_session_id),
            "identity_session_id": (
                str(normalized.identity_session_id)
                if normalized.identity_session_id is not None
                else None
            ),
        },
    )


async def resolve_environment_session_attention(
    *,
    request: ResolveEnvironmentSessionAttentionRequestSpec,
    host_context: ServiceApiHostContext,
    session_backend: EnvironmentSessionBackend | None,
    attention_resolution_backend: EnvironmentSessionAttentionBackend | None = None,
    attention_api_client: AttentionEnvironmentSessionApiClient | None = None,
) -> ResolveEnvironmentSessionAttentionResponseSpec:
    actor_id = request.actor_id or host_context.operation_context.actor_id
    resolution_backend = attention_resolution_backend or session_backend
    if resolution_backend is None:
        return _blocked_attention_resolution_response(
            request=request,
            actor_id=actor_id,
            reason="environment_session_attention_backend_unavailable",
            blockers=["environment_session_attention_backend_unavailable"],
        )
    resolve_backend = getattr(
        resolution_backend,
        "resolve_environment_session_attention",
        None,
    )
    if resolve_backend is None:
        return _blocked_attention_resolution_response(
            request=request,
            actor_id=actor_id,
            reason="environment_session_attention_backend_unavailable",
            blockers=["environment_session_attention_backend_unavailable"],
        )

    scoped_request = request.model_copy(update={"actor_id": actor_id})
    resolution = await resolve_backend(request=scoped_request)
    if resolution is None:
        return _blocked_attention_resolution_response(
            request=request,
            actor_id=actor_id,
            reason="environment_session_attention_not_found",
            blockers=["environment_session_attention_not_found"],
        )
    resolution = _normalize_attention_resolution(resolution)
    if resolution.status == "blocked" or resolution.blockers:
        blockers = list(resolution.blockers) or ["environment_session_attention_blocked"]
        return _attention_resolution_response_from_resolution(
            request=request,
            actor_id=actor_id,
            status="blocked",
            error=blockers[0],
            resolution=_resolution_with_blockers(
                resolution,
                blockers=blockers,
                status="blocked",
            ),
        )
    scope_blockers = _attention_resolution_scope_blockers(
        request=request,
        resolution=resolution,
    )
    if scope_blockers:
        return _attention_resolution_response_from_resolution(
            request=request,
            actor_id=actor_id,
            status="blocked",
            error=scope_blockers[0],
            resolution=_resolution_with_blockers(
                resolution,
                blockers=scope_blockers,
                status="blocked",
            ),
        )

    attention_client = attention_api_client or _build_attention_service_api_client(
        host_context=host_context,
    )
    attention_blocker = _attention_client_blocker(attention_client)
    if attention_blocker is not None:
        return _attention_resolution_response_from_resolution(
            request=request,
            actor_id=actor_id,
            status="blocked",
            error=attention_blocker,
            resolution=_resolution_with_blockers(
                resolution,
                blockers=[attention_blocker],
                status="blocked",
            ),
        )
    assert attention_client is not None

    attention_session = None
    active_transition = None
    validation = None
    transitions: list[AttentionFocusTransitionPin] = []
    attention_api = attention_client.attention
    if resolution.attention_session_id is not None:
        session_response = (
            await attention_api.describe_attention_session.describe_attention_session(
                DescribeAttentionSessionRequest(
                    request_id=request.request_id,
                    attention_session_id=resolution.attention_session_id,
                    identity_session_id=resolution.identity_session_id,
                )
            )
        )
        if session_response.session is None:
            reason = session_response.info or "attention_session_not_found"
            return _attention_resolution_response_from_resolution(
                request=request,
                actor_id=actor_id,
                status="blocked",
                error=reason,
                resolution=_resolution_with_blockers(
                    resolution,
                    blockers=[reason],
                    status="blocked",
                ),
                evidence={"attention_info": session_response.info},
            )
        attention_session = session_response.session
        active_transition = session_response.active_transition

    transition_id = request.attention_focus_transition_id
    if transition_id is None and active_transition is not None:
        transition_id = active_transition.attention_focus_transition_id
    if transition_id is not None:
        validation_response = (
            await attention_api.validate_attention_transition.validate_attention_transition(
                ValidateAttentionTransitionRequest(
                    request_id=request.request_id,
                    attention_focus_transition_id=transition_id,
                    expected_identity_session_id=resolution.identity_session_id,
                    expected_attention_session_id=resolution.attention_session_id,
                    expected_attention_session_section_id=(
                        request.expected_attention_session_section_id
                    ),
                    expected_focus_scope_id=request.expected_focus_scope_id,
                    expected_object_instance_graph_commit_id=(
                        request.expected_object_instance_graph_commit_id
                    ),
                    expected_projection_hash=request.expected_projection_hash,
                )
            )
        )
        validation = validation_response.validation
        if validation.transition is not None:
            active_transition = validation.transition

    if request.include_transition_list and resolution.attention_session_id is not None:
        list_response = (
            await attention_api.list_attention_transitions.list_attention_transitions(
                ListAttentionTransitionsRequest(
                    request_id=request.request_id,
                    attention_session_id=resolution.attention_session_id,
                    limit=request.transition_limit,
                )
            )
        )
        transitions = list(list_response.transitions)

    validation_blockers = (
        list(validation.failure_reasons)
        if validation is not None and not validation.valid
        else []
    )
    status = "resolved" if not validation_blockers else "invalid_attention_transition"
    return _attention_resolution_response_from_resolution(
        request=request,
        actor_id=actor_id,
        status=status,
        error=validation_blockers[0] if validation_blockers else None,
        resolution=resolution.model_copy(
            update={
                "attention_session": (
                    attention_session if request.include_attention_session else None
                ),
                "active_transition": active_transition,
                "validation": validation,
                "transitions": transitions,
                "status": status,
                "blockers": validation_blockers,
                "evidence": {
                    **resolution.evidence,
                    "source": "aware_environment_service.session_attention",
                    "request_branch_id": (
                        str(request.branch_id) if request.branch_id is not None else None
                    ),
                    "request_projection_hash": request.projection_hash,
                    "attention_session_described": attention_session is not None,
                    "attention_transition_validated": validation is not None,
                },
            }
        ),
    )


class _AdmissionValidation(BaseModel):
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


def _validate_admission(
    *,
    actor_id: UUID | None,
    environment_id: UUID,
    environment_profile_id: UUID,
    receipt: EnvironmentActorAdmissionReceiptSpec,
) -> _AdmissionValidation:
    evidence: dict[str, Any] = {
        "source": "aware_environment_service.session",
        "admission_status": receipt.status,
        "admission_binding_count": len(receipt.bindings),
    }
    blockers: list[str] = []
    if actor_id is None:
        blockers.append("actor_id_missing")
    if not receipt.accepted:
        blockers.append(receipt.error or "environment_admission_not_accepted")
    if receipt.actor_id is None:
        blockers.append("environment_admission_actor_id_missing")
    elif actor_id is not None and receipt.actor_id != actor_id:
        blockers.append("environment_admission_actor_mismatch")
    if receipt.environment_id != environment_id:
        blockers.append("environment_admission_environment_mismatch")
    if receipt.environment_profile_id != environment_profile_id:
        blockers.append("environment_admission_profile_mismatch")
    if receipt.actor_config_id is None:
        blockers.append("environment_admission_actor_config_missing")
    if not receipt.bindings:
        blockers.append("environment_admission_bindings_missing")
    if any(binding.actor_id != receipt.actor_id for binding in receipt.bindings):
        blockers.append("environment_admission_binding_actor_mismatch")
    if blockers:
        evidence["blockers"] = list(dict.fromkeys(blockers))
    return _AdmissionValidation(
        blockers=list(dict.fromkeys(blockers)),
        evidence=evidence,
    )


def _blocked_start_for_validation(
    *,
    request: StartEnvironmentSessionRequestSpec,
    actor_id: UUID | None,
    validation: _AdmissionValidation,
) -> StartEnvironmentSessionResponseSpec | None:
    if not validation.blockers:
        return None
    return _blocked_start_response(
        request=request,
        actor_id=actor_id,
        reason=validation.blockers[0],
        blockers=validation.blockers,
        evidence=validation.evidence,
    )


def _blocked_join_for_validation(
    *,
    request: JoinEnvironmentSessionRequestSpec,
    actor_id: UUID | None,
    validation: _AdmissionValidation,
) -> JoinEnvironmentSessionResponseSpec | None:
    if not validation.blockers:
        return None
    return _blocked_join_response(
        request=request,
        actor_id=actor_id,
        reason=validation.blockers[0],
        blockers=validation.blockers,
        evidence=validation.evidence,
    )


def _blocked_start_response(
    *,
    request: StartEnvironmentSessionRequestSpec,
    actor_id: UUID | None,
    reason: str,
    blockers: list[str],
    evidence: Mapping[str, Any],
) -> StartEnvironmentSessionResponseSpec:
    receipt = _blocked_join_receipt(
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        status="blocked",
        reason=reason,
        blockers=blockers,
        evidence=evidence,
    )
    return StartEnvironmentSessionResponseSpec(
        request_id=request.request_id,
        actor_id=actor_id,
        environment_id=request.environment_id,
        accepted=False,
        status="blocked",
        error=receipt.error,
        join_receipt=receipt,
        evidence=dict(receipt.evidence),
    )


def _blocked_join_response(
    *,
    request: JoinEnvironmentSessionRequestSpec,
    actor_id: UUID | None,
    reason: str,
    blockers: list[str],
    evidence: Mapping[str, Any],
) -> JoinEnvironmentSessionResponseSpec:
    receipt = _blocked_join_receipt(
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        environment_session_id=request.environment_session_id,
        status="blocked",
        reason=reason,
        blockers=blockers,
        evidence=evidence,
    )
    return JoinEnvironmentSessionResponseSpec(
        request_id=request.request_id,
        actor_id=actor_id,
        environment_id=request.environment_id,
        accepted=False,
        status="blocked",
        error=receipt.error,
        receipt=receipt,
        evidence=dict(receipt.evidence),
    )


def _blocked_join_receipt(
    *,
    actor_id: UUID | None,
    environment_id: UUID,
    environment_profile_id: UUID,
    status: str,
    reason: str,
    blockers: list[str],
    evidence: Mapping[str, Any],
    environment_session_id: UUID | None = None,
    environment_session_key: str | None = None,
) -> EnvironmentSessionJoinReceiptSpec:
    return EnvironmentSessionJoinReceiptSpec(
        accepted=False,
        status=status,
        error=reason,
        reason=reason,
        actor_id=actor_id,
        environment_id=environment_id,
        environment_profile_id=environment_profile_id,
        environment_session_id=environment_session_id,
        environment_session_key=environment_session_key,
        blockers=blockers,
        evidence=dict(evidence),
    )


def _session_config_blockers(
    *,
    request_environment_id: UUID,
    request_environment_profile_id: UUID,
    session_config: EnvironmentSessionConfigViewSpec | None,
) -> list[str]:
    blockers: list[str] = []
    if session_config is None:
        return ["environment_session_config_not_found"]
    if session_config.environment_id != request_environment_id:
        blockers.append("environment_session_config_environment_mismatch")
    if session_config.environment_profile_id != request_environment_profile_id:
        blockers.append("environment_session_config_profile_mismatch")
    return blockers


def _session_scope_blockers(
    *,
    request_environment_id: UUID,
    request_environment_profile_id: UUID,
    session: EnvironmentSessionViewSpec,
) -> list[str]:
    blockers: list[str] = []
    if session.environment_id != request_environment_id:
        blockers.append("environment_session_environment_mismatch")
    if session.environment_profile_id != request_environment_profile_id:
        blockers.append("environment_session_profile_mismatch")
    return blockers


def _attention_resolution_scope_blockers(
    *,
    request: ResolveEnvironmentSessionAttentionRequestSpec,
    resolution: EnvironmentSessionAttentionResolutionSpec,
) -> list[str]:
    blockers: list[str] = []
    if request.environment_id != resolution.environment_id:
        blockers.append("environment_session_attention_environment_mismatch")
    if request.environment_session_id != resolution.environment_session_id:
        blockers.append("environment_session_attention_session_mismatch")
    if (
        request.environment_navigation_context_id is not None
        and resolution.environment_navigation_context_id
        != request.environment_navigation_context_id
    ):
        blockers.append("environment_navigation_context_mismatch")
    if (
        request.environment_session_thread_id is not None
        and resolution.environment_session_thread_id
        != request.environment_session_thread_id
    ):
        blockers.append("environment_session_thread_mismatch")
    if (
        request.environment_session_attention_session_id is not None
        and resolution.environment_session_attention_session_id
        != request.environment_session_attention_session_id
    ):
        blockers.append("environment_session_attention_session_mismatch")
    if resolution.attention_session_id is None:
        blockers.append("environment_session_attention_session_missing")
    if (
        request.expected_attention_session_id is not None
        and resolution.attention_session_id != request.expected_attention_session_id
    ):
        blockers.append("attention_session_mismatch")
    if request.transition_limit is not None and request.transition_limit < 0:
        blockers.append("attention_transition_limit_invalid")
    return list(dict.fromkeys(blockers))


def _normalize_attention_resolution(
    resolution: EnvironmentSessionAttentionResolutionSpec,
) -> EnvironmentSessionAttentionResolutionSpec:
    return EnvironmentSessionAttentionResolutionSpec.model_validate(
        resolution.model_dump(mode="python")
    )


def _resolution_with_blockers(
    resolution: EnvironmentSessionAttentionResolutionSpec,
    *,
    blockers: list[str],
    status: str,
) -> EnvironmentSessionAttentionResolutionSpec:
    return resolution.model_copy(
        update={
            "status": status,
            "blockers": list(dict.fromkeys([*resolution.blockers, *blockers])),
            "evidence": {
                **resolution.evidence,
                "source": "aware_environment_service.session_attention",
                "blockers": list(dict.fromkeys(blockers)),
            },
        }
    )


def _blocked_attention_resolution_response(
    *,
    request: ResolveEnvironmentSessionAttentionRequestSpec,
    actor_id: UUID | None,
    reason: str,
    blockers: list[str],
    evidence: Mapping[str, Any] | None = None,
) -> ResolveEnvironmentSessionAttentionResponseSpec:
    return ResolveEnvironmentSessionAttentionResponseSpec(
        request_id=request.request_id,
        actor_id=actor_id,
        environment_id=request.environment_id,
        status="blocked",
        error=reason,
        resolution=None,
        evidence={
            "source": "aware_environment_service.session_attention",
            "blockers": list(dict.fromkeys(blockers)),
            **dict(evidence or {}),
        },
    )


def _attention_resolution_response_from_resolution(
    *,
    request: ResolveEnvironmentSessionAttentionRequestSpec,
    actor_id: UUID | None,
    status: str,
    error: str | None,
    resolution: EnvironmentSessionAttentionResolutionSpec,
    evidence: Mapping[str, Any] | None = None,
) -> ResolveEnvironmentSessionAttentionResponseSpec:
    return ResolveEnvironmentSessionAttentionResponseSpec(
        request_id=request.request_id,
        actor_id=actor_id,
        environment_id=request.environment_id,
        status=status,
        error=error,
        resolution=resolution,
        evidence={
            "source": "aware_environment_service.session_attention",
            "environment_session_id": str(request.environment_session_id),
            **dict(evidence or {}),
        },
    )


async def _start_identity_session(
    *,
    request: StartEnvironmentSessionRequestSpec,
    actor_id: UUID | None,
    identity_client: IdentityEnvironmentSessionApiClient,
    session_config: EnvironmentSessionConfigViewSpec,
) -> SessionSummary:
    receipt = await identity_client.identity.start_session.start_session(
        SessionStartRequest(
            session_config_id=session_config.identity_session_config_id,
            key=request.session_key,
            title=request.title or session_config.title,
            description=request.description or session_config.description,
            purpose=request.purpose or session_config.purpose,
            created_by_actor_id=actor_id,
            source_kind=request.source_kind or "environment_session",
            source_ref=(
                request.source_ref or str(session_config.environment_session_config_id)
            ),
            metadata_json=_json_object(request.metadata),
            request_id=request.request_id,
        )
    )
    return receipt.session


async def _join_identity_session(
    *,
    request_id: UUID | None,
    actor_id: UUID | None,
    environment_id: UUID,
    environment_profile_id: UUID,
    environment_session_id: UUID,
    identity_session: SessionSummary,
    receipt: EnvironmentActorAdmissionReceiptSpec,
    identity_client: IdentityEnvironmentSessionApiClient,
    metadata: Mapping[str, Any],
    validation_evidence: Mapping[str, Any],
) -> EnvironmentSessionIdentityEvidenceSpec:
    assert actor_id is not None
    assert receipt.actor_config_id is not None
    binding_receipt = await identity_client.identity.bind_session_config_actor_config.bind_session_config_actor_config(
        SessionConfigActorConfigBindRequest(
            session_config_id=identity_session.session_config_id,
            actor_config_id=receipt.actor_config_id,
            purpose="environment_session_participant",
            metadata_json=_json_object(
                {
                    **dict(metadata),
                    "environment_id": str(environment_id),
                    "environment_profile_id": str(environment_profile_id),
                }
            ),
            request_id=request_id,
        )
    )
    join_receipt = await identity_client.identity.join_session.join_session(
        SessionJoinRequest(
            session_id=identity_session.session_id,
            actor_id=actor_id,
            session_actor_config_id=(
                binding_receipt.binding.session_config_actor_config_id
            ),
            metadata_json=_json_object(
                {
                    **dict(metadata),
                    "environment_id": str(environment_id),
                    "environment_profile_id": str(environment_profile_id),
                    "environment_session_id": str(environment_session_id),
                }
            ),
            request_id=request_id,
        )
    )
    actor_roles: list[SessionMemberActorRoleSummary] = []
    for admission_binding in receipt.bindings:
        actor_role_receipt = await identity_client.identity.record_session_member_actor_role.record_session_member_actor_role(
            SessionMemberActorRoleRecordRequest(
                session_id=identity_session.session_id,
                session_member_id=join_receipt.member.session_member_id,
                actor_role_id=admission_binding.actor_role_id,
                source_kind="environment_admission",
                evidence_json=_json_object(
                    {
                        **dict(validation_evidence),
                        "environment_id": str(environment_id),
                        "environment_profile_id": str(environment_profile_id),
                        "environment_session_id": str(environment_session_id),
                        "role_config_id": str(admission_binding.role_config_id),
                    }
                ),
                request_id=request_id,
            )
        )
        actor_roles.append(actor_role_receipt.actor_role)
    member = join_receipt.member.model_copy(update={"actor_roles": actor_roles})
    return EnvironmentSessionIdentityEvidenceSpec(
        identity_session=identity_session.model_copy(
            update={"member_count": max(identity_session.member_count, 1)}
        ),
        identity_member=member,
        identity_actor_roles=actor_roles,
        evidence={
            **dict(validation_evidence),
            "identity_session_id": str(identity_session.session_id),
            "identity_session_member_id": str(member.session_member_id),
            "identity_actor_role_count": len(actor_roles),
        },
    )


def _start_response_from_session(
    *,
    request: StartEnvironmentSessionRequestSpec,
    actor_id: UUID | None,
    session: EnvironmentSessionViewSpec,
    identity_evidence: EnvironmentSessionIdentityEvidenceSpec,
    validation_evidence: Mapping[str, Any],
) -> StartEnvironmentSessionResponseSpec:
    receipt = EnvironmentSessionJoinReceiptSpec(
        accepted=True,
        status="joined",
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        environment_session_id=session.environment_session_id,
        environment_session_key=session.session_key,
        identity_evidence=identity_evidence,
        evidence={
            **dict(validation_evidence),
            "environment_session_id": str(session.environment_session_id),
            "environment_session_key": session.session_key,
            "identity_session_id": (
                str(session.identity_session_id)
                if session.identity_session_id is not None
                else None
            ),
        },
    )
    return StartEnvironmentSessionResponseSpec(
        request_id=request.request_id,
        actor_id=actor_id,
        environment_id=request.environment_id,
        accepted=True,
        status="started",
        session=session,
        join_receipt=receipt,
        evidence=dict(receipt.evidence),
    )


def _join_response_from_session(
    *,
    request: JoinEnvironmentSessionRequestSpec,
    actor_id: UUID | None,
    session: EnvironmentSessionViewSpec,
    identity_evidence: EnvironmentSessionIdentityEvidenceSpec,
    validation_evidence: Mapping[str, Any],
) -> JoinEnvironmentSessionResponseSpec:
    receipt = EnvironmentSessionJoinReceiptSpec(
        accepted=True,
        status="joined",
        reason=request.reason,
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_profile_id=request.environment_profile_id,
        environment_session_id=session.environment_session_id,
        environment_session_key=session.session_key,
        identity_evidence=identity_evidence,
        evidence={
            **dict(validation_evidence),
            "environment_session_id": str(session.environment_session_id),
            "environment_session_key": session.session_key,
            "identity_session_id": (
                str(session.identity_session_id)
                if session.identity_session_id is not None
                else None
            ),
        },
    )
    return JoinEnvironmentSessionResponseSpec(
        request_id=request.request_id,
        actor_id=actor_id,
        environment_id=request.environment_id,
        accepted=True,
        status="joined",
        session=session,
        receipt=receipt,
        evidence=dict(receipt.evidence),
    )


async def _describe_session_config_for_session(
    *,
    session_backend: EnvironmentSessionBackend,
    environment_id: UUID,
    environment_profile_id: UUID,
    session: EnvironmentSessionViewSpec,
) -> EnvironmentSessionConfigViewSpec | None:
    if session.environment_session_config_id is None:
        return None
    return await session_backend.describe_environment_session_config(
        environment_id=environment_id,
        environment_profile_id=environment_profile_id,
        environment_session_config_id=session.environment_session_config_id,
    )


async def _resolve_default_navigation_context_if_requested(
    *,
    requested: bool,
    session_backend: EnvironmentSessionBackend,
    actor_id: UUID | None,
    environment_id: UUID,
    environment_profile_id: UUID,
    session: EnvironmentSessionViewSpec,
    session_config: EnvironmentSessionConfigViewSpec | None,
    join_receipt: EnvironmentSessionJoinReceiptSpec,
    request_id: UUID | None,
    metadata: Mapping[str, Any],
    validation_evidence: Mapping[str, Any],
) -> EnvironmentDefaultNavigationContextResolutionSpec | None:
    if not requested:
        return None
    resolver = getattr(session_backend, "ensure_default_navigation_context", None)
    if resolver is None:
        reason = "environment_default_navigation_backend_unavailable"
        return EnvironmentDefaultNavigationContextResolutionSpec(
            receipt=_blocked_default_navigation_receipt(
                actor_id=actor_id,
                environment_id=environment_id,
                environment_session_id=session.environment_session_id,
                reason=reason,
                evidence=validation_evidence,
            )
        )
    return await cast(
        _EnvironmentDefaultNavigationResolver,
        session_backend,
    ).ensure_default_navigation_context(
        actor_id=actor_id,
        environment_id=environment_id,
        environment_profile_id=environment_profile_id,
        session=session,
        session_config=session_config,
        join_receipt=join_receipt,
        request_id=request_id,
        metadata=metadata,
    )


def _blocked_default_navigation_receipt(
    *,
    actor_id: UUID | None,
    environment_id: UUID,
    environment_session_id: UUID,
    reason: str,
    evidence: Mapping[str, Any],
) -> EnvironmentNavigationCommitReceiptSpec:
    return EnvironmentNavigationCommitReceiptSpec(
        accepted=False,
        status="blocked",
        error=reason,
        reason=reason,
        actor_id=actor_id,
        environment_id=environment_id,
        environment_session_id=environment_session_id,
        key="default",
        is_default=True,
        blockers=[reason],
        evidence={
            **dict(evidence),
            "source": "aware_environment_service.session",
            "environment_session_id": str(environment_session_id),
            "default_navigation_context_requested": True,
        },
    )


def _start_response_with_default_navigation(
    *,
    response: StartEnvironmentSessionResponseSpec,
    default_navigation: EnvironmentDefaultNavigationContextResolutionSpec | None,
) -> StartEnvironmentSessionResponseSpec:
    if default_navigation is None:
        return response
    return response.model_copy(
        update={
            "default_navigation_context": default_navigation.context,
            "default_navigation_receipt": default_navigation.receipt,
            "evidence": _evidence_with_default_navigation(
                response.evidence,
                default_navigation=default_navigation,
            ),
        }
    )


def _join_response_with_default_navigation(
    *,
    response: JoinEnvironmentSessionResponseSpec,
    default_navigation: EnvironmentDefaultNavigationContextResolutionSpec | None,
) -> JoinEnvironmentSessionResponseSpec:
    if default_navigation is None:
        return response
    return response.model_copy(
        update={
            "default_navigation_context": default_navigation.context,
            "default_navigation_receipt": default_navigation.receipt,
            "evidence": _evidence_with_default_navigation(
                response.evidence,
                default_navigation=default_navigation,
            ),
        }
    )


def _evidence_with_default_navigation(
    evidence: Mapping[str, Any],
    *,
    default_navigation: EnvironmentDefaultNavigationContextResolutionSpec,
) -> dict[str, Any]:
    receipt = default_navigation.receipt
    return {
        **dict(evidence),
        "default_navigation_context_requested": True,
        "default_navigation_context_id": (
            str(default_navigation.context.environment_navigation_context_id)
            if default_navigation.context is not None
            else None
        ),
        "default_navigation_status": receipt.status if receipt is not None else None,
        "default_navigation_error": receipt.error if receipt is not None else None,
    }


def _normalize_session(
    session: EnvironmentSessionViewSpec,
    *,
    identity_session: SessionSummary | None = None,
    environment_session_config_id: UUID | None = None,
) -> EnvironmentSessionViewSpec:
    resolved_identity_session = identity_session or session.identity_session
    resolved_identity_session_id = (
        resolved_identity_session.session_id
        if resolved_identity_session is not None
        else session.identity_session_id
    )
    return session.model_copy(
        update={
            "environment_session_config_id": (
                environment_session_config_id or session.environment_session_config_id
            ),
            "identity_session_id": resolved_identity_session_id,
            "identity_session": resolved_identity_session,
        }
    )


def _identity_client_blocker(
    identity_client: IdentityEnvironmentSessionApiClient | None,
) -> str | None:
    if identity_client is None:
        return "identity_session_api_route_unavailable"
    identity_api = getattr(identity_client, "identity", None)
    if identity_api is None:
        return "identity_session_api_route_unavailable"
    for capability_name in (
        "bind_session_config_actor_config",
        "start_session",
        "join_session",
        "record_session_member_actor_role",
    ):
        if getattr(identity_api, capability_name, None) is None:
            return f"identity_{capability_name}_capability_unavailable"
    return None


def _attention_client_blocker(
    attention_client: AttentionEnvironmentSessionApiClient | None,
) -> str | None:
    if attention_client is None:
        return "attention_session_api_route_unavailable"
    attention_api = getattr(attention_client, "attention", None)
    if attention_api is None:
        return "attention_session_api_route_unavailable"
    for capability_name in (
        "describe_attention_session",
        "list_attention_transitions",
        "validate_attention_transition",
    ):
        if getattr(attention_api, capability_name, None) is None:
            return f"attention_{capability_name}_capability_unavailable"
    return None


def _build_identity_service_api_client(
    *,
    host_context: ServiceApiHostContext,
) -> IdentityEnvironmentSessionApiClient | None:
    invoker = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name=_IDENTITY_SERVICE_API_PACKAGE_NAME,
        actor_id=host_context.operation_context.actor_id,
        invocation_context=_host_invocation_context_payload(host_context),
    )
    if invoker is None:
        return None
    return cast(
        IdentityEnvironmentSessionApiClient,
        _identity_api_client_model()(invoker),
    )


def _build_attention_service_api_client(
    *,
    host_context: ServiceApiHostContext,
) -> AttentionEnvironmentSessionApiClient | None:
    invoker = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name=_ATTENTION_SERVICE_API_PACKAGE_NAME,
        actor_id=host_context.operation_context.actor_id,
        invocation_context=_host_invocation_context_payload(host_context),
    )
    if invoker is None:
        return None
    return cast(
        AttentionEnvironmentSessionApiClient,
        _attention_api_client_model()(invoker),
    )


def _identity_api_client_model() -> type[Any]:
    module = import_module("aware_" + "identity" + "_service_api")
    return cast(type[Any], getattr(module, "AwareIdentityServiceApiClient"))


def _attention_api_client_model() -> type[Any]:
    module = import_module("aware_" + "attention" + "_service_api")
    return cast(type[Any], getattr(module, "AwareAttentionServiceApiClient"))


def _host_invocation_context_payload(
    host_context: ServiceApiHostContext,
) -> JsonObject | None:
    if host_context.invocation_context is None:
        return None
    return _json_object(host_context.invocation_context)


__all__ = [
    "AttentionEnvironmentSessionApiClient",
    "DescribeEnvironmentSessionRequestSpec",
    "DescribeEnvironmentSessionResponseSpec",
    "EnvironmentSessionBackend",
    "EnvironmentSessionAttentionBackend",
    "EnvironmentSessionAttentionResolutionSpec",
    "EnvironmentSessionConfigViewSpec",
    "EnvironmentSessionIdentityEvidenceSpec",
    "EnvironmentSessionJoinReceiptSpec",
    "EnvironmentSessionViewSpec",
    "IdentityEnvironmentSessionApiClient",
    "JoinEnvironmentSessionRequestSpec",
    "JoinEnvironmentSessionResponseSpec",
    "ResolveEnvironmentSessionAttentionRequestSpec",
    "ResolveEnvironmentSessionAttentionResponseSpec",
    "StartEnvironmentSessionRequestSpec",
    "StartEnvironmentSessionResponseSpec",
    "describe_environment_session",
    "join_environment_session",
    "resolve_environment_session_attention",
    "start_environment_session",
]
