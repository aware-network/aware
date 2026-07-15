from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, Field

from aware_environment_service.navigation_models import (
    EnvironmentNavigationCommitReceiptSpec,
    EnvironmentNavigationContextViewSpec,
)
from aware_environment_service.session_service import (
    EnvironmentSessionJoinReceiptSpec,
)
from aware_identity_service_dto.session.session import SessionMemberSummary
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext


class CreateEnvironmentNavigationContextRequestSpec(BaseModel):
    request_id: UUID | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    environment_session_id: UUID
    session_join_receipt: EnvironmentSessionJoinReceiptSpec
    key: str
    title: str | None = None
    status: str = "active"
    is_default: bool = False
    selected_process_id: UUID | None = None
    selected_thread_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreateEnvironmentNavigationContextResponseSpec(BaseModel):
    request_id: UUID | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    accepted: bool = False
    status: str
    error: str | None = None
    context: EnvironmentNavigationContextViewSpec | None = None
    receipt: EnvironmentNavigationCommitReceiptSpec
    evidence: dict[str, Any] = Field(default_factory=dict)


class SelectEnvironmentNavigationTargetRequestSpec(BaseModel):
    request_id: UUID | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    environment_session_id: UUID
    environment_navigation_context_id: UUID
    session_join_receipt: EnvironmentSessionJoinReceiptSpec
    selected_process_id: UUID | None = None
    selected_thread_id: UUID | None = None
    expected_head_commit_id: UUID | None = None
    expected_graph_hash_pre: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SelectEnvironmentNavigationTargetResponseSpec(BaseModel):
    request_id: UUID | None = None
    actor_id: UUID | None = None
    environment_id: UUID
    accepted: bool = False
    status: str
    error: str | None = None
    context: EnvironmentNavigationContextViewSpec | None = None
    receipt: EnvironmentNavigationCommitReceiptSpec
    evidence: dict[str, Any] = Field(default_factory=dict)


class DescribeEnvironmentNavigationContextRequestSpec(BaseModel):
    actor_id: UUID | None = None
    environment_id: UUID
    environment_session_id: UUID
    environment_navigation_context_id: UUID
    session_join_receipt: EnvironmentSessionJoinReceiptSpec
    include_commit: bool = True


class DescribeEnvironmentNavigationContextResponseSpec(BaseModel):
    actor_id: UUID | None = None
    environment_id: UUID
    status: str
    error: str | None = None
    context: EnvironmentNavigationContextViewSpec | None = None
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class ListEnvironmentNavigationContextsRequestSpec(BaseModel):
    actor_id: UUID | None = None
    environment_id: UUID
    environment_session_id: UUID
    session_join_receipt: EnvironmentSessionJoinReceiptSpec
    include_closed: bool = False


class ListEnvironmentNavigationContextsResponseSpec(BaseModel):
    actor_id: UUID | None = None
    environment_id: UUID
    status: str
    error: str | None = None
    contexts: list[EnvironmentNavigationContextViewSpec] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class EnvironmentNavigationBackend(Protocol):
    async def create_navigation_context(
        self,
        *,
        request: CreateEnvironmentNavigationContextRequestSpec,
        actor_id: UUID,
        member: SessionMemberSummary,
    ) -> EnvironmentNavigationContextViewSpec: ...

    async def select_navigation_target(
        self,
        *,
        request: SelectEnvironmentNavigationTargetRequestSpec,
        actor_id: UUID,
        member: SessionMemberSummary,
    ) -> EnvironmentNavigationContextViewSpec: ...

    async def describe_navigation_context(
        self,
        *,
        request: DescribeEnvironmentNavigationContextRequestSpec,
        actor_id: UUID,
        member: SessionMemberSummary,
    ) -> EnvironmentNavigationContextViewSpec | None: ...

    async def list_navigation_contexts(
        self,
        *,
        request: ListEnvironmentNavigationContextsRequestSpec,
        actor_id: UUID,
        member: SessionMemberSummary,
    ) -> list[EnvironmentNavigationContextViewSpec]: ...


