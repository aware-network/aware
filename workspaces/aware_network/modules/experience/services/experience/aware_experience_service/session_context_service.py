from __future__ import annotations

from typing import Any, Protocol, cast
from uuid import UUID

from pydantic import BaseModel, Field
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentSessionAttentionResolution,
    EnvironmentSessionJoinReceipt,
    ResolveEnvironmentSessionAttentionRequest,
    ResolveEnvironmentSessionAttentionResponse,
)
from aware_experience_service_dto.experience.actor_admission.models import (
    ExperienceActorConfigAdmissionReceipt,
)
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)

from aware_experience_service.session_feature_service import (
    AdmitExperienceSessionActorRequest,
    ExperienceSessionActorAdmissionSpec,
    ExperienceSessionActorContextSpec,
    ExperienceSessionIdentityEvidenceSpec,
    ExperienceSessionScopeSpec,
    IdentityExperienceSessionApiClient,
    admit_experience_session_actor,
)

_ENVIRONMENT_SERVICE_API_PACKAGE_NAME = "environment-service-api"


class ExperienceSessionAttentionResolutionRequestSpec(BaseModel):
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


class ResolveExperienceSessionContextRequestSpec(BaseModel):
    request_id: UUID | None = None
    session_scope: ExperienceSessionScopeSpec
    actor_context: ExperienceSessionActorContextSpec | None = None
    environment_admission: EnvironmentActorAdmissionReceipt | None = None
    environment_session_join: EnvironmentSessionJoinReceipt | None = None
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = None
    experience_identity_session_config_id: UUID | None = None
    environment_attention: ExperienceSessionAttentionResolutionRequestSpec | None = None
    idempotency_key: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class ExperienceSessionLensContextSpec(BaseModel):
    status: str = "pending"
    view_ref: str | None = None
    projection_view_key: str | None = None
    section_graph_binding_key: str | None = None
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class ExperienceSessionContextReceiptSpec(BaseModel):
    accepted: bool = False
    status: str
    error: str | None = None
    session_scope: ExperienceSessionScopeSpec
    actor_admission: ExperienceSessionActorAdmissionSpec | None = None
    identity_evidence: ExperienceSessionIdentityEvidenceSpec | None = None
    environment_attention_resolution: EnvironmentSessionAttentionResolution | None = (
        None
    )
    lens: ExperienceSessionLensContextSpec | None = None
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class ResolveExperienceSessionContextResponseSpec(BaseModel):
    request_id: UUID | None = None
    accepted: bool = False
    status: str
    error: str | None = None
    receipt: ExperienceSessionContextReceiptSpec
    evidence: dict[str, Any] = Field(default_factory=dict)


class _EnvironmentSessionCapability(Protocol):
    async def resolve_attention(
        self,
        request: ResolveEnvironmentSessionAttentionRequest,
    ) -> ResolveEnvironmentSessionAttentionResponse: ...


class _EnvironmentCapability(Protocol):
    @property
    def session(self) -> _EnvironmentSessionCapability: ...


class EnvironmentSessionContextApiClient(Protocol):
    @property
    def environment(self) -> _EnvironmentCapability: ...


