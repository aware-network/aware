from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from importlib import import_module
from typing import Any, Protocol, cast
from uuid import UUID

from pydantic import BaseModel, Field
from aware_types import JsonObject
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentSessionJoinReceipt,
)
from aware_experience_service_dto.experience.actor_admission.models import (
    ExperienceActorConfigAdmissionReceipt,
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

from aware_experience.supervisor import (
    EXPERIENCE_SESSION_NARRATOR_FEATURE,
    ExperienceFeatureLeaseSnapshot,
    ExperienceSessionNarrationEventBuffer,
    ExperienceSessionScope,
    ExperienceSessionSnapshot,
    ExperienceSupervisorManager,
    experience_session_narration_event_payload,
)
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)

from aware_experience_service.supervisor_manager import (
    get_experience_narration_event_buffer,
    get_experience_supervisor_manager,
)

_IDENTITY_SERVICE_API_PACKAGE_NAME = "identity-service-api"


def _json_object(values: Mapping[str, Any]) -> JsonObject:
    return JsonObject(dict(values))


class ExperienceSessionScopeSpec(BaseModel):
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


class ExperienceSessionActorContextSpec(BaseModel):
    status: str = "ready"
    kind: str | None = None
    source: str | None = None
    actor_id: UUID | None = None
    identity_id: UUID | None = None
    execution_id: str | None = None
    provider_key: str | None = None
    provider_session_id: str | None = None
    agent_process_thread_id: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class ExperienceSessionIdentityEvidenceSpec(BaseModel):
    parent_environment_identity_session: SessionSummary | None = None
    experience_identity_session: SessionSummary | None = None
    experience_identity_member: SessionMemberSummary | None = None
    experience_identity_actor_roles: list[SessionMemberActorRoleSummary] = Field(
        default_factory=list
    )
    environment_session_join: EnvironmentSessionJoinReceipt | None = None
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class ExperienceSessionActorAdmissionSpec(BaseModel):
    contract_version: str = "aware.experience.session_actor_admission.v0"
    status: str
    admitted: bool = False
    reason: str | None = None
    session_scope: ExperienceSessionScopeSpec
    actor_context: ExperienceSessionActorContextSpec | None = None
    environment_admission: EnvironmentActorAdmissionReceipt | None = None
    environment_session_join: EnvironmentSessionJoinReceipt | None = None
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = None
    experience_identity_session_config_id: UUID | None = None
    identity_evidence: ExperienceSessionIdentityEvidenceSpec | None = None
    actor_id: UUID | None = None
    actor_kind: str | None = None
    identity_id: UUID | None = None
    execution_id: str | None = None
    provider_key: str | None = None
    provider_session_id: str | None = None
    agent_process_thread_id: str | None = None
    blockers: list[str] = Field(default_factory=list)
    next_suggested_action: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class AdmitExperienceSessionActorRequest(BaseModel):
    request_id: UUID | None = None
    session_scope: ExperienceSessionScopeSpec
    actor_context: ExperienceSessionActorContextSpec | None = None
    environment_admission: EnvironmentActorAdmissionReceipt | None = None
    environment_session_join: EnvironmentSessionJoinReceipt | None = None
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = None
    experience_identity_session_config_id: UUID | None = None
    idempotency_key: str | None = None


class GetExperienceSessionActorAdmissionRequest(BaseModel):
    session_scope: ExperienceSessionScopeSpec
    actor_id: UUID | None = None


class EnsureExperienceSessionFeatureRequest(BaseModel):
    session_scope: ExperienceSessionScopeSpec
    feature_key: str
    config: dict[str, Any] = Field(default_factory=dict)
    lease_key: str | None = None


class ReleaseExperienceSessionFeatureRequest(BaseModel):
    session_scope: ExperienceSessionScopeSpec
    feature_key: str
    lease_key: str | None = None


class GetExperienceSessionSnapshotRequest(BaseModel):
    session_scope: ExperienceSessionScopeSpec


class ExperienceFeatureLeaseSnapshotSpec(BaseModel):
    lease_key: str
    session_scope: ExperienceSessionScopeSpec
    feature_key: str
    desired_state: str
    worker_status: str
    revision: int
    info: str | None = None
    last_error: str | None = None
    health_payload: dict[str, Any] | None = None


class ExperienceSessionSnapshotSpec(BaseModel):
    session_scope: ExperienceSessionScopeSpec
    feature_lease_count: int
    leases: list[ExperienceFeatureLeaseSnapshotSpec] = Field(default_factory=list)
    actor_admission: ExperienceSessionActorAdmissionSpec | None = None


class AdmitExperienceSessionActorResponse(BaseModel):
    accepted: bool
    admission: ExperienceSessionActorAdmissionSpec


class GetExperienceSessionActorAdmissionResponse(BaseModel):
    accepted: bool
    admission: ExperienceSessionActorAdmissionSpec | None = None
    error: str | None = None


class EnsureExperienceSessionFeatureResponse(BaseModel):
    accepted: bool
    snapshot: ExperienceFeatureLeaseSnapshotSpec | None = None
    error: str | None = None
    actor_admission: ExperienceSessionActorAdmissionSpec | None = None


class ReleaseExperienceSessionFeatureResponse(BaseModel):
    accepted: bool
    snapshot: ExperienceFeatureLeaseSnapshotSpec | None = None
    error: str | None = None
    actor_admission: ExperienceSessionActorAdmissionSpec | None = None