async def create_environment_navigation_context(
    *,
    request: CreateEnvironmentNavigationContextRequestSpec,
    host_context: ServiceApiHostContext,
    navigation_backend: EnvironmentNavigationBackend | None,
) -> CreateEnvironmentNavigationContextResponseSpec:
    actor_id = request.actor_id or host_context.operation_context.actor_id
    validation = _validate_session_join(
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_session_id=request.environment_session_id,
        receipt=request.session_join_receipt,
    )
    if validation.blockers:
        receipt = _blocked_commit_receipt(
            actor_id=actor_id,
            environment_id=request.environment_id,
            environment_session_id=request.environment_session_id,
            key=request.key,
            reason=validation.blockers[0],
            blockers=validation.blockers,
            evidence=validation.evidence,
        )
        return CreateEnvironmentNavigationContextResponseSpec(
            request_id=request.request_id,
            actor_id=actor_id,
            environment_id=request.environment_id,
            accepted=False,
            status="blocked",
            error=receipt.error,
            receipt=receipt,
            evidence=dict(receipt.evidence),
        )
    if navigation_backend is None:
        receipt = _blocked_commit_receipt(
            actor_id=actor_id,
            environment_id=request.environment_id,
            environment_session_id=request.environment_session_id,
            key=request.key,
            reason="environment_navigation_backend_unavailable",
            blockers=["environment_navigation_backend_unavailable"],
            evidence=validation.evidence,
        )
        return CreateEnvironmentNavigationContextResponseSpec(
            request_id=request.request_id,
            actor_id=actor_id,
            environment_id=request.environment_id,
            accepted=False,
            status="blocked",
            error=receipt.error,
            receipt=receipt,
            evidence=dict(receipt.evidence),
        )

    validated_actor_id = _validated_actor_id(actor_id)
    member = _validated_member(validation)
    context = await navigation_backend.create_navigation_context(
        request=request,
        actor_id=validated_actor_id,
        member=member,
    )
    normalized = _normalize_context(
        context, request_environment_id=request.environment_id
    )
    receipt = _commit_receipt_from_context(
        context=normalized,
        actor_id=actor_id,
        environment_id=request.environment_id,
        status="created",
        validation_evidence=validation.evidence,
    )
    return CreateEnvironmentNavigationContextResponseSpec(
        request_id=request.request_id,
        actor_id=actor_id,
        environment_id=request.environment_id,
        accepted=True,
        status="created",
        context=normalized,
        receipt=receipt,
        evidence=dict(receipt.evidence),
    )


