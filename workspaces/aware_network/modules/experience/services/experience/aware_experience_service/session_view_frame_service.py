from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentSessionAttentionResolution,
    EnvironmentSessionJoinReceipt,
)
from aware_experience_service_dto.experience.actor_admission.models import (
    ExperienceActorConfigAdmissionReceipt,
)
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext

from aware_experience_service.session_context_service import (
    EnvironmentSessionContextApiClient,
    ExperienceSessionAttentionResolutionRequestSpec,
    ExperienceSessionContextReceiptSpec,
    ResolveExperienceSessionContextRequestSpec,
    resolve_experience_session_context,
)
from aware_experience_service.session_feature_service import (
    ExperienceSessionActorContextSpec,
    ExperienceSessionScopeSpec,
    IdentityExperienceSessionApiClient,
)


class ExperienceSessionViewFrameScopeSpec(BaseModel):
    namespace: str | None = None
    experience_name: str
    profile_key: str | None = None
    environment_id: UUID | None = None
    environment_session_id: UUID | None = None
    actor_id: UUID | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    workspace_session_id: str | None = None
    view_ref: str | None = None
    window_key: str | None = None
    layout_key: str | None = None
    layout_config_id: UUID | None = None
    section_key: str | None = None
    layout_config_section_config_id: UUID | None = None
    layout_section_id: UUID | None = None
    section_focus_scope_id: UUID | None = None
    focus_scope_id: UUID | None = None
    focus_id: UUID | None = None
    observable_id: UUID | None = None
    projection_view_key: str | None = None
    section_graph_binding_key: str | None = None
    projection_experience_graph_identity_id: UUID | None = None
    object_projection_graph_identity_id: UUID | None = None
    object_instance_graph_branch_id: UUID | None = None
    topology_seed_key: str | None = None
    source_kind: str = "interface_runtime_focus"
    evidence: dict[str, Any] = Field(default_factory=dict)


class ResolveExperienceSessionViewFrameRequestSpec(BaseModel):
    request_id: UUID | None = None
    session_scope: ExperienceSessionViewFrameScopeSpec
    actor_context: ExperienceSessionActorContextSpec | None = None
    environment_admission: EnvironmentActorAdmissionReceipt | None = None
    environment_session_join: EnvironmentSessionJoinReceipt | None = None
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = None
    experience_identity_session_config_id: UUID | None = None
    environment_attention: ExperienceSessionAttentionResolutionRequestSpec | None = None
    idempotency_key: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class ExperienceSessionViewFrameLensSpec(BaseModel):
    status: str = "pending"
    view_ref: str | None = None
    projection_view_key: str | None = None
    section_graph_binding_key: str | None = None
    section_key: str | None = None
    window_key: str | None = None
    layout_key: str | None = None
    layout_config_id: UUID | None = None
    layout_config_section_config_id: UUID | None = None
    layout_section_id: UUID | None = None
    section_focus_scope_id: UUID | None = None
    focus_scope_id: UUID | None = None
    focus_id: UUID | None = None
    observable_id: UUID | None = None
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class ExperienceSessionViewFrameSpec(BaseModel):
    accepted: bool = False
    status: str
    error: str | None = None
    session_scope: ExperienceSessionViewFrameScopeSpec
    actor_admission: object | None = None
    identity_evidence: object | None = None
    environment_attention_resolution: EnvironmentSessionAttentionResolution | None = (
        None
    )
    context_receipt: ExperienceSessionContextReceiptSpec | None = None
    lens: ExperienceSessionViewFrameLensSpec | None = None
    environment_id: UUID | None = None
    environment_profile_id: UUID | None = None
    environment_session_id: UUID | None = None
    environment_navigation_context_id: UUID | None = None
    environment_session_thread_id: UUID | None = None
    environment_session_attention_session_id: UUID | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    thread_layout_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    attention_session_id: UUID | None = None
    active_attention_focus_transition_id: UUID | None = None
    transition_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class ResolveExperienceSessionViewFrameResponseSpec(BaseModel):
    request_id: UUID | None = None
    accepted: bool = False
    status: str
    error: str | None = None
    frame: ExperienceSessionViewFrameSpec
    evidence: dict[str, Any] = Field(default_factory=dict)


