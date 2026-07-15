from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol, cast
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentSessionRequest,
    DescribeEnvironmentSessionResponse,
    EnvironmentActorAdmissionReceipt as DtoEnvironmentActorAdmissionReceipt,
    EnvironmentNavigationCommitReceipt as DtoEnvironmentNavigationCommitReceipt,
    EnvironmentNavigationContextView as DtoEnvironmentNavigationContextView,
    EnvironmentSessionAttentionResolution as DtoEnvironmentSessionAttentionResolution,
    EnvironmentSessionIdentityEvidence as DtoEnvironmentSessionIdentityEvidence,
    EnvironmentSessionJoinReceipt as DtoEnvironmentSessionJoinReceipt,
    EnvironmentSessionView as DtoEnvironmentSessionView,
    JoinEnvironmentSessionRequest,
    JoinEnvironmentSessionResponse,
    MountEnvironmentSessionAttentionRequest,
    MountEnvironmentSessionAttentionResponse,
    ResolveEnvironmentSessionAttentionRequest,
    ResolveEnvironmentSessionAttentionResponse,
    StartEnvironmentSessionRequest,
    StartEnvironmentSessionResponse,
)
from aware_environment_sdk.admission import (
    EnvironmentActorAdmissionReceipt as SdkEnvironmentActorAdmissionReceipt,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionFocusTransitionPin,
    AttentionSessionPin,
    AttentionTransitionValidationResult,
)
from aware_identity_service_dto.session.session import (
    SessionMemberActorRoleSummary,
    SessionMemberSummary,
    SessionSummary,
)
from aware_types import JsonObject


class EnvironmentSessionError(RuntimeError):
    """Raised when Environment session start/join/describe fails closed."""

    def __init__(
        self,
        message: str,
        *,
        receipt: "EnvironmentSessionJoinReceipt | None" = None,
    ) -> None:
        super().__init__(message)
        self.receipt = receipt


class _EnvironmentSessionCapabilityClient(Protocol):
    async def start_session(
        self,
        request: StartEnvironmentSessionRequest,
    ) -> StartEnvironmentSessionResponse: ...

    async def join_session(
        self,
        request: JoinEnvironmentSessionRequest,
    ) -> JoinEnvironmentSessionResponse: ...

    async def describe_session(
        self,
        request: DescribeEnvironmentSessionRequest,
    ) -> DescribeEnvironmentSessionResponse: ...

    async def resolve_attention(
        self,
        request: ResolveEnvironmentSessionAttentionRequest,
    ) -> ResolveEnvironmentSessionAttentionResponse: ...

    async def mount_attention_session(
        self,
        request: MountEnvironmentSessionAttentionRequest,
    ) -> MountEnvironmentSessionAttentionResponse: ...


class _EnvironmentApiClient(Protocol):
    @property
    def session(self) -> _EnvironmentSessionCapabilityClient: ...


class EnvironmentSessionGeneratedApiClient(Protocol):
    @property
    def environment(self) -> _EnvironmentApiClient: ...


@dataclass(frozen=True, slots=True)
class EnvironmentSessionContext:
    actor_id: UUID
    environment_id: UUID

    @classmethod
    def from_object(cls, context: object) -> "EnvironmentSessionContext":
        return cls(
            actor_id=_required_uuid(
                getattr(context, "actor_id", None),
                field_name="actor_id",
            ),
            environment_id=_required_uuid(
                getattr(context, "environment_id", None),
                field_name="environment_id",
            ),
        )