async def select_environment_navigation_target(
    *,
    request: SelectEnvironmentNavigationTargetRequestSpec,
    host_context: ServiceApiHostContext,
    navigation_backend: EnvironmentNavigationBackend | None,
) -> SelectEnvironmentNavigationTargetResponseSpec:
    actor_id = request.actor_id or host_context.operation_context.actor_id
    validation = _validate_session_join(
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_session_id=request.environment_session_id,
        receipt=request.session_join_receipt,
    )
    if validation.blockers:
        receipt = _blocked_commit_receipt(
            actor_id=actor_id,
            environment_id=request.environment_id,
            environment_session_id=request.environment_session_id,
            environment_navigation_context_id=request.environment_navigation_context_id,
            reason=validation.blockers[0],
            blockers=validation.blockers,
            evidence=validation.evidence,
        )
        return SelectEnvironmentNavigationTargetResponseSpec(
            request_id=request.request_id,
            actor_id=actor_id,
            environment_id=request.environment_id,
            accepted=False,
            status="blocked",
            error=receipt.error,
            receipt=receipt,
            evidence=dict(receipt.evidence),
        )
    if navigation_backend is None:
        receipt = _blocked_commit_receipt(
            actor_id=actor_id,
            environment_id=request.environment_id,
            environment_session_id=request.environment_session_id,
            environment_navigation_context_id=request.environment_navigation_context_id,
            reason="environment_navigation_backend_unavailable",
            blockers=["environment_navigation_backend_unavailable"],
            evidence=validation.evidence,
        )
        return SelectEnvironmentNavigationTargetResponseSpec(
            request_id=request.request_id,
            actor_id=actor_id,
            environment_id=request.environment_id,
            accepted=False,
            status="blocked",
            error=receipt.error,
            receipt=receipt,
            evidence=dict(receipt.evidence),
        )

    validated_actor_id = _validated_actor_id(actor_id)
    member = _validated_member(validation)
    context = await navigation_backend.select_navigation_target(
        request=request,
        actor_id=validated_actor_id,
        member=member,
    )
    normalized = _normalize_context(
        context, request_environment_id=request.environment_id
    )
    receipt = _commit_receipt_from_context(
        context=normalized,
        actor_id=actor_id,
        environment_id=request.environment_id,
        status="selected",
        validation_evidence=validation.evidence,
        reason=request.reason,
    )
    return SelectEnvironmentNavigationTargetResponseSpec(
        request_id=request.request_id,
        actor_id=actor_id,
        environment_id=request.environment_id,
        accepted=True,
        status="selected",
        context=normalized,
        receipt=receipt,
        evidence=dict(receipt.evidence),
    )


async def describe_environment_navigation_context(
    *,
    request: DescribeEnvironmentNavigationContextRequestSpec,
    host_context: ServiceApiHostContext,
    navigation_backend: EnvironmentNavigationBackend | None,
) -> DescribeEnvironmentNavigationContextResponseSpec:
    actor_id = request.actor_id or host_context.operation_context.actor_id
    validation = _validate_session_join(
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_session_id=request.environment_session_id,
        receipt=request.session_join_receipt,
    )
    if validation.blockers:
        return _blocked_describe_response(
            request=request,
            actor_id=actor_id,
            blockers=validation.blockers,
            evidence=validation.evidence,
        )
    if navigation_backend is None:
        return _blocked_describe_response(
            request=request,
            actor_id=actor_id,
            blockers=["environment_navigation_backend_unavailable"],
            evidence=validation.evidence,
        )

    validated_actor_id = _validated_actor_id(actor_id)
    member = _validated_member(validation)
    context = await navigation_backend.describe_navigation_context(
        request=request,
        actor_id=validated_actor_id,
        member=member,
    )
    if context is None:
        return DescribeEnvironmentNavigationContextResponseSpec(
            actor_id=actor_id,
            environment_id=request.environment_id,
            status="not_found",
            error="environment_navigation_context_not_found",
            blockers=["environment_navigation_context_not_found"],
            evidence={
                **validation.evidence,
                "environment_navigation_context_id": str(
                    request.environment_navigation_context_id
                ),
            },
        )
    normalized = _normalize_context(
        context, request_environment_id=request.environment_id
    )
    return DescribeEnvironmentNavigationContextResponseSpec(
        actor_id=actor_id,
        environment_id=request.environment_id,
        status="described",
        context=normalized,
        evidence={
            **validation.evidence,
            "environment_navigation_context_id": str(
                normalized.environment_navigation_context_id
            ),
        },
    )