async def resolve_experience_session_view_frame(
    *,
    request: ResolveExperienceSessionViewFrameRequestSpec,
    host_context: ServiceApiHostContext,
    identity_api_client: IdentityExperienceSessionApiClient | None = None,
    environment_api_client: EnvironmentSessionContextApiClient | None = None,
) -> ResolveExperienceSessionViewFrameResponseSpec:
    context_response = await resolve_experience_session_context(
        request=_context_request_from_view_frame_request(request),
        host_context=host_context,
        identity_api_client=identity_api_client,
        environment_api_client=environment_api_client,
    )
    frame = _frame_from_context_response(
        request=request,
        context_receipt=context_response.receipt,
        status=context_response.status,
        error=context_response.error,
        accepted=context_response.accepted,
    )
    evidence = {
        "source": "aware_experience_service.session_view_frame",
        "context_status": context_response.status,
        "view_frame_status": frame.status,
        "environment_session_id": (
            str(frame.environment_session_id)
            if frame.environment_session_id is not None
            else None
        ),
        "attention_session_id": (
            str(frame.attention_session_id)
            if frame.attention_session_id is not None
            else None
        ),
    }
    return ResolveExperienceSessionViewFrameResponseSpec(
        request_id=context_response.request_id,
        accepted=context_response.accepted,
        status=frame.status,
        error=context_response.error,
        frame=frame.model_copy(
            update={
                "evidence": {
                    **dict(frame.evidence),
                    "response_evidence": evidence,
                }
            }
        ),
        evidence=evidence,
    )


def _context_request_from_view_frame_request(
    request: ResolveExperienceSessionViewFrameRequestSpec,
) -> ResolveExperienceSessionContextRequestSpec:
    return ResolveExperienceSessionContextRequestSpec(
        request_id=request.request_id,
        session_scope=_context_scope_from_view_frame_scope(request.session_scope),
        actor_context=request.actor_context,
        environment_admission=request.environment_admission,
        environment_session_join=request.environment_session_join,
        experience_actor_admission=request.experience_actor_admission,
        experience_identity_session_config_id=(
            request.experience_identity_session_config_id
        ),
        environment_attention=request.environment_attention,
        idempotency_key=request.idempotency_key,
        evidence={
            **dict(request.evidence),
            "source": "aware_experience_service.session_view_frame",
        },
    )


def _context_scope_from_view_frame_scope(
    scope: ExperienceSessionViewFrameScopeSpec,
) -> ExperienceSessionScopeSpec:
    return ExperienceSessionScopeSpec(
        experience_name=scope.experience_name,
        profile_key=scope.profile_key,
        environment_id=scope.environment_id,
        environment_session_id=scope.environment_session_id,
        actor_id=scope.actor_id,
        process_id=scope.process_id,
        thread_id=scope.thread_id,
        branch_id=scope.branch_id,
        projection_hash=scope.projection_hash,
        workspace_session_id=scope.workspace_session_id,
    )