async def resolve_experience_session_context(
    *,
    request: ResolveExperienceSessionContextRequestSpec,
    host_context: ServiceApiHostContext,
    identity_api_client: IdentityExperienceSessionApiClient | None = None,
    environment_api_client: EnvironmentSessionContextApiClient | None = None,
) -> ResolveExperienceSessionContextResponseSpec:
    session_scope = _session_scope_with_environment_join(request)
    admission_response = await admit_experience_session_actor(
        request=AdmitExperienceSessionActorRequest(
            request_id=request.request_id,
            session_scope=session_scope,
            actor_context=request.actor_context,
            environment_admission=request.environment_admission,
            environment_session_join=request.environment_session_join,
            experience_actor_admission=request.experience_actor_admission,
            experience_identity_session_config_id=(
                request.experience_identity_session_config_id
            ),
            idempotency_key=request.idempotency_key,
        ),
        host_context=host_context,
        identity_api_client=identity_api_client,
    )
    admission = admission_response.admission
    if not admission.admitted:
        return _blocked_response(
            request=request,
            session_scope=session_scope,
            admission=admission,
            reason=admission.reason or "experience_session_actor_not_admitted",
            blockers=list(admission.blockers),
            evidence={
                "source": "aware_experience_service.session_context",
                "stage": "experience_session_admission",
            },
        )

    environment_client = environment_api_client or _build_environment_api_client(
        host_context=host_context,
    )
    if environment_client is None:
        return _blocked_response(
            request=request,
            session_scope=session_scope,
            admission=admission,
            reason="environment_session_attention_api_route_unavailable",
            blockers=["environment_session_attention_api_route_unavailable"],
            evidence={
                "source": "aware_experience_service.session_context",
                "stage": "environment_attention_resolution",
            },
        )

    environment_response = (
        await environment_client.environment.session.resolve_attention(
            _environment_attention_request(
                request=request,
                session_scope=session_scope,
                admission=admission,
            )
        )
    )
    resolution = environment_response.resolution
    environment_blockers = _environment_attention_blockers(environment_response)
    if environment_blockers:
        return _blocked_response(
            request=request,
            session_scope=session_scope,
            admission=admission,
            reason=environment_response.error
            or (resolution.status if resolution is not None else None)
            or "environment_session_attention_not_resolved",
            blockers=environment_blockers,
            environment_attention_resolution=resolution,
            evidence={
                "source": "aware_experience_service.session_context",
                "stage": "environment_attention_resolution",
                "environment_response_status": environment_response.status,
            },
        )

    receipt = ExperienceSessionContextReceiptSpec(
        accepted=True,
        status="resolved",
        session_scope=session_scope,
        actor_admission=admission,
        identity_evidence=admission.identity_evidence,
        environment_attention_resolution=resolution,
        lens=_lens_context_from_scope(request=request, resolution=resolution),
        evidence={
            "source": "aware_experience_service.session_context",
            "environment_response_status": environment_response.status,
            "environment_session_id": str(session_scope.environment_session_id),
            "attention_session_id": (
                str(resolution.attention_session_id)
                if resolution is not None
                and resolution.attention_session_id is not None
                else None
            ),
        },
    )
    return ResolveExperienceSessionContextResponseSpec(
        request_id=request.request_id,
        accepted=True,
        status="resolved",
        receipt=receipt,
        evidence=dict(receipt.evidence),
    )


def _session_scope_with_environment_join(
    request: ResolveExperienceSessionContextRequestSpec,
) -> ExperienceSessionScopeSpec:
    if (
        request.session_scope.environment_session_id is None
        and request.environment_session_join is not None
    ):
        return request.session_scope.model_copy(
            update={
                "environment_session_id": (
                    request.environment_session_join.environment_session_id
                )
            }
        )
    return request.session_scope


def _environment_attention_request(
    *,
    request: ResolveExperienceSessionContextRequestSpec,
    session_scope: ExperienceSessionScopeSpec,
    admission: ExperienceSessionActorAdmissionSpec,
) -> ResolveEnvironmentSessionAttentionRequest:
    attention = request.environment_attention or (
        ExperienceSessionAttentionResolutionRequestSpec()
    )
    if session_scope.environment_id is None:
        raise ValueError("Experience session context requires environment_id.")
    if session_scope.environment_session_id is None:
        raise ValueError("Experience session context requires environment_session_id.")
    return ResolveEnvironmentSessionAttentionRequest(
        actor_id=admission.actor_id or session_scope.actor_id,
        environment_id=session_scope.environment_id,
        branch_id=session_scope.branch_id,
        projection_hash=session_scope.projection_hash,
        request_id=request.request_id,
        environment_session_id=session_scope.environment_session_id,
        environment_navigation_context_id=(attention.environment_navigation_context_id),
        environment_session_thread_id=attention.environment_session_thread_id,
        environment_session_attention_session_id=(
            attention.environment_session_attention_session_id
        ),
        expected_attention_session_id=attention.expected_attention_session_id,
        attention_focus_transition_id=attention.attention_focus_transition_id,
        expected_attention_session_section_id=(
            attention.expected_attention_session_section_id
        ),
        expected_focus_scope_id=attention.expected_focus_scope_id,
        expected_object_instance_graph_commit_id=(
            attention.expected_object_instance_graph_commit_id
        ),
        expected_projection_hash=attention.expected_projection_hash
        or session_scope.projection_hash,
        include_attention_session=attention.include_attention_session,
        include_transition_list=attention.include_transition_list,
        transition_limit=attention.transition_limit,
        metadata={
            **dict(attention.metadata),
            "source": "aware_experience_service.session_context",
            "experience_name": session_scope.experience_name,
            "profile_key": session_scope.profile_key,
            "request_evidence": dict(request.evidence),
        },
    )