async def list_environment_navigation_contexts(
    *,
    request: ListEnvironmentNavigationContextsRequestSpec,
    host_context: ServiceApiHostContext,
    navigation_backend: EnvironmentNavigationBackend | None,
) -> ListEnvironmentNavigationContextsResponseSpec:
    actor_id = request.actor_id or host_context.operation_context.actor_id
    validation = _validate_session_join(
        actor_id=actor_id,
        environment_id=request.environment_id,
        environment_session_id=request.environment_session_id,
        receipt=request.session_join_receipt,
    )
    if validation.blockers:
        return _blocked_list_response(
            request=request,
            actor_id=actor_id,
            blockers=validation.blockers,
            evidence=validation.evidence,
        )
    if navigation_backend is None:
        return _blocked_list_response(
            request=request,
            actor_id=actor_id,
            blockers=["environment_navigation_backend_unavailable"],
            evidence=validation.evidence,
        )

    validated_actor_id = _validated_actor_id(actor_id)
    member = _validated_member(validation)
    contexts = await navigation_backend.list_navigation_contexts(
        request=request,
        actor_id=validated_actor_id,
        member=member,
    )
    normalized = [
        _normalize_context(context, request_environment_id=request.environment_id)
        for context in contexts
        if request.include_closed or context.status != "closed"
    ]
    return ListEnvironmentNavigationContextsResponseSpec(
        actor_id=actor_id,
        environment_id=request.environment_id,
        status="listed",
        contexts=normalized,
        evidence={
            **validation.evidence,
            "environment_session_id": str(request.environment_session_id),
            "context_count": len(normalized),
        },
    )


class _SessionJoinValidation(BaseModel):
    blockers: list[str] = Field(default_factory=list)
    member: SessionMemberSummary | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


def _validate_session_join(
    *,
    actor_id: UUID | None,
    environment_id: UUID,
    environment_session_id: UUID,
    receipt: EnvironmentSessionJoinReceiptSpec,
) -> _SessionJoinValidation:
    evidence: dict[str, Any] = {
        "source": "aware_environment_service.navigation",
        "session_join_status": receipt.status,
        "environment_session_id": str(environment_session_id),
    }
    blockers: list[str] = []
    if actor_id is None:
        blockers.append("actor_id_missing")
    if not receipt.accepted:
        blockers.append(receipt.error or "environment_session_join_not_accepted")
    if receipt.actor_id is None:
        blockers.append("environment_session_join_actor_id_missing")
    elif actor_id is not None and receipt.actor_id != actor_id:
        blockers.append("environment_session_join_actor_mismatch")
    if receipt.environment_id != environment_id:
        blockers.append("environment_session_join_environment_mismatch")
    if receipt.environment_session_id is None:
        blockers.append("environment_session_join_session_id_missing")
    elif receipt.environment_session_id != environment_session_id:
        blockers.append("environment_session_join_session_mismatch")
    identity_evidence = receipt.identity_evidence
    identity_session = (
        identity_evidence.identity_session if identity_evidence is not None else None
    )
    member = (
        identity_evidence.identity_member if identity_evidence is not None else None
    )
    if identity_evidence is None:
        blockers.append("environment_session_join_identity_evidence_missing")
    if identity_session is None:
        blockers.append("environment_session_join_identity_session_missing")
    if member is None:
        blockers.append("environment_session_join_identity_member_missing")
    else:
        if actor_id is not None and member.actor_id != actor_id:
            blockers.append("environment_session_join_identity_member_actor_mismatch")
        if (
            identity_session is not None
            and member.session_id != identity_session.session_id
        ):
            blockers.append("environment_session_join_identity_member_session_mismatch")
        if (member.status or "").strip().lower() != "active":
            blockers.append("environment_session_identity_member_inactive")
    if blockers:
        evidence["blockers"] = list(dict.fromkeys(blockers))
    return _SessionJoinValidation(
        blockers=list(dict.fromkeys(blockers)),
        member=member,
        evidence=evidence,
    )


def _validated_member(
    validation: _SessionJoinValidation,
) -> SessionMemberSummary:
    member = validation.member
    if member is None:
        raise RuntimeError("Environment navigation validation missing member.")
    return member


def _validated_actor_id(actor_id: UUID | None) -> UUID:
    if actor_id is None:
        raise RuntimeError("Environment navigation validation missing actor_id.")
    return actor_id