def _frame_from_context_response(
    *,
    request: ResolveExperienceSessionViewFrameRequestSpec,
    context_receipt: ExperienceSessionContextReceiptSpec,
    status: str,
    error: str | None,
    accepted: bool,
) -> ExperienceSessionViewFrameSpec:
    resolution = context_receipt.environment_attention_resolution
    session_scope = _resolved_view_frame_scope(
        request_scope=request.session_scope,
        context_receipt=context_receipt,
    )
    blockers = list(context_receipt.blockers)
    context_lens = context_receipt.lens
    if context_lens is not None:
        blockers.extend(context_lens.blockers)
    active_transition = (
        getattr(resolution, "active_transition", None)
        if resolution is not None
        else None
    )
    active_transition_id = (
        getattr(active_transition, "attention_focus_transition_id", None)
        if active_transition is not None
        else None
    )
    transitions = (
        list(getattr(resolution, "transitions", []) or [])
        if resolution is not None
        else []
    )
    frame_status = "resolved" if accepted and not blockers else "blocked"
    return ExperienceSessionViewFrameSpec(
        accepted=accepted,
        status=frame_status if status not in {"resolved", "ok"} else status,
        error=error,
        session_scope=session_scope,
        actor_admission=context_receipt.actor_admission,
        identity_evidence=context_receipt.identity_evidence,
        environment_attention_resolution=resolution,
        context_receipt=context_receipt,
        lens=_lens_from_scope(
            scope=session_scope,
            context_lens=context_lens,
            blockers=blockers,
            resolved=accepted and not blockers,
        ),
        environment_id=session_scope.environment_id
        or (resolution.environment_id if resolution is not None else None),
        environment_profile_id=(
            resolution.environment_profile_id if resolution is not None else None
        ),
        environment_session_id=session_scope.environment_session_id
        or (resolution.environment_session_id if resolution is not None else None),
        environment_navigation_context_id=(
            resolution.environment_navigation_context_id
            if resolution is not None
            else None
        ),
        environment_session_thread_id=(
            resolution.environment_session_thread_id
            if resolution is not None
            else None
        ),
        environment_session_attention_session_id=(
            resolution.environment_session_attention_session_id
            if resolution is not None
            else None
        ),
        process_id=session_scope.process_id,
        thread_id=session_scope.thread_id
        or (resolution.thread_id if resolution is not None else None),
        thread_layout_id=resolution.thread_layout_id if resolution is not None else None,
        branch_id=session_scope.branch_id,
        projection_hash=session_scope.projection_hash,
        attention_session_id=(
            resolution.attention_session_id if resolution is not None else None
        ),
        active_attention_focus_transition_id=active_transition_id,
        transition_count=len(transitions),
        blockers=_dedupe_text(blockers),
        evidence={
            "source": "aware_experience_service.session_view_frame",
            "context_status": context_receipt.status,
            "context_error": context_receipt.error,
            "context_evidence": dict(context_receipt.evidence),
            "request_evidence": dict(request.evidence),
        },
    )


def _resolved_view_frame_scope(
    *,
    request_scope: ExperienceSessionViewFrameScopeSpec,
    context_receipt: ExperienceSessionContextReceiptSpec,
) -> ExperienceSessionViewFrameScopeSpec:
    context_scope = context_receipt.session_scope
    return request_scope.model_copy(
        update={
            "environment_id": request_scope.environment_id
            or context_scope.environment_id,
            "environment_session_id": request_scope.environment_session_id
            or context_scope.environment_session_id,
            "actor_id": request_scope.actor_id or context_scope.actor_id,
            "process_id": request_scope.process_id or context_scope.process_id,
            "thread_id": request_scope.thread_id or context_scope.thread_id,
            "branch_id": request_scope.branch_id or context_scope.branch_id,
            "projection_hash": request_scope.projection_hash
            or context_scope.projection_hash,
            "workspace_session_id": request_scope.workspace_session_id
            or context_scope.workspace_session_id,
        }
    )


def _lens_from_scope(
    *,
    scope: ExperienceSessionViewFrameScopeSpec,
    context_lens: object | None,
    blockers: list[str],
    resolved: bool,
) -> ExperienceSessionViewFrameLensSpec:
    context_evidence = (
        dict(getattr(context_lens, "evidence", {}) or {})
        if context_lens is not None
        else {}
    )
    return ExperienceSessionViewFrameLensSpec(
        status="resolved" if resolved else "blocked",
        view_ref=scope.view_ref or getattr(context_lens, "view_ref", None),
        projection_view_key=scope.projection_view_key
        or getattr(context_lens, "projection_view_key", None),
        section_graph_binding_key=scope.section_graph_binding_key
        or getattr(context_lens, "section_graph_binding_key", None),
        section_key=scope.section_key,
        window_key=scope.window_key,
        layout_key=scope.layout_key,
        layout_config_id=scope.layout_config_id,
        layout_config_section_config_id=scope.layout_config_section_config_id,
        layout_section_id=scope.layout_section_id,
        section_focus_scope_id=scope.section_focus_scope_id,
        focus_scope_id=scope.focus_scope_id,
        focus_id=scope.focus_id,
        observable_id=scope.observable_id,
        blockers=_dedupe_text(blockers),
        evidence={
            "source": "aware_experience_service.session_view_frame",
            "scope_evidence": dict(scope.evidence),
            "context_lens_evidence": context_evidence,
        },
    )


def _dedupe_text(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


__all__ = [
    "ExperienceSessionViewFrameLensSpec",
    "ExperienceSessionViewFrameScopeSpec",
    "ExperienceSessionViewFrameSpec",
    "ResolveExperienceSessionViewFrameRequestSpec",
    "ResolveExperienceSessionViewFrameResponseSpec",
    "resolve_experience_session_view_frame",
]