def _environment_attention_blockers(
    response: ResolveEnvironmentSessionAttentionResponse,
) -> list[str]:
    blockers: list[str] = []
    resolution = response.resolution
    if resolution is None:
        if response.error:
            blockers.append(response.error)
        blockers.append("environment_session_attention_resolution_missing")
        return _dedupe_text(blockers)
    blockers.extend(resolution.blockers)
    if blockers:
        return _dedupe_text(blockers)
    if response.error:
        blockers.append(response.error)
    if response.status not in {"resolved", "ok"}:
        blockers.append("environment_session_attention_not_resolved")
    if resolution.status not in {"resolved", "ok"}:
        blockers.append("environment_session_attention_resolution_not_resolved")
    return _dedupe_text(blockers)


def _dedupe_text(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _lens_context_from_scope(
    *,
    request: ResolveExperienceSessionContextRequestSpec,
    resolution: EnvironmentSessionAttentionResolution | None,
) -> ExperienceSessionLensContextSpec:
    scope = request.session_scope
    return ExperienceSessionLensContextSpec(
        status="resolved" if resolution is not None else "pending",
        view_ref=getattr(scope, "view_ref", None),
        projection_view_key=getattr(scope, "projection_view_key", None),
        section_graph_binding_key=getattr(scope, "section_graph_binding_key", None),
        evidence={
            "source": "aware_experience_service.session_context",
            "thread_id": (
                str(resolution.thread_id)
                if resolution is not None and resolution.thread_id is not None
                else None
            ),
            "thread_layout_id": (
                str(resolution.thread_layout_id)
                if resolution is not None and resolution.thread_layout_id is not None
                else None
            ),
        },
    )


def _blocked_response(
    *,
    request: ResolveExperienceSessionContextRequestSpec,
    session_scope: ExperienceSessionScopeSpec,
    admission: ExperienceSessionActorAdmissionSpec | None,
    reason: str,
    blockers: list[str],
    evidence: dict[str, Any],
    environment_attention_resolution: (
        EnvironmentSessionAttentionResolution | None
    ) = None,
) -> ResolveExperienceSessionContextResponseSpec:
    receipt = ExperienceSessionContextReceiptSpec(
        accepted=False,
        status="blocked",
        error=reason,
        session_scope=session_scope,
        actor_admission=admission,
        identity_evidence=admission.identity_evidence if admission else None,
        environment_attention_resolution=environment_attention_resolution,
        lens=ExperienceSessionLensContextSpec(
            status="blocked",
            blockers=blockers,
            evidence=evidence,
        ),
        blockers=blockers,
        evidence=evidence,
    )
    return ResolveExperienceSessionContextResponseSpec(
        request_id=request.request_id,
        accepted=False,
        status="blocked",
        error=reason,
        receipt=receipt,
        evidence=dict(receipt.evidence),
    )


def _build_environment_api_client(
    *,
    host_context: ServiceApiHostContext,
) -> EnvironmentSessionContextApiClient | None:
    invoker = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name=_ENVIRONMENT_SERVICE_API_PACKAGE_NAME,
        actor_id=host_context.operation_context.actor_id,
        invocation_context=cast(
            Any,
            (
                dict(host_context.invocation_context)
                if host_context.invocation_context is not None
                else None
            ),
        ),
    )
    if invoker is None:
        return None

    from aware_environment_service_api import AwareEnvironmentServiceApiClient

    return AwareEnvironmentServiceApiClient(invoker)


__all__ = [
    "EnvironmentSessionContextApiClient",
    "ExperienceSessionAttentionResolutionRequestSpec",
    "ExperienceSessionContextReceiptSpec",
    "ExperienceSessionLensContextSpec",
    "ResolveExperienceSessionContextRequestSpec",
    "ResolveExperienceSessionContextResponseSpec",
    "resolve_experience_session_context",
]