def _commit_receipt_from_context(
    *,
    context: EnvironmentNavigationContextViewSpec,
    actor_id: UUID | None,
    environment_id: UUID,
    status: str,
    validation_evidence: Mapping[str, Any],
    reason: str | None = None,
) -> EnvironmentNavigationCommitReceiptSpec:
    return EnvironmentNavigationCommitReceiptSpec(
        accepted=True,
        status=status,
        reason=reason,
        actor_id=actor_id,
        environment_id=environment_id,
        environment_session_id=context.environment_session_id,
        environment_navigation_context_id=context.environment_navigation_context_id,
        key=context.key,
        is_default=context.is_default,
        branch_id=context.branch_id,
        projection_hash=context.projection_hash,
        root_object_id=context.root_object_id,
        commit_id=context.commit_id,
        object_instance_graph_commit_id=context.object_instance_graph_commit_id,
        graph_hash_post=context.graph_hash_post,
        selected_process_id=context.selected_process_id,
        selected_thread_id=context.selected_thread_id,
        evidence={
            **dict(validation_evidence),
            **dict(context.evidence),
            "environment_navigation_context_id": str(
                context.environment_navigation_context_id
            ),
        },
    )


def _blocked_commit_receipt(
    *,
    actor_id: UUID | None,
    environment_id: UUID,
    environment_session_id: UUID,
    reason: str,
    blockers: list[str],
    evidence: Mapping[str, Any],
    environment_navigation_context_id: UUID | None = None,
    key: str | None = None,
    is_default: bool = False,
) -> EnvironmentNavigationCommitReceiptSpec:
    return EnvironmentNavigationCommitReceiptSpec(
        accepted=False,
        status="blocked",
        error=reason,
        reason=reason,
        actor_id=actor_id,
        environment_id=environment_id,
        environment_session_id=environment_session_id,
        environment_navigation_context_id=environment_navigation_context_id,
        key=key,
        is_default=is_default,
        blockers=blockers,
        evidence=dict(evidence),
    )


def _blocked_describe_response(
    *,
    request: DescribeEnvironmentNavigationContextRequestSpec,
    actor_id: UUID | None,
    blockers: list[str],
    evidence: Mapping[str, Any],
) -> DescribeEnvironmentNavigationContextResponseSpec:
    reason = blockers[0]
    return DescribeEnvironmentNavigationContextResponseSpec(
        actor_id=actor_id,
        environment_id=request.environment_id,
        status="blocked",
        error=reason,
        blockers=blockers,
        evidence=dict(evidence),
    )


def _blocked_list_response(
    *,
    request: ListEnvironmentNavigationContextsRequestSpec,
    actor_id: UUID | None,
    blockers: list[str],
    evidence: Mapping[str, Any],
) -> ListEnvironmentNavigationContextsResponseSpec:
    reason = blockers[0]
    return ListEnvironmentNavigationContextsResponseSpec(
        actor_id=actor_id,
        environment_id=request.environment_id,
        status="blocked",
        error=reason,
        blockers=blockers,
        evidence=dict(evidence),
    )


def _normalize_context(
    context: EnvironmentNavigationContextViewSpec,
    *,
    request_environment_id: UUID,
) -> EnvironmentNavigationContextViewSpec:
    return context.model_copy(update={"environment_id": request_environment_id})


__all__ = [
    "CreateEnvironmentNavigationContextRequestSpec",
    "CreateEnvironmentNavigationContextResponseSpec",
    "DescribeEnvironmentNavigationContextRequestSpec",
    "DescribeEnvironmentNavigationContextResponseSpec",
    "EnvironmentNavigationBackend",
    "EnvironmentNavigationCommitReceiptSpec",
    "EnvironmentNavigationContextViewSpec",
    "ListEnvironmentNavigationContextsRequestSpec",
    "ListEnvironmentNavigationContextsResponseSpec",
    "SelectEnvironmentNavigationTargetRequestSpec",
    "SelectEnvironmentNavigationTargetResponseSpec",
    "create_environment_navigation_context",
    "describe_environment_navigation_context",
    "list_environment_navigation_contexts",
    "select_environment_navigation_target",
]