class GetExperienceSessionSnapshotResponse(BaseModel):
    accepted: bool
    snapshot: ExperienceSessionSnapshotSpec | None = None
    error: str | None = None


class ExperienceSessionActorAdmissionRegistry:
    def __init__(self) -> None:
        self._admissions: dict[str, ExperienceSessionActorAdmissionSpec] = {}

    def admit(
        self,
        *,
        request: AdmitExperienceSessionActorRequest,
    ) -> ExperienceSessionActorAdmissionSpec:
        admission = _build_actor_admission(request=request)
        self._admissions[
            _admission_key(
                admission.session_scope,
                admission.actor_id or request.session_scope.actor_id,
            )
        ] = admission
        return admission

    def record(
        self,
        *,
        admission: ExperienceSessionActorAdmissionSpec,
    ) -> ExperienceSessionActorAdmissionSpec:
        self._admissions[
            _admission_key(
                admission.session_scope,
                admission.actor_id or admission.session_scope.actor_id,
            )
        ] = admission
        return admission

    def get(
        self,
        *,
        session_scope: ExperienceSessionScopeSpec,
        actor_id: UUID | None = None,
    ) -> ExperienceSessionActorAdmissionSpec | None:
        return self._admissions.get(_admission_key(session_scope, actor_id))


_DEFAULT_ACTOR_ADMISSION_REGISTRY = ExperienceSessionActorAdmissionRegistry()


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


class _IdentityExperienceSessionApi(Protocol):
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


class IdentityExperienceSessionApiClient(Protocol):
    @property
    def identity(self) -> _IdentityExperienceSessionApi: ...


async def admit_experience_session_actor(
    *,
    request: AdmitExperienceSessionActorRequest,
    host_context: ServiceApiHostContext,
    admission_registry: ExperienceSessionActorAdmissionRegistry | None = None,
    identity_api_client: IdentityExperienceSessionApiClient | None = None,
) -> AdmitExperienceSessionActorResponse:
    registry = admission_registry or _DEFAULT_ACTOR_ADMISSION_REGISTRY
    admission = _build_actor_admission(request=request)
    if admission.admitted:
        identity_client = identity_api_client or _build_identity_service_api_client(
            host_context=host_context,
        )
        identity_blocker = _identity_client_blocker(identity_client)
        if identity_blocker is not None:
            admission = _blocked_actor_admission(
                session_scope=request.session_scope,
                actor_context=request.actor_context,
                environment_admission=request.environment_admission,
                environment_session_join=request.environment_session_join,
                experience_actor_admission=request.experience_actor_admission,
                experience_identity_session_config_id=(
                    request.experience_identity_session_config_id
                ),
                reason=identity_blocker,
                blockers=[identity_blocker],
                next_suggested_action="resolve_identity_session_api",
                evidence={
                    **dict(admission.evidence),
                    "identity_session_required": True,
                },
            )
        else:
            assert identity_client is not None
            identity_evidence = await _ensure_experience_identity_evidence(
                request=request,
                admission=admission,
                identity_client=identity_client,
            )
            admission = admission.model_copy(
                update={
                    "identity_evidence": identity_evidence,
                    "evidence": {
                        **dict(admission.evidence),
                        "experience_identity_session_id": (
                            str(
                                identity_evidence.experience_identity_session.session_id
                            )
                            if identity_evidence.experience_identity_session is not None
                            else None
                        ),
                        "experience_identity_member_id": (
                            str(
                                identity_evidence.experience_identity_member.session_member_id
                            )
                            if identity_evidence.experience_identity_member is not None
                            else None
                        ),
                        "experience_identity_actor_role_count": len(
                            identity_evidence.experience_identity_actor_roles
                        ),
                    },
                }
            )
    registry.record(admission=admission)
    return AdmitExperienceSessionActorResponse(
        accepted=admission.admitted,
        admission=admission,
    )


async def get_experience_session_actor_admission(
    *,
    request: GetExperienceSessionActorAdmissionRequest,
    host_context: ServiceApiHostContext,
    admission_registry: ExperienceSessionActorAdmissionRegistry | None = None,
) -> GetExperienceSessionActorAdmissionResponse:
    _ = host_context
    registry = admission_registry or _DEFAULT_ACTOR_ADMISSION_REGISTRY
    admission = registry.get(
        session_scope=request.session_scope,
        actor_id=request.actor_id,
    )
    if admission is None:
        return GetExperienceSessionActorAdmissionResponse(
            accepted=False,
            error="Experience session actor admission was not found.",
        )
    return GetExperienceSessionActorAdmissionResponse(
        accepted=admission.admitted,
        admission=admission,
    )