@dataclass(frozen=True, slots=True)
class EnvironmentSessionIdentityEvidence:
    identity_session: SessionSummary | None
    identity_member: SessionMemberSummary | None
    identity_actor_roles: tuple[SessionMemberActorRoleSummary, ...]
    evidence: Mapping[str, object] = field(default_factory=dict)
    dto_evidence: DtoEnvironmentSessionIdentityEvidence | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentSession:
    environment_session_id: UUID
    environment_session_config_id: UUID | None
    identity_session_id: UUID | None
    identity_session: SessionSummary | None
    environment_id: UUID
    environment_profile_id: UUID
    session_key: str
    title: str | None
    description: str | None
    purpose: str | None
    status: str
    created_by_actor_id: UUID | None
    source_kind: str | None
    source_ref: str | None
    evidence: Mapping[str, object] = field(default_factory=dict)
    dto_session: DtoEnvironmentSessionView | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentSessionJoinReceipt:
    accepted: bool
    status: str
    error: str | None
    reason: str | None
    actor_id: UUID | None
    environment_id: UUID
    environment_profile_id: UUID
    environment_session_id: UUID | None
    environment_session_key: str | None
    identity_evidence: EnvironmentSessionIdentityEvidence | None
    blockers: tuple[str, ...]
    evidence: Mapping[str, object] = field(default_factory=dict)
    dto_receipt: DtoEnvironmentSessionJoinReceipt | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentSessionStartResult:
    accepted: bool
    status: str
    error: str | None
    session: EnvironmentSession | None
    join_receipt: EnvironmentSessionJoinReceipt
    default_navigation_context: DtoEnvironmentNavigationContextView | None
    default_navigation_receipt: DtoEnvironmentNavigationCommitReceipt | None
    evidence: Mapping[str, object] = field(default_factory=dict)
    raw_response: StartEnvironmentSessionResponse | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentSessionJoinResult:
    accepted: bool
    status: str
    error: str | None
    session: EnvironmentSession | None
    receipt: EnvironmentSessionJoinReceipt
    default_navigation_context: DtoEnvironmentNavigationContextView | None
    default_navigation_receipt: DtoEnvironmentNavigationCommitReceipt | None
    evidence: Mapping[str, object] = field(default_factory=dict)
    raw_response: JoinEnvironmentSessionResponse | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentSessionDescribeResult:
    status: str
    error: str | None
    session: EnvironmentSession | None
    evidence: Mapping[str, object] = field(default_factory=dict)
    raw_response: DescribeEnvironmentSessionResponse | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentSessionAttentionResolution:
    environment_session_id: UUID
    environment_navigation_context_id: UUID | None
    environment_session_thread_id: UUID | None
    environment_session_attention_session_id: UUID | None
    environment_id: UUID
    environment_profile_id: UUID | None
    thread_id: UUID | None
    thread_layout_id: UUID | None
    attention_session_id: UUID | None
    identity_session_id: UUID | None
    attention_session: AttentionSessionPin | None
    active_transition: AttentionFocusTransitionPin | None
    validation: AttentionTransitionValidationResult | None
    transitions: tuple[AttentionFocusTransitionPin, ...]
    status: str
    blockers: tuple[str, ...]
    evidence: Mapping[str, object] = field(default_factory=dict)
    dto_resolution: DtoEnvironmentSessionAttentionResolution | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentSessionAttentionResolveResult:
    status: str
    error: str | None
    resolution: EnvironmentSessionAttentionResolution | None
    evidence: Mapping[str, object] = field(default_factory=dict)
    raw_response: ResolveEnvironmentSessionAttentionResponse | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentSessionAttentionMountResult:
    environment_session_attention_session_id: UUID
    environment_session_id: UUID
    attention_session_id: UUID
    status: str
    domain_commit_id: UUID | None
    object_instance_graph_commit_id: UUID
    graph_hash_post: str
    raw_response: MountEnvironmentSessionAttentionResponse