async def ensure_experience_session_feature(
    *,
    request: EnsureExperienceSessionFeatureRequest,
    host_context: ServiceApiHostContext,
    manager: ExperienceSupervisorManager | None = None,
    admission_registry: ExperienceSessionActorAdmissionRegistry | None = None,
) -> EnsureExperienceSessionFeatureResponse:
    actor_admission = _require_admitted_actor(
        session_scope=request.session_scope,
        admission_registry=admission_registry,
    )
    if not actor_admission.admitted:
        return EnsureExperienceSessionFeatureResponse(
            accepted=False,
            error=actor_admission.reason or "Experience session actor is not admitted.",
            actor_admission=actor_admission,
        )
    resolved_manager = manager or get_experience_supervisor_manager(
        host_context=host_context,
    )
    try:
        snapshot = await resolved_manager.ensure_feature(
            session_scope=_scope_from_spec(request.session_scope),
            feature_key=request.feature_key,
            config=request.config,
            lease_key=request.lease_key,
        )
    except ValueError as exc:
        return EnsureExperienceSessionFeatureResponse(
            accepted=False,
            error=str(exc),
            actor_admission=actor_admission,
        )
    return EnsureExperienceSessionFeatureResponse(
        accepted=True,
        snapshot=_feature_snapshot_spec(snapshot),
        actor_admission=actor_admission,
    )


async def release_experience_session_feature(
    *,
    request: ReleaseExperienceSessionFeatureRequest,
    host_context: ServiceApiHostContext,
    manager: ExperienceSupervisorManager | None = None,
    admission_registry: ExperienceSessionActorAdmissionRegistry | None = None,
) -> ReleaseExperienceSessionFeatureResponse:
    actor_admission = _require_admitted_actor(
        session_scope=request.session_scope,
        admission_registry=admission_registry,
    )
    if not actor_admission.admitted:
        return ReleaseExperienceSessionFeatureResponse(
            accepted=False,
            error=actor_admission.reason or "Experience session actor is not admitted.",
            actor_admission=actor_admission,
        )
    resolved_manager = manager or get_experience_supervisor_manager(
        host_context=host_context,
    )
    snapshot = await resolved_manager.release_feature(
        session_scope=_scope_from_spec(request.session_scope),
        feature_key=request.feature_key,
        lease_key=request.lease_key,
    )
    if snapshot is None:
        return ReleaseExperienceSessionFeatureResponse(
            accepted=False,
            error="Experience session feature lease was not found.",
            actor_admission=actor_admission,
        )
    return ReleaseExperienceSessionFeatureResponse(
        accepted=True,
        snapshot=_feature_snapshot_spec(snapshot),
        actor_admission=actor_admission,
    )


async def get_experience_session_snapshot(
    *,
    request: GetExperienceSessionSnapshotRequest,
    host_context: ServiceApiHostContext,
    manager: ExperienceSupervisorManager | None = None,
    admission_registry: ExperienceSessionActorAdmissionRegistry | None = None,
    narration_event_buffer: ExperienceSessionNarrationEventBuffer | None = None,
) -> GetExperienceSessionSnapshotResponse:
    resolved_manager = manager or get_experience_supervisor_manager(
        host_context=host_context,
    )
    resolved_narration_event_buffer = narration_event_buffer
    if resolved_narration_event_buffer is None and manager is None:
        resolved_narration_event_buffer = get_experience_narration_event_buffer(
            host_context=host_context,
        )
    snapshot = await resolved_manager.get_session_snapshot(
        session_scope=_scope_from_spec(request.session_scope),
    )
    return GetExperienceSessionSnapshotResponse(
        accepted=True,
        snapshot=_session_snapshot_spec(
            snapshot,
            actor_admission=_current_actor_admission(
                session_scope=request.session_scope,
                admission_registry=admission_registry,
            ),
            narration_event_buffer=resolved_narration_event_buffer,
        ),
    )


def _scope_from_spec(spec: ExperienceSessionScopeSpec) -> ExperienceSessionScope:
    return ExperienceSessionScope(
        experience_name=spec.experience_name,
        profile_key=spec.profile_key,
        environment_id=spec.environment_id,
        environment_session_id=spec.environment_session_id,
        actor_id=spec.actor_id,
        process_id=spec.process_id,
        thread_id=spec.thread_id,
        branch_id=spec.branch_id,
        projection_hash=spec.projection_hash,
        workspace_session_id=spec.workspace_session_id,
    )


def _scope_spec(scope: ExperienceSessionScope) -> ExperienceSessionScopeSpec:
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


def _session_snapshot_spec(
    snapshot: ExperienceSessionSnapshot,
    *,
    actor_admission: ExperienceSessionActorAdmissionSpec | None = None,
    narration_event_buffer: ExperienceSessionNarrationEventBuffer | None = None,
) -> ExperienceSessionSnapshotSpec:
    return ExperienceSessionSnapshotSpec(
        session_scope=_scope_spec(snapshot.session_scope),
        feature_lease_count=snapshot.feature_lease_count,
        leases=[
            _feature_snapshot_spec(
                lease,
                narration_event_buffer=narration_event_buffer,
            )
            for lease in snapshot.leases
        ],
        actor_admission=actor_admission,
    )


def _feature_snapshot_spec(
    snapshot: ExperienceFeatureLeaseSnapshot,
    *,
    narration_event_buffer: ExperienceSessionNarrationEventBuffer | None = None,
) -> ExperienceFeatureLeaseSnapshotSpec:
    return ExperienceFeatureLeaseSnapshotSpec(
        lease_key=snapshot.lease_key,
        session_scope=_scope_spec(snapshot.session_scope),
        feature_key=snapshot.feature_key,
        desired_state=snapshot.desired_state,
        worker_status=snapshot.worker_status,
        revision=snapshot.revision,
        info=snapshot.info,
        last_error=snapshot.last_error,
        health_payload=_feature_health_payload(
            snapshot,
            narration_event_buffer=narration_event_buffer,
        ),
    )