@dataclass(frozen=True, slots=True)
class EnvironmentSessionClient:
    api_client: EnvironmentSessionGeneratedApiClient
    context: EnvironmentSessionContext

    async def start_session(
        self,
        *,
        environment_profile_id: UUID | str,
        environment_session_config_id: UUID | str,
        admission_receipt: object,
        session_key: str,
        request_id: UUID | str | None = None,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        source_kind: str | None = None,
        source_ref: str | None = None,
        resolve_default_navigation_context: bool = False,
        metadata: Mapping[str, object] | None = None,
    ) -> EnvironmentSessionStartResult:
        response = await self.api_client.environment.session.start_session(
            StartEnvironmentSessionRequest(
                actor_id=self.context.actor_id,
                environment_id=self.context.environment_id,
                request_id=_optional_uuid(request_id),
                environment_profile_id=_required_uuid(
                    environment_profile_id,
                    field_name="environment_profile_id",
                ),
                environment_session_config_id=_required_uuid(
                    environment_session_config_id,
                    field_name="environment_session_config_id",
                ),
                admission_receipt=_dto_admission_receipt(admission_receipt),
                session_key=session_key,
                title=title,
                description=description,
                purpose=purpose,
                source_kind=source_kind,
                source_ref=source_ref,
                resolve_default_navigation_context=(resolve_default_navigation_context),
                metadata=cast(JsonObject, dict(metadata or {})),
            )
        )
        result = _start_result_from_response(response)
        if not result.accepted:
            raise EnvironmentSessionError(
                f"Environment session start failed: {result.error or result.status}",
                receipt=result.join_receipt,
            )
        return result

    async def join_session(
        self,
        *,
        environment_profile_id: UUID | str,
        environment_session_id: UUID | str,
        admission_receipt: object,
        request_id: UUID | str | None = None,
        reason: str | None = None,
        resolve_default_navigation_context: bool = False,
        metadata: Mapping[str, object] | None = None,
    ) -> EnvironmentSessionJoinResult:
        response = await self.api_client.environment.session.join_session(
            JoinEnvironmentSessionRequest(
                actor_id=self.context.actor_id,
                environment_id=self.context.environment_id,
                request_id=_optional_uuid(request_id),
                environment_profile_id=_required_uuid(
                    environment_profile_id,
                    field_name="environment_profile_id",
                ),
                environment_session_id=_required_uuid(
                    environment_session_id,
                    field_name="environment_session_id",
                ),
                admission_receipt=_dto_admission_receipt(admission_receipt),
                reason=reason,
                resolve_default_navigation_context=(resolve_default_navigation_context),
                metadata=cast(JsonObject, dict(metadata or {})),
            )
        )
        result = _join_result_from_response(response)
        if not result.accepted:
            raise EnvironmentSessionError(
                f"Environment session join failed: {result.error or result.status}",
                receipt=result.receipt,
            )
        return result

    async def describe_session(
        self,
        *,
        environment_session_id: UUID | str,
    ) -> EnvironmentSessionDescribeResult:
        response = await self.api_client.environment.session.describe_session(
            DescribeEnvironmentSessionRequest(
                actor_id=self.context.actor_id,
                environment_id=self.context.environment_id,
                environment_session_id=_required_uuid(
                    environment_session_id,
                    field_name="environment_session_id",
                ),
            )
        )
        result = _describe_result_from_response(response)
        if result.error is not None:
            raise EnvironmentSessionError(
                f"Environment session describe failed: {result.error}",
            )
        return result

    async def mount_attention_session(
        self,
        *,
        environment_session_id: UUID | str,
        attention_session_id: UUID | str,
        key: str | None = None,
        title: str | None = None,
        status: str = "active",
        request_id: UUID | str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> EnvironmentSessionAttentionMountResult:
        response = await self.api_client.environment.session.mount_attention_session(
            MountEnvironmentSessionAttentionRequest(
                actor_id=self.context.actor_id,
                environment_id=self.context.environment_id,
                request_id=_optional_uuid(request_id),
                environment_session_id=_required_uuid(
                    environment_session_id,
                    field_name="environment_session_id",
                ),
                attention_session_id=_required_uuid(
                    attention_session_id,
                    field_name="attention_session_id",
                ),
                key=key,
                title=title,
                status=status,
                metadata=cast(JsonObject, dict(metadata or {})),
            )
        )
        if response.object_instance_graph_commit_id is None:
            raise EnvironmentSessionError(
                "Environment Attention portal mount returned no graph commit."
            )
        if not response.graph_hash_post:
            raise EnvironmentSessionError(
                "Environment Attention portal mount returned no graph hash."
            )
        return EnvironmentSessionAttentionMountResult(
            environment_session_attention_session_id=(
                response.environment_session_attention_session_id
            ),
            environment_session_id=response.environment_session_id,
            attention_session_id=response.attention_session_id,
            status=response.status,
            domain_commit_id=response.domain_commit_id,
            object_instance_graph_commit_id=(response.object_instance_graph_commit_id),
            graph_hash_post=response.graph_hash_post,
            raw_response=response,
        )

    async def resolve_attention(
        self,
        *,
        environment_session_id: UUID | str,
        environment_navigation_context_id: UUID | str | None = None,
        environment_session_thread_id: UUID | str | None = None,
        environment_session_attention_session_id: UUID | str | None = None,
        expected_attention_session_id: UUID | str | None = None,
        attention_focus_transition_id: UUID | str | None = None,
        expected_attention_session_section_id: UUID | str | None = None,
        expected_focus_scope_id: UUID | str | None = None,
        expected_object_instance_graph_commit_id: UUID | str | None = None,
        expected_projection_hash: str | None = None,
        include_attention_session: bool = True,
        include_transition_list: bool = False,
        transition_limit: int | None = None,
        request_id: UUID | str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> EnvironmentSessionAttentionResolveResult:
        response = await self.api_client.environment.session.resolve_attention(
            ResolveEnvironmentSessionAttentionRequest(
                actor_id=self.context.actor_id,
                environment_id=self.context.environment_id,
                request_id=_optional_uuid(request_id),
                environment_session_id=_required_uuid(
                    environment_session_id,
                    field_name="environment_session_id",
                ),
                environment_navigation_context_id=_optional_uuid(
                    environment_navigation_context_id
                ),
                environment_session_thread_id=_optional_uuid(
                    environment_session_thread_id
                ),
                environment_session_attention_session_id=_optional_uuid(
                    environment_session_attention_session_id
                ),
                expected_attention_session_id=_optional_uuid(
                    expected_attention_session_id
                ),
                attention_focus_transition_id=_optional_uuid(
                    attention_focus_transition_id
                ),
                expected_attention_session_section_id=_optional_uuid(
                    expected_attention_session_section_id
                ),
                expected_focus_scope_id=_optional_uuid(expected_focus_scope_id),
                expected_object_instance_graph_commit_id=_optional_uuid(
                    expected_object_instance_graph_commit_id
                ),
                expected_projection_hash=expected_projection_hash,
                include_attention_session=include_attention_session,
                include_transition_list=include_transition_list,
                transition_limit=transition_limit,
                metadata=cast(JsonObject, dict(metadata or {})),
            )
        )
        result = _attention_result_from_response(response)
        if result.status == "blocked" or result.resolution is None:
            raise EnvironmentSessionError(
                f"Environment session Attention resolution failed: "
                f"{result.error or result.status}",
            )
        return result


def _start_result_from_response(
    response: StartEnvironmentSessionResponse,
) -> EnvironmentSessionStartResult:
    return EnvironmentSessionStartResult(
        accepted=response.accepted,
        status=response.status,
        error=response.error,
        session=_session_from_dto(response.session),
        join_receipt=_join_receipt_from_dto(response.join_receipt),
        default_navigation_context=response.default_navigation_context,
        default_navigation_receipt=response.default_navigation_receipt,
        evidence=dict(response.evidence),
        raw_response=response,
    )


def _join_result_from_response(
    response: JoinEnvironmentSessionResponse,
) -> EnvironmentSessionJoinResult:
    return EnvironmentSessionJoinResult(
        accepted=response.accepted,
        status=response.status,
        error=response.error,
        session=_session_from_dto(response.session),
        receipt=_join_receipt_from_dto(response.receipt),
        default_navigation_context=response.default_navigation_context,
        default_navigation_receipt=response.default_navigation_receipt,
        evidence=dict(response.evidence),
        raw_response=response,
    )


def _describe_result_from_response(
    response: DescribeEnvironmentSessionResponse,
) -> EnvironmentSessionDescribeResult:
    return EnvironmentSessionDescribeResult(
        status=response.status,
        error=response.error,
        session=_session_from_dto(response.session),
        evidence=dict(response.evidence),
        raw_response=response,
    )


def _attention_result_from_response(
    response: ResolveEnvironmentSessionAttentionResponse,
) -> EnvironmentSessionAttentionResolveResult:
    return EnvironmentSessionAttentionResolveResult(
        status=response.status,
        error=response.error,
        resolution=_attention_resolution_from_dto(response.resolution),
        evidence=dict(response.evidence),
        raw_response=response,
    )


def _attention_resolution_from_dto(
    resolution: DtoEnvironmentSessionAttentionResolution | None,
) -> EnvironmentSessionAttentionResolution | None:
    if resolution is None:
        return None
    return EnvironmentSessionAttentionResolution(
        environment_session_id=resolution.environment_session_id,
        environment_navigation_context_id=resolution.environment_navigation_context_id,
        environment_session_thread_id=resolution.environment_session_thread_id,
        environment_session_attention_session_id=(
            resolution.environment_session_attention_session_id
        ),
        environment_id=resolution.environment_id,
        environment_profile_id=resolution.environment_profile_id,
        thread_id=resolution.thread_id,
        thread_layout_id=resolution.thread_layout_id,
        attention_session_id=resolution.attention_session_id,
        identity_session_id=resolution.identity_session_id,
        attention_session=resolution.attention_session,
        active_transition=resolution.active_transition,
        validation=resolution.validation,
        transitions=tuple(resolution.transitions),
        status=resolution.status,
        blockers=tuple(resolution.blockers),
        evidence=dict(resolution.evidence),
        dto_resolution=resolution,
    )


def _session_from_dto(
    session: DtoEnvironmentSessionView | None,
) -> EnvironmentSession | None:
    if session is None:
        return None
    return EnvironmentSession(
        environment_session_id=session.environment_session_id,
        environment_session_config_id=session.environment_session_config_id,
        identity_session_id=session.identity_session_id,
        identity_session=session.identity_session,
        environment_id=session.environment_id,
        environment_profile_id=session.environment_profile_id,
        session_key=session.session_key,
        title=session.title,
        description=session.description,
        purpose=session.purpose,
        status=session.status,
        created_by_actor_id=session.created_by_actor_id,
        source_kind=session.source_kind,
        source_ref=session.source_ref,
        evidence=dict(session.evidence),
        dto_session=session,
    )


def _identity_evidence_from_dto(
    evidence: DtoEnvironmentSessionIdentityEvidence | None,
) -> EnvironmentSessionIdentityEvidence | None:
    if evidence is None:
        return None
    return EnvironmentSessionIdentityEvidence(
        identity_session=evidence.identity_session,
        identity_member=evidence.identity_member,
        identity_actor_roles=tuple(evidence.identity_actor_roles),
        evidence=dict(evidence.evidence),
        dto_evidence=evidence,
    )


def _join_receipt_from_dto(
    receipt: DtoEnvironmentSessionJoinReceipt,
) -> EnvironmentSessionJoinReceipt:
    return EnvironmentSessionJoinReceipt(
        accepted=receipt.accepted,
        status=receipt.status,
        error=receipt.error,
        reason=receipt.reason,
        actor_id=receipt.actor_id,
        environment_id=receipt.environment_id,
        environment_profile_id=receipt.environment_profile_id,
        environment_session_id=receipt.environment_session_id,
        environment_session_key=receipt.environment_session_key,
        identity_evidence=_identity_evidence_from_dto(receipt.identity_evidence),
        blockers=tuple(receipt.blockers),
        evidence=dict(receipt.evidence),
        dto_receipt=receipt,
    )


def _dto_admission_receipt(value: object) -> DtoEnvironmentActorAdmissionReceipt:
    if isinstance(value, DtoEnvironmentActorAdmissionReceipt):
        return value
    if isinstance(value, SdkEnvironmentActorAdmissionReceipt):
        if value.dto_receipt is None:
            raise ValueError("admission_receipt does not carry a DTO receipt.")
        return value.dto_receipt
    return DtoEnvironmentActorAdmissionReceipt.model_validate(value)


def _required_uuid(value: object, *, field_name: str) -> UUID:
    resolved = _optional_uuid(value)
    if resolved is None:
        raise ValueError(f"{field_name} is required.")
    return resolved


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        return UUID(text)
    raise TypeError(f"Expected UUID or UUID string, got {type(value).__name__}.")


__all__ = [
    "EnvironmentSession",
    "EnvironmentSessionClient",
    "EnvironmentSessionContext",
    "EnvironmentSessionDescribeResult",
    "EnvironmentSessionError",
    "EnvironmentSessionAttentionResolution",
    "EnvironmentSessionAttentionResolveResult",
    "EnvironmentSessionGeneratedApiClient",
    "EnvironmentSessionIdentityEvidence",
    "EnvironmentSessionJoinReceipt",
    "EnvironmentSessionJoinResult",
    "EnvironmentSessionStartResult",
]