def _feature_health_payload(
    snapshot: ExperienceFeatureLeaseSnapshot,
    *,
    narration_event_buffer: ExperienceSessionNarrationEventBuffer | None,
) -> dict[str, Any] | None:
    payload = _health_payload(snapshot.health)
    if (
        snapshot.feature_key != EXPERIENCE_SESSION_NARRATOR_FEATURE
        or narration_event_buffer is None
    ):
        return payload
    events = narration_event_buffer.recent_events(
        lease_key=snapshot.lease_key,
        limit=25,
    )
    enriched: dict[str, Any] = dict(payload or {})
    enriched.setdefault("status", snapshot.worker_status)
    enriched["event_count"] = len(events)
    enriched["events"] = [
        experience_session_narration_event_payload(event) for event in events
    ]
    if events:
        enriched["last_commit_id"] = str(events[-1].commit_id)
    return enriched


def _health_payload(value: object | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if is_dataclass(value) and not isinstance(value, type):
        return dict(asdict(value))
    if isinstance(value, dict):
        return dict(value)
    return {"value": value}


def _build_actor_admission(
    *,
    request: AdmitExperienceSessionActorRequest,
) -> ExperienceSessionActorAdmissionSpec:
    scope = request.session_scope
    context = request.actor_context
    environment_admission = request.environment_admission
    base_evidence = {
        "source": "aware_experience_service.session_actor_admission",
    }
    environment_blocker = _environment_admission_blocker(
        session_scope=scope,
        actor_context=context,
        environment_admission=environment_admission,
    )
    if environment_blocker is not None:
        reason, blockers, next_action = environment_blocker
        return _blocked_actor_admission(
            session_scope=scope,
            actor_context=context,
            environment_admission=environment_admission,
            reason=reason,
            blockers=blockers,
            next_suggested_action=next_action,
            evidence=base_evidence,
        )
    environment_session_blocker = _environment_session_join_blocker(
        session_scope=scope,
        actor_context=context,
        environment_admission=environment_admission,
        environment_session_join=request.environment_session_join,
    )
    if environment_session_blocker is not None:
        reason, blockers, next_action = environment_session_blocker
        return _blocked_actor_admission(
            session_scope=scope,
            actor_context=context,
            environment_admission=environment_admission,
            environment_session_join=request.environment_session_join,
            experience_actor_admission=request.experience_actor_admission,
            experience_identity_session_config_id=(
                request.experience_identity_session_config_id
            ),
            reason=reason,
            blockers=blockers,
            next_suggested_action=next_action,
            evidence=base_evidence,
        )
    experience_actor_blocker = _experience_actor_admission_blocker(
        session_scope=scope,
        actor_context=context,
        experience_actor_admission=request.experience_actor_admission,
    )
    if experience_actor_blocker is not None:
        reason, blockers, next_action = experience_actor_blocker
        return _blocked_actor_admission(
            session_scope=scope,
            actor_context=context,
            environment_admission=environment_admission,
            environment_session_join=request.environment_session_join,
            experience_actor_admission=request.experience_actor_admission,
            experience_identity_session_config_id=(
                request.experience_identity_session_config_id
            ),
            reason=reason,
            blockers=blockers,
            next_suggested_action=next_action,
            evidence=base_evidence,
        )
    if request.experience_identity_session_config_id is None:
        return _blocked_actor_admission(
            session_scope=scope,
            actor_context=context,
            environment_admission=environment_admission,
            environment_session_join=request.environment_session_join,
            experience_actor_admission=request.experience_actor_admission,
            experience_identity_session_config_id=None,
            reason="missing_experience_identity_session_config_id",
            blockers=["experience_identity_session_config_id_missing"],
            next_suggested_action="resolve_experience_identity_session_config",
            evidence=base_evidence,
        )
    if context is None:
        return _blocked_actor_admission(
            session_scope=scope,
            actor_context=None,
            environment_admission=environment_admission,
            reason="missing_actor_context",
            blockers=["actor_context_missing"],
            next_suggested_action="resolve_identity",
            evidence=base_evidence,
        )
    if context.status != "ready":
        return _blocked_actor_admission(
            session_scope=scope,
            actor_context=context,
            environment_admission=environment_admission,
            reason="actor_context_not_ready",
            blockers=["actor_context_not_ready"],
            next_suggested_action="resolve_identity",
            evidence=base_evidence,
        )
    if context.kind not in {
        "agent_operator",
        "human_identity",
        "service_actor",
        "experience_service",
    }:
        return _blocked_actor_admission(
            session_scope=scope,
            actor_context=context,
            environment_admission=environment_admission,
            reason="invalid_actor_context_kind",
            blockers=["actor_context_kind_invalid"],
            next_suggested_action="resolve_identity",
            evidence=base_evidence,
        )
    if context.actor_id is None:
        return _blocked_actor_admission(
            session_scope=scope,
            actor_context=context,
            environment_admission=environment_admission,
            reason="missing_actor_id",
            blockers=["actor_id_missing"],
            next_suggested_action="resolve_identity",
            evidence=base_evidence,
        )
    if scope.actor_id is None:
        return _blocked_actor_admission(
            session_scope=scope,
            actor_context=context,
            environment_admission=environment_admission,
            reason="missing_session_scope_actor_id",
            blockers=["session_scope_actor_id_missing"],
            next_suggested_action="bind_session_actor",
            evidence=base_evidence,
        )
    if context.actor_id != scope.actor_id:
        return _blocked_actor_admission(
            session_scope=scope,
            actor_context=context,
            environment_admission=environment_admission,
            reason="actor_scope_mismatch",
            blockers=["session_actor_scope_mismatch"],
            next_suggested_action="bind_session_actor",
            evidence=base_evidence,
        )
    return ExperienceSessionActorAdmissionSpec(
        status="admitted",
        admitted=True,
        session_scope=scope,
        actor_context=context,
        environment_admission=environment_admission,
        environment_session_join=request.environment_session_join,
        experience_actor_admission=request.experience_actor_admission,
        experience_identity_session_config_id=(
            request.experience_identity_session_config_id
        ),
        actor_id=context.actor_id,
        actor_kind=context.kind,
        identity_id=context.identity_id,
        execution_id=context.execution_id,
        provider_key=context.provider_key,
        provider_session_id=context.provider_session_id,
        agent_process_thread_id=context.agent_process_thread_id,
        evidence={
            **base_evidence,
            "actor_context_source": context.source,
            "actor_context_status": context.status,
            "environment_admission_status": (
                environment_admission.status
                if environment_admission is not None
                else None
            ),
            "environment_admission_binding_count": (
                len(environment_admission.bindings)
                if environment_admission is not None
                else 0
            ),
            "environment_profile_id": (
                str(environment_admission.environment_profile_id)
                if environment_admission is not None
                else None
            ),
            "environment_session_id": (
                str(request.environment_session_join.environment_session_id)
                if request.environment_session_join is not None
                else None
            ),
            "experience_actor_admission_status": (
                request.experience_actor_admission.status
                if request.experience_actor_admission is not None
                else None
            ),
            "experience_actor_admission_binding_count": (
                len(request.experience_actor_admission.bindings)
                if request.experience_actor_admission is not None
                else 0
            ),
        },
    )


def _environment_admission_blocker(
    *,
    session_scope: ExperienceSessionScopeSpec,
    actor_context: ExperienceSessionActorContextSpec | None,
    environment_admission: EnvironmentActorAdmissionReceipt | None,
) -> tuple[str, list[str], str] | None:
    if session_scope.environment_id is None:
        return (
            "missing_environment_scope",
            ["session_scope_environment_id_missing"],
            "admit_environment_actor",
        )
    if environment_admission is None:
        return (
            "missing_environment_admission",
            ["environment_admission_missing"],
            "admit_environment_actor",
        )
    if not environment_admission.accepted or environment_admission.status != "admitted":
        return (
            environment_admission.error
            or environment_admission.reason
            or "environment_actor_not_admitted",
            ["environment_actor_not_admitted", *environment_admission.blockers],
            "admit_environment_actor",
        )
    if not environment_admission.bindings:
        return (
            "environment_admission_has_no_role_bindings",
            ["environment_actor_role_binding_missing"],
            "admit_environment_actor",
        )
    if environment_admission.actor_id != session_scope.actor_id:
        return (
            "environment_admission_actor_scope_mismatch",
            ["environment_admission_actor_scope_mismatch"],
            "admit_environment_actor",
        )
    if (
        actor_context is not None
        and actor_context.actor_id is not None
        and environment_admission.actor_id != actor_context.actor_id
    ):
        return (
            "environment_admission_actor_context_mismatch",
            ["environment_admission_actor_context_mismatch"],
            "resolve_identity",
        )
    if environment_admission.environment_id != session_scope.environment_id:
        return (
            "environment_admission_environment_scope_mismatch",
            ["environment_admission_environment_scope_mismatch"],
            "admit_environment_actor",
        )
    return None


def _environment_session_join_blocker(
    *,
    session_scope: ExperienceSessionScopeSpec,
    actor_context: ExperienceSessionActorContextSpec | None,
    environment_admission: EnvironmentActorAdmissionReceipt | None,
    environment_session_join: EnvironmentSessionJoinReceipt | None,
) -> tuple[str, list[str], str] | None:
    if environment_session_join is None:
        return (
            "missing_environment_session_join",
            ["environment_session_join_missing"],
            "join_environment_session",
        )
    if (
        not environment_session_join.accepted
        or environment_session_join.status != "joined"
    ):
        return (
            environment_session_join.error
            or environment_session_join.reason
            or "environment_session_not_joined",
            ["environment_session_not_joined", *environment_session_join.blockers],
            "join_environment_session",
        )
    if environment_session_join.environment_session_id is None:
        return (
            "environment_session_join_session_id_missing",
            ["environment_session_join_session_id_missing"],
            "join_environment_session",
        )
    if session_scope.environment_session_id is not None and (
        environment_session_join.environment_session_id
        != session_scope.environment_session_id
    ):
        return (
            "environment_session_join_scope_mismatch",
            ["environment_session_join_scope_mismatch"],
            "join_environment_session",
        )
    if environment_session_join.actor_id != session_scope.actor_id:
        return (
            "environment_session_join_actor_scope_mismatch",
            ["environment_session_join_actor_scope_mismatch"],
            "join_environment_session",
        )
    if (
        actor_context is not None
        and actor_context.actor_id is not None
        and environment_session_join.actor_id != actor_context.actor_id
    ):
        return (
            "environment_session_join_actor_context_mismatch",
            ["environment_session_join_actor_context_mismatch"],
            "resolve_identity",
        )
    if environment_session_join.environment_id != session_scope.environment_id:
        return (
            "environment_session_join_environment_scope_mismatch",
            ["environment_session_join_environment_scope_mismatch"],
            "join_environment_session",
        )
    if environment_admission is not None:
        if (
            environment_session_join.environment_id
            != environment_admission.environment_id
        ):
            return (
                "environment_session_join_admission_environment_mismatch",
                ["environment_session_join_admission_environment_mismatch"],
                "join_environment_session",
            )
        if (
            environment_session_join.environment_profile_id
            != environment_admission.environment_profile_id
        ):
            return (
                "environment_session_join_admission_profile_mismatch",
                ["environment_session_join_admission_profile_mismatch"],
                "join_environment_session",
            )
    identity_evidence = environment_session_join.identity_evidence
    if identity_evidence is None:
        return (
            "environment_session_join_identity_evidence_missing",
            ["environment_session_join_identity_evidence_missing"],
            "join_environment_session",
        )
    if identity_evidence.identity_session is None:
        return (
            "environment_session_join_identity_session_missing",
            ["environment_session_join_identity_session_missing"],
            "join_environment_session",
        )
    if identity_evidence.identity_member is None:
        return (
            "environment_session_join_identity_member_missing",
            ["environment_session_join_identity_member_missing"],
            "join_environment_session",
        )
    if identity_evidence.identity_member.actor_id != session_scope.actor_id:
        return (
            "environment_session_join_identity_member_actor_mismatch",
            ["environment_session_join_identity_member_actor_mismatch"],
            "join_environment_session",
        )
    if identity_evidence.identity_member.status != "active":
        return (
            "environment_session_join_identity_member_inactive",
            ["environment_session_join_identity_member_inactive"],
            "join_environment_session",
        )
    return None


def _experience_actor_admission_blocker(
    *,
    session_scope: ExperienceSessionScopeSpec,
    actor_context: ExperienceSessionActorContextSpec | None,
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None,
) -> tuple[str, list[str], str] | None:
    if experience_actor_admission is None:
        return (
            "missing_experience_actor_admission",
            ["experience_actor_admission_missing"],
            "admit_experience_actor_config",
        )
    if (
        not experience_actor_admission.accepted
        or experience_actor_admission.status != "admitted"
    ):
        return (
            experience_actor_admission.reason or "experience_actor_not_admitted",
            ["experience_actor_not_admitted", *experience_actor_admission.blockers],
            "admit_experience_actor_config",
        )
    if experience_actor_admission.experience_name != session_scope.experience_name:
        return (
            "experience_actor_admission_name_mismatch",
            ["experience_actor_admission_name_mismatch"],
            "admit_experience_actor_config",
        )
    if experience_actor_admission.actor_id != session_scope.actor_id:
        return (
            "experience_actor_admission_actor_scope_mismatch",
            ["experience_actor_admission_actor_scope_mismatch"],
            "admit_experience_actor_config",
        )
    if (
        actor_context is not None
        and actor_context.actor_id is not None
        and experience_actor_admission.actor_id != actor_context.actor_id
    ):
        return (
            "experience_actor_admission_actor_context_mismatch",
            ["experience_actor_admission_actor_context_mismatch"],
            "resolve_identity",
        )
    if experience_actor_admission.actor_config_id is None:
        return (
            "experience_actor_admission_actor_config_missing",
            ["experience_actor_admission_actor_config_missing"],
            "admit_experience_actor_config",
        )
    if not experience_actor_admission.bindings:
        return (
            "experience_actor_admission_has_no_role_bindings",
            ["experience_actor_role_binding_missing"],
            "admit_experience_actor_config",
        )
    if any(
        binding.actor_id != experience_actor_admission.actor_id
        for binding in experience_actor_admission.bindings
    ):
        return (
            "experience_actor_admission_binding_actor_mismatch",
            ["experience_actor_admission_binding_actor_mismatch"],
            "admit_experience_actor_config",
        )
    return None


def _blocked_actor_admission(
    *,
    session_scope: ExperienceSessionScopeSpec,
    actor_context: ExperienceSessionActorContextSpec | None,
    environment_admission: EnvironmentActorAdmissionReceipt | None,
    environment_session_join: EnvironmentSessionJoinReceipt | None = None,
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = None,
    experience_identity_session_config_id: UUID | None = None,
    reason: str,
    blockers: list[str],
    next_suggested_action: str,
    evidence: dict[str, Any],
) -> ExperienceSessionActorAdmissionSpec:
    return ExperienceSessionActorAdmissionSpec(
        status="blocked",
        admitted=False,
        reason=reason,
        session_scope=session_scope,
        actor_context=actor_context,
        environment_admission=environment_admission,
        environment_session_join=environment_session_join,
        experience_actor_admission=experience_actor_admission,
        experience_identity_session_config_id=experience_identity_session_config_id,
        actor_id=actor_context.actor_id if actor_context is not None else None,
        actor_kind=actor_context.kind if actor_context is not None else None,
        identity_id=actor_context.identity_id if actor_context is not None else None,
        execution_id=actor_context.execution_id if actor_context is not None else None,
        provider_key=actor_context.provider_key if actor_context is not None else None,
        provider_session_id=(
            actor_context.provider_session_id if actor_context is not None else None
        ),
        agent_process_thread_id=(
            actor_context.agent_process_thread_id if actor_context is not None else None
        ),
        blockers=blockers,
        next_suggested_action=next_suggested_action,
        evidence={
            **evidence,
            "environment_admission_required": True,
            "environment_admission_status": (
                environment_admission.status
                if environment_admission is not None
                else None
            ),
            "environment_session_join_status": (
                environment_session_join.status
                if environment_session_join is not None
                else None
            ),
            "experience_actor_admission_status": (
                experience_actor_admission.status
                if experience_actor_admission is not None
                else None
            ),
            "actor_context_source": (
                actor_context.source if actor_context is not None else None
            ),
            "actor_context_status": (
                actor_context.status if actor_context is not None else None
            ),
        },
    )


def _require_admitted_actor(
    *,
    session_scope: ExperienceSessionScopeSpec,
    admission_registry: ExperienceSessionActorAdmissionRegistry | None,
) -> ExperienceSessionActorAdmissionSpec:
    admission = _current_actor_admission(
        session_scope=session_scope,
        admission_registry=admission_registry,
    )
    if admission is not None:
        return admission
    return _blocked_actor_admission(
        session_scope=session_scope,
        actor_context=None,
        environment_admission=None,
        reason="missing_session_actor_admission",
        blockers=["session_actor_not_admitted"],
        next_suggested_action="admit_experience_session_actor",
        evidence={
            "source": "aware_experience_service.session_actor_admission",
        },
    )


def _current_actor_admission(
    *,
    session_scope: ExperienceSessionScopeSpec,
    admission_registry: ExperienceSessionActorAdmissionRegistry | None,
) -> ExperienceSessionActorAdmissionSpec | None:
    registry = admission_registry or _DEFAULT_ACTOR_ADMISSION_REGISTRY
    return registry.get(
        session_scope=session_scope,
        actor_id=session_scope.actor_id,
    )


def _admission_key(
    session_scope: ExperienceSessionScopeSpec,
    actor_id: UUID | None,
) -> str:
    scope_parts = (
        session_scope.experience_name,
        session_scope.profile_key,
        session_scope.environment_id,
        session_scope.environment_session_id,
        actor_id,
        session_scope.process_id,
        session_scope.thread_id,
        session_scope.branch_id,
        session_scope.projection_hash,
        session_scope.workspace_session_id,
    )
    return ":".join(str(part) if part is not None else "-" for part in scope_parts)


async def _ensure_experience_identity_evidence(
    *,
    request: AdmitExperienceSessionActorRequest,
    admission: ExperienceSessionActorAdmissionSpec,
    identity_client: IdentityExperienceSessionApiClient,
) -> ExperienceSessionIdentityEvidenceSpec:
    assert request.environment_session_join is not None
    assert request.environment_session_join.identity_evidence is not None
    assert (
        request.environment_session_join.identity_evidence.identity_session is not None
    )
    assert request.experience_actor_admission is not None
    assert request.experience_actor_admission.actor_config_id is not None
    assert request.experience_identity_session_config_id is not None
    assert admission.actor_id is not None

    parent_session = request.environment_session_join.identity_evidence.identity_session
    environment_session_id = request.environment_session_join.environment_session_id
    child_session = await _start_experience_identity_session(
        request=request,
        actor_id=admission.actor_id,
        parent_session=parent_session,
        environment_session_id=environment_session_id,
        identity_client=identity_client,
    )
    binding_receipt = await identity_client.identity.bind_session_config_actor_config.bind_session_config_actor_config(
        SessionConfigActorConfigBindRequest(
            session_config_id=child_session.session_config_id,
            actor_config_id=request.experience_actor_admission.actor_config_id,
            purpose="experience_session_participant",
            metadata_json=_json_object(
                {
                    "experience_name": admission.session_scope.experience_name,
                    "environment_id": str(admission.session_scope.environment_id),
                    "environment_session_id": (
                        str(environment_session_id)
                        if environment_session_id is not None
                        else None
                    ),
                }
            ),
            request_id=request.request_id,
        )
    )
    join_receipt = await identity_client.identity.join_session.join_session(
        SessionJoinRequest(
            session_id=child_session.session_id,
            actor_id=admission.actor_id,
            session_actor_config_id=(
                binding_receipt.binding.session_config_actor_config_id
            ),
            metadata_json=_json_object(
                {
                    "experience_name": admission.session_scope.experience_name,
                    "environment_id": str(admission.session_scope.environment_id),
                    "environment_session_id": (
                        str(environment_session_id)
                        if environment_session_id is not None
                        else None
                    ),
                    "parent_environment_identity_session_id": str(
                        parent_session.session_id
                    ),
                }
            ),
            request_id=request.request_id,
        )
    )
    actor_roles: list[SessionMemberActorRoleSummary] = []
    for actor_binding in request.experience_actor_admission.bindings:
        role_receipt = await identity_client.identity.record_session_member_actor_role.record_session_member_actor_role(
            SessionMemberActorRoleRecordRequest(
                session_id=child_session.session_id,
                session_member_id=join_receipt.member.session_member_id,
                actor_role_id=actor_binding.actor_role_id,
                source_kind="experience_actor_admission",
                evidence_json=_json_object(
                    {
                        "experience_name": admission.session_scope.experience_name,
                        "environment_id": str(admission.session_scope.environment_id),
                        "environment_session_id": (
                            str(environment_session_id)
                            if environment_session_id is not None
                            else None
                        ),
                        "role_config_id": str(actor_binding.role_config_id),
                        "role_config_name": actor_binding.role_config_name,
                        "experience_actor_config_id": str(
                            request.experience_actor_admission.actor_config_id
                        ),
                    }
                ),
                request_id=request.request_id,
            )
        )
        actor_roles.append(role_receipt.actor_role)
    member = join_receipt.member.model_copy(update={"actor_roles": actor_roles})
    child_session = child_session.model_copy(
        update={"member_count": max(child_session.member_count, 1)}
    )
    return ExperienceSessionIdentityEvidenceSpec(
        parent_environment_identity_session=parent_session,
        experience_identity_session=child_session,
        experience_identity_member=member,
        experience_identity_actor_roles=actor_roles,
        environment_session_join=request.environment_session_join,
        experience_actor_admission=request.experience_actor_admission,
        evidence={
            "source": "aware_experience_service.session_actor_admission",
            "parent_environment_identity_session_id": str(parent_session.session_id),
            "experience_identity_session_id": str(child_session.session_id),
            "experience_identity_member_id": str(member.session_member_id),
            "experience_identity_actor_role_count": len(actor_roles),
        },
    )


async def _start_experience_identity_session(
    *,
    request: AdmitExperienceSessionActorRequest,
    actor_id: UUID,
    parent_session: SessionSummary,
    environment_session_id: UUID | None,
    identity_client: IdentityExperienceSessionApiClient,
) -> SessionSummary:
    key = request.idempotency_key or _experience_identity_session_key(
        session_scope=request.session_scope,
        actor_id=actor_id,
        environment_session_id=environment_session_id,
    )
    receipt = await identity_client.identity.start_session.start_session(
        SessionStartRequest(
            session_config_id=cast(UUID, request.experience_identity_session_config_id),
            key=key,
            parent_session_id=parent_session.session_id,
            title=f"{request.session_scope.experience_name} experience session",
            purpose="experience_session",
            created_by_actor_id=actor_id,
            source_kind="experience_session_handoff",
            source_ref=(
                str(environment_session_id)
                if environment_session_id is not None
                else request.session_scope.experience_name
            ),
            metadata_json=_json_object(
                {
                    "experience_name": request.session_scope.experience_name,
                    "environment_id": str(request.session_scope.environment_id),
                    "environment_session_id": (
                        str(environment_session_id)
                        if environment_session_id is not None
                        else None
                    ),
                    "parent_environment_identity_session_id": str(
                        parent_session.session_id
                    ),
                }
            ),
            request_id=request.request_id,
        )
    )
    return receipt.session


def _experience_identity_session_key(
    *,
    session_scope: ExperienceSessionScopeSpec,
    actor_id: UUID,
    environment_session_id: UUID | None,
) -> str:
    environment_session_part = (
        str(environment_session_id) if environment_session_id is not None else "-"
    )
    return (
        f"experience:{session_scope.experience_name}:"
        f"environment-session:{environment_session_part}:"
        f"actor:{actor_id}"
    )


def _identity_client_blocker(
    identity_client: IdentityExperienceSessionApiClient | None,
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


def _build_identity_service_api_client(
    *,
    host_context: ServiceApiHostContext,
) -> IdentityExperienceSessionApiClient | None:
    invoker = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name=_IDENTITY_SERVICE_API_PACKAGE_NAME,
        actor_id=host_context.operation_context.actor_id,
        invocation_context=_host_invocation_context_payload(host_context),
    )
    if invoker is None:
        return None
    return cast(
        IdentityExperienceSessionApiClient,
        _identity_api_client_model()(invoker),
    )


def _identity_api_client_model() -> type[Any]:
    module = import_module("aware_" + "identity" + "_service_api")
    return cast(type[Any], getattr(module, "AwareIdentityServiceApiClient"))


def _host_invocation_context_payload(
    host_context: ServiceApiHostContext,
) -> JsonObject | None:
    if host_context.invocation_context is None:
        return None
    return _json_object(host_context.invocation_context)


__all__ = [
    "AdmitExperienceSessionActorRequest",
    "AdmitExperienceSessionActorResponse",
    "EnsureExperienceSessionFeatureRequest",
    "EnsureExperienceSessionFeatureResponse",
    "ExperienceSessionActorAdmissionRegistry",
    "ExperienceSessionActorAdmissionSpec",
    "ExperienceSessionActorContextSpec",
    "ExperienceFeatureLeaseSnapshotSpec",
    "ExperienceSessionIdentityEvidenceSpec",
    "ExperienceSessionScopeSpec",
    "ExperienceSessionSnapshotSpec",
    "GetExperienceSessionActorAdmissionRequest",
    "GetExperienceSessionActorAdmissionResponse",
    "GetExperienceSessionSnapshotRequest",
    "GetExperienceSessionSnapshotResponse",
    "IdentityExperienceSessionApiClient",
    "ReleaseExperienceSessionFeatureRequest",
    "ReleaseExperienceSessionFeatureResponse",
    "admit_experience_session_actor",
    "ensure_experience_session_feature",
    "get_experience_session_actor_admission",
    "get_experience_session_snapshot",
    "release_experience_session_feature",
]
