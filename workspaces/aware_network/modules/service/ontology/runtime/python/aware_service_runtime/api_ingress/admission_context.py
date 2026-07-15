from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, cast, runtime_checkable
from uuid import UUID

from aware_code.types import JsonObject

_ACTOR_CONTEXT_KEYS = (
    "service_actor_context",
    "actor_context",
    "session_actor_context",
    "workspace_session_actor_context",
    "experience_session_actor_context",
)
_SESSION_SCOPE_KEYS = (
    "service_session_scope",
    "session_scope",
    "workspace_session_scope",
    "experience_session_scope",
)
_PARTICIPANT_ADMISSION_KEYS = (
    "service_participant_admission",
    "participant_admission",
    "session_participant_admission",
    "workspace_session_participant_admission",
    "experience_session_actor_admission",
    "actor_admission",
)
_CONTRACT_ACCESS_KEYS = (
    "service_contract_access_context",
    "contract_access_context",
    "service_contract_access_context_ref",
)
_OPERATION_AUTHORIZATION_KEYS = (
    "service_operation_authorization",
    "service_operation_authorization_ref",
    "operation_authorization",
)

_ADMITTED_ACTOR_KINDS = frozenset(
    {
        "agent_operator",
        "human_identity",
        "service_actor",
        "experience_service",
        "system_service",
        "legacy_actor",
    }
)


@runtime_checkable
class _ModelDumpProtocol(Protocol):
    def model_dump(self, *, mode: str) -> object: ...


@dataclass(frozen=True, slots=True)
class ServiceActorContext:
    """Provider-neutral actor context consumed by Service admission."""

    status: str = "ready"
    kind: str | None = None
    source: str | None = None
    actor_id: UUID | None = None
    actor_ref: str | None = None
    identity_id: UUID | None = None
    identity_ref: str | None = None
    identity_profile_id: str | None = None
    public_handle: str | None = None
    identity_type: str | None = None
    execution_id: str | None = None
    provider_key: str | None = None
    provider_session_id: str | None = None
    agent_id: str | None = None
    agent_process_id: str | None = None
    agent_process_thread_id: str | None = None
    agent_session_id: str | None = None
    state_path: str | None = None
    evidence: JsonObject | None = None


@dataclass(frozen=True, slots=True)
class ServiceSessionScope:
    """Common session scope shape for Workspace, Experience, and future services."""

    scope_kind: str = "service_session"
    scope_ref: str | None = None
    service_name: str | None = None
    session_id: str | None = None
    session_key: str | None = None
    workspace_root: str | None = None
    branch_key: str | None = None
    workspace_session_id: str | None = None
    experience_name: str | None = None
    profile_key: str | None = None
    environment_id: UUID | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    actor_id: UUID | None = None
    actor_ref: str | None = None
    evidence: JsonObject | None = None


@dataclass(frozen=True, slots=True)
class ServiceParticipantAdmission:
    """Service-owned participant admission evidence above one actor/session pair."""

    schema: str = "aware.service.participant_admission.v0"
    status: str = "blocked"
    admitted: bool = False
    reason: str | None = None
    actor_context: ServiceActorContext | None = None
    session_scope: ServiceSessionScope | None = None
    actor_id: UUID | None = None
    actor_ref: str | None = None
    actor_kind: str | None = None
    identity_id: UUID | None = None
    identity_ref: str | None = None
    execution_id: str | None = None
    provider_key: str | None = None
    provider_session_id: str | None = None
    agent_process_thread_id: str | None = None
    blockers: tuple[str, ...] = ()
    next_suggested_action: str | None = None
    evidence: JsonObject | None = None


@dataclass(frozen=True, slots=True)
class ServiceContractAccessContextRef:
    """Lightweight contract/subscription refs carried by callers before resolution."""

    consumer_finance_entity_id: UUID | None = None
    service_subscription_id: UUID | None = None
    service_contract_id: UUID | None = None
    service_contract_config_id: UUID | None = None
    smart_contract_id: UUID | None = None
    evidence: JsonObject | None = None


@dataclass(frozen=True, slots=True)
class ServiceOperationAuthorizationRef:
    """Exact contract/permit binding for one Service operation invocation."""

    contract_version: str = "aware.service.operation_authorization.v1"
    service_contract_id: UUID | None = None
    permit_id: UUID | None = None
    operation_key: str | None = None
    request_hash: str | None = None


@dataclass(frozen=True, slots=True)
class ServiceOperationAdmissionContext:
    """Normalized Service admission context for one operation invocation."""

    schema: str = "aware.service.operation_admission_context.v0"
    actor_context: ServiceActorContext | None = None
    session_scope: ServiceSessionScope | None = None
    participant_admission: ServiceParticipantAdmission | None = None
    contract_access_context_ref: ServiceContractAccessContextRef | None = None
    operation_authorization_ref: ServiceOperationAuthorizationRef | None = None
    source: str = "service_host.invocation_context"

    @property
    def effective_actor_id(self) -> UUID | None:
        if self.actor_context is not None and self.actor_context.actor_id is not None:
            return self.actor_context.actor_id
        if (
            self.participant_admission is not None
            and self.participant_admission.actor_id is not None
        ):
            return self.participant_admission.actor_id
        return None


def normalize_service_operation_admission_context(
    *,
    invocation_context: Mapping[str, object] | None,
    legacy_actor_id: UUID | None = None,
) -> ServiceOperationAdmissionContext:
    """Normalize caller-owned actor/session evidence without importing caller domains."""

    root = _object_mapping(invocation_context)
    source = (
        "service_host.invocation_context" if root else "service_host.legacy_actor_id"
    )
    container = _first_mapping(
        root,
        ("service_operation_admission_context", "service_admission_context"),
    )
    source_mapping = container or root
    actor_context = _normalize_actor_context(
        _first_mapping(source_mapping, _ACTOR_CONTEXT_KEYS),
        legacy_actor_id=legacy_actor_id,
    )
    session_scope = _normalize_session_scope(
        _first_mapping(source_mapping, _SESSION_SCOPE_KEYS),
    )
    participant_payload = _first_mapping(source_mapping, _PARTICIPANT_ADMISSION_KEYS)
    participant_admission = (
        _normalize_participant_admission(
            participant_payload,
            actor_context=actor_context,
            session_scope=session_scope,
        )
        if participant_payload
        else build_service_participant_admission(
            actor_context=actor_context,
            session_scope=session_scope,
        )
    )
    contract_access_context_ref = _normalize_contract_access_context_ref(
        _first_mapping(source_mapping, _CONTRACT_ACCESS_KEYS),
    )
    operation_authorization_ref = _normalize_operation_authorization_ref(
        _first_mapping(source_mapping, _OPERATION_AUTHORIZATION_KEYS),
    )
    return ServiceOperationAdmissionContext(
        actor_context=actor_context,
        session_scope=session_scope,
        participant_admission=participant_admission,
        contract_access_context_ref=contract_access_context_ref,
        operation_authorization_ref=operation_authorization_ref,
        source=source,
    )


def build_service_participant_admission(
    *,
    actor_context: ServiceActorContext | None,
    session_scope: ServiceSessionScope | None,
) -> ServiceParticipantAdmission:
    base_evidence = cast(
        JsonObject,
        {"source": "aware_service_runtime.admission_context"},
    )
    if actor_context is None:
        return _blocked_participant_admission(
            actor_context=None,
            session_scope=session_scope,
            reason="missing_actor_context",
            blockers=("actor_context_missing",),
            next_suggested_action="resolve_identity",
            evidence=base_evidence,
        )
    if actor_context.status != "ready":
        return _blocked_participant_admission(
            actor_context=actor_context,
            session_scope=session_scope,
            reason="actor_context_not_ready",
            blockers=("actor_context_not_ready",),
            next_suggested_action="resolve_identity",
            evidence=base_evidence,
        )
    if actor_context.kind not in _ADMITTED_ACTOR_KINDS:
        return _blocked_participant_admission(
            actor_context=actor_context,
            session_scope=session_scope,
            reason="invalid_actor_context_kind",
            blockers=("actor_context_kind_invalid",),
            next_suggested_action="resolve_identity",
            evidence=base_evidence,
        )
    if actor_context.actor_id is None:
        return _blocked_participant_admission(
            actor_context=actor_context,
            session_scope=session_scope,
            reason="missing_actor_id",
            blockers=("actor_id_missing",),
            next_suggested_action="resolve_identity",
            evidence=base_evidence,
        )
    if (
        session_scope is not None
        and session_scope.actor_id is not None
        and session_scope.actor_id != actor_context.actor_id
    ):
        return _blocked_participant_admission(
            actor_context=actor_context,
            session_scope=session_scope,
            reason="actor_scope_mismatch",
            blockers=("session_actor_scope_mismatch",),
            next_suggested_action="bind_session_actor",
            evidence=base_evidence,
        )
    return ServiceParticipantAdmission(
        status="admitted",
        admitted=True,
        actor_context=actor_context,
        session_scope=session_scope,
        actor_id=actor_context.actor_id,
        actor_ref=actor_context.actor_ref,
        actor_kind=actor_context.kind,
        identity_id=actor_context.identity_id,
        identity_ref=actor_context.identity_ref,
        execution_id=actor_context.execution_id,
        provider_key=actor_context.provider_key,
        provider_session_id=actor_context.provider_session_id,
        agent_process_thread_id=actor_context.agent_process_thread_id,
        evidence=cast(
            JsonObject,
            {
                **base_evidence,
                "actor_context_source": actor_context.source,
                "actor_context_status": actor_context.status,
            },
        ),
    )


def service_operation_admission_context_payload(
    admission_context: ServiceOperationAdmissionContext | None,
) -> JsonObject | None:
    if admission_context is None:
        return None
    return cast(
        JsonObject,
        {
            "schema": admission_context.schema,
            "source": admission_context.source,
            "actor_context": service_actor_context_payload(
                admission_context.actor_context
            ),
            "session_scope": service_session_scope_payload(
                admission_context.session_scope
            ),
            "participant_admission": service_participant_admission_payload(
                admission_context.participant_admission
            ),
            "contract_access_context_ref": service_contract_access_context_ref_payload(
                admission_context.contract_access_context_ref
            ),
            "operation_authorization_ref": service_operation_authorization_ref_payload(
                admission_context.operation_authorization_ref
            ),
        },
    )


def service_actor_context_payload(
    actor_context: ServiceActorContext | None,
) -> JsonObject | None:
    if actor_context is None:
        return None
    return _drop_none(
        {
            "status": actor_context.status,
            "kind": actor_context.kind,
            "source": actor_context.source,
            "actor_id": _uuid_text(actor_context.actor_id),
            "actor_ref": actor_context.actor_ref,
            "identity_id": _uuid_text(actor_context.identity_id),
            "identity_ref": actor_context.identity_ref,
            "identity_profile_id": actor_context.identity_profile_id,
            "public_handle": actor_context.public_handle,
            "identity_type": actor_context.identity_type,
            "execution_id": actor_context.execution_id,
            "provider_key": actor_context.provider_key,
            "provider_session_id": actor_context.provider_session_id,
            "agent_id": actor_context.agent_id,
            "agent_process_id": actor_context.agent_process_id,
            "agent_process_thread_id": actor_context.agent_process_thread_id,
            "agent_session_id": actor_context.agent_session_id,
            "state_path": actor_context.state_path,
            "evidence": actor_context.evidence,
        }
    )


def service_session_scope_payload(
    session_scope: ServiceSessionScope | None,
) -> JsonObject | None:
    if session_scope is None:
        return None
    return _drop_none(
        {
            "scope_kind": session_scope.scope_kind,
            "scope_ref": session_scope.scope_ref,
            "service_name": session_scope.service_name,
            "session_id": session_scope.session_id,
            "session_key": session_scope.session_key,
            "workspace_root": session_scope.workspace_root,
            "branch_key": session_scope.branch_key,
            "workspace_session_id": session_scope.workspace_session_id,
            "experience_name": session_scope.experience_name,
            "profile_key": session_scope.profile_key,
            "environment_id": _uuid_text(session_scope.environment_id),
            "process_id": _uuid_text(session_scope.process_id),
            "thread_id": _uuid_text(session_scope.thread_id),
            "branch_id": _uuid_text(session_scope.branch_id),
            "projection_hash": session_scope.projection_hash,
            "actor_id": _uuid_text(session_scope.actor_id),
            "actor_ref": session_scope.actor_ref,
            "evidence": session_scope.evidence,
        }
    )


def service_participant_admission_payload(
    participant_admission: ServiceParticipantAdmission | None,
) -> JsonObject | None:
    if participant_admission is None:
        return None
    return _drop_none(
        {
            "schema": participant_admission.schema,
            "status": participant_admission.status,
            "admitted": participant_admission.admitted,
            "reason": participant_admission.reason,
            "actor_id": _uuid_text(participant_admission.actor_id),
            "actor_ref": participant_admission.actor_ref,
            "actor_kind": participant_admission.actor_kind,
            "identity_id": _uuid_text(participant_admission.identity_id),
            "identity_ref": participant_admission.identity_ref,
            "execution_id": participant_admission.execution_id,
            "provider_key": participant_admission.provider_key,
            "provider_session_id": participant_admission.provider_session_id,
            "agent_process_thread_id": (participant_admission.agent_process_thread_id),
            "blockers": list(participant_admission.blockers),
            "next_suggested_action": (participant_admission.next_suggested_action),
            "actor_context": service_actor_context_payload(
                participant_admission.actor_context
            ),
            "session_scope": service_session_scope_payload(
                participant_admission.session_scope
            ),
            "evidence": participant_admission.evidence,
        }
    )


def service_contract_access_context_ref_payload(
    contract_access_context_ref: ServiceContractAccessContextRef | None,
) -> JsonObject | None:
    if contract_access_context_ref is None:
        return None
    return _drop_none(
        {
            "consumer_finance_entity_id": _uuid_text(
                contract_access_context_ref.consumer_finance_entity_id
            ),
            "service_subscription_id": _uuid_text(
                contract_access_context_ref.service_subscription_id
            ),
            "service_contract_id": _uuid_text(
                contract_access_context_ref.service_contract_id
            ),
            "service_contract_config_id": _uuid_text(
                contract_access_context_ref.service_contract_config_id
            ),
            "smart_contract_id": _uuid_text(
                contract_access_context_ref.smart_contract_id
            ),
            "evidence": contract_access_context_ref.evidence,
        }
    )


def service_operation_authorization_ref_payload(
    authorization_ref: ServiceOperationAuthorizationRef | None,
) -> JsonObject | None:
    if authorization_ref is None:
        return None
    return _drop_none(
        {
            "contract_version": authorization_ref.contract_version,
            "service_contract_id": _uuid_text(authorization_ref.service_contract_id),
            "permit_id": _uuid_text(authorization_ref.permit_id),
            "operation_key": authorization_ref.operation_key,
            "request_hash": authorization_ref.request_hash,
        }
    )


def service_participant_admission_blocking_reasons(
    participant_admission: ServiceParticipantAdmission | None,
) -> tuple[str, ...]:
    if participant_admission is None or participant_admission.admitted:
        return ()
    if participant_admission.blockers:
        return participant_admission.blockers
    if participant_admission.reason is not None:
        return (participant_admission.reason,)
    return ("participant_admission_denied",)


def _normalize_actor_context(
    payload: Mapping[str, object] | None,
    *,
    legacy_actor_id: UUID | None,
) -> ServiceActorContext | None:
    if payload is None:
        if legacy_actor_id is None:
            return None
        return ServiceActorContext(
            status="ready",
            kind="legacy_actor",
            source="service_host_api_ingress.actor_id",
            actor_id=legacy_actor_id,
            actor_ref=str(legacy_actor_id),
            evidence=cast(JsonObject, {"compatibility": "legacy_actor_id"}),
        )
    actor_ref = _optional_text(payload.get("actor_ref")) or _optional_text(
        payload.get("actor_id")
    )
    identity_ref = _optional_text(payload.get("identity_ref")) or _optional_text(
        payload.get("identity_id")
    )
    return ServiceActorContext(
        status=_optional_text(payload.get("status")) or "blocked",
        kind=_optional_text(payload.get("kind")),
        source=_optional_text(payload.get("source")),
        actor_id=_optional_uuid(payload.get("actor_id")),
        actor_ref=actor_ref,
        identity_id=_optional_uuid(payload.get("identity_id")),
        identity_ref=identity_ref,
        identity_profile_id=_optional_text(payload.get("identity_profile_id")),
        public_handle=_optional_text(payload.get("public_handle")),
        identity_type=_optional_text(payload.get("identity_type")),
        execution_id=_optional_text(payload.get("execution_id")),
        provider_key=_optional_text(payload.get("provider_key")),
        provider_session_id=_optional_text(payload.get("provider_session_id")),
        agent_id=_optional_text(payload.get("agent_id")),
        agent_process_id=_optional_text(payload.get("agent_process_id")),
        agent_process_thread_id=_optional_text(payload.get("agent_process_thread_id")),
        agent_session_id=_optional_text(payload.get("agent_session_id")),
        state_path=_optional_text(payload.get("state_path")),
        evidence=_json_object(payload.get("evidence")),
    )


def _normalize_session_scope(
    payload: Mapping[str, object] | None,
) -> ServiceSessionScope | None:
    if payload is None:
        return None
    actor_ref = _optional_text(payload.get("actor_ref")) or _optional_text(
        payload.get("actor_id")
    )
    return ServiceSessionScope(
        scope_kind=_optional_text(payload.get("scope_kind")) or "service_session",
        scope_ref=_optional_text(payload.get("scope_ref")),
        service_name=_optional_text(payload.get("service_name")),
        session_id=_optional_text(payload.get("session_id")),
        session_key=_optional_text(payload.get("session_key")),
        workspace_root=_optional_text(payload.get("workspace_root")),
        branch_key=_optional_text(payload.get("branch_key")),
        workspace_session_id=_optional_text(payload.get("workspace_session_id")),
        experience_name=_optional_text(payload.get("experience_name")),
        profile_key=_optional_text(payload.get("profile_key")),
        environment_id=_optional_uuid(payload.get("environment_id")),
        process_id=_optional_uuid(payload.get("process_id")),
        thread_id=_optional_uuid(payload.get("thread_id")),
        branch_id=_optional_uuid(payload.get("branch_id")),
        projection_hash=_optional_text(payload.get("projection_hash")),
        actor_id=_optional_uuid(payload.get("actor_id")),
        actor_ref=actor_ref,
        evidence=_json_object(payload.get("evidence")),
    )


def _normalize_participant_admission(
    payload: Mapping[str, object],
    *,
    actor_context: ServiceActorContext | None,
    session_scope: ServiceSessionScope | None,
) -> ServiceParticipantAdmission:
    blockers = tuple(str(item) for item in _sequence(payload.get("blockers")))
    admitted = bool(payload.get("admitted", False))
    status = _optional_text(payload.get("status")) or (
        "admitted" if admitted else "blocked"
    )
    reason = _optional_text(payload.get("reason"))
    actor_id = _optional_uuid(payload.get("actor_id")) or (
        actor_context.actor_id if actor_context is not None else None
    )
    actor_ref = (
        _optional_text(payload.get("actor_ref"))
        or _optional_text(payload.get("actor_id"))
        or (actor_context.actor_ref if actor_context is not None else None)
    )
    actor_kind = _optional_text(payload.get("actor_kind")) or (
        actor_context.kind if actor_context is not None else None
    )
    identity_id = _optional_uuid(payload.get("identity_id")) or (
        actor_context.identity_id if actor_context is not None else None
    )
    return ServiceParticipantAdmission(
        status=status,
        admitted=admitted,
        reason=reason,
        actor_context=actor_context,
        session_scope=session_scope,
        actor_id=actor_id,
        actor_ref=actor_ref,
        actor_kind=actor_kind,
        identity_id=identity_id,
        identity_ref=_optional_text(payload.get("identity_ref"))
        or _optional_text(payload.get("identity_id")),
        execution_id=_optional_text(payload.get("execution_id"))
        or (actor_context.execution_id if actor_context is not None else None),
        provider_key=_optional_text(payload.get("provider_key"))
        or (actor_context.provider_key if actor_context is not None else None),
        provider_session_id=_optional_text(payload.get("provider_session_id"))
        or (actor_context.provider_session_id if actor_context is not None else None),
        agent_process_thread_id=_optional_text(payload.get("agent_process_thread_id"))
        or (
            actor_context.agent_process_thread_id if actor_context is not None else None
        ),
        blockers=blockers,
        next_suggested_action=_optional_text(payload.get("next_suggested_action")),
        evidence=_json_object(payload.get("evidence")),
    )


def _normalize_contract_access_context_ref(
    payload: Mapping[str, object] | None,
) -> ServiceContractAccessContextRef | None:
    if payload is None:
        return None
    return ServiceContractAccessContextRef(
        consumer_finance_entity_id=_optional_uuid(
            payload.get("consumer_finance_entity_id")
        ),
        service_subscription_id=_optional_uuid(payload.get("service_subscription_id")),
        service_contract_id=_optional_uuid(payload.get("service_contract_id")),
        service_contract_config_id=_optional_uuid(
            payload.get("service_contract_config_id")
        ),
        smart_contract_id=_optional_uuid(payload.get("smart_contract_id")),
        evidence=_json_object(payload.get("evidence")),
    )


def _normalize_operation_authorization_ref(
    payload: Mapping[str, object] | None,
) -> ServiceOperationAuthorizationRef | None:
    if payload is None:
        return None
    contract_version = _optional_text(payload.get("contract_version")) or ""
    if contract_version != "aware.service.operation_authorization.v1":
        raise ValueError(
            "Unsupported Service operation authorization contract_version: "
            f"{contract_version!r}"
        )
    return ServiceOperationAuthorizationRef(
        contract_version=contract_version,
        service_contract_id=_optional_uuid(payload.get("service_contract_id")),
        permit_id=_optional_uuid(payload.get("permit_id")),
        operation_key=_optional_text(payload.get("operation_key")),
        request_hash=_optional_text(payload.get("request_hash")),
    )


def _blocked_participant_admission(
    *,
    actor_context: ServiceActorContext | None,
    session_scope: ServiceSessionScope | None,
    reason: str,
    blockers: tuple[str, ...],
    next_suggested_action: str,
    evidence: JsonObject,
) -> ServiceParticipantAdmission:
    return ServiceParticipantAdmission(
        status="blocked",
        admitted=False,
        reason=reason,
        actor_context=actor_context,
        session_scope=session_scope,
        actor_id=actor_context.actor_id if actor_context is not None else None,
        actor_ref=actor_context.actor_ref if actor_context is not None else None,
        actor_kind=actor_context.kind if actor_context is not None else None,
        identity_id=actor_context.identity_id if actor_context is not None else None,
        identity_ref=actor_context.identity_ref if actor_context is not None else None,
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
        evidence=evidence,
    )


def _first_mapping(
    source: Mapping[str, object],
    keys: Sequence[str],
) -> Mapping[str, object] | None:
    for key in keys:
        nested = _object_mapping(source.get(key))
        if nested:
            return nested
    return None


def _object_mapping(value: object) -> Mapping[str, object]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        return {str(key): item for key, item in mapping.items()}
    if isinstance(value, _ModelDumpProtocol):
        dumped = value.model_dump(mode="json")
        if isinstance(dumped, Mapping):
            dumped_mapping = cast(Mapping[object, object], dumped)
            return {str(key): item for key, item in dumped_mapping.items()}
    return {}


def _json_object(value: object) -> JsonObject | None:
    mapping = _object_mapping(value)
    return cast(JsonObject, dict(mapping)) if mapping else None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_uuid(value: object) -> UUID | None:
    if value is None or value == "":
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _uuid_text(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _sequence(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _drop_none(payload: Mapping[str, object | None]) -> JsonObject:
    return cast(
        JsonObject,
        {key: value for key, value in payload.items() if value is not None},
    )


__all__ = [
    "ServiceActorContext",
    "ServiceContractAccessContextRef",
    "ServiceOperationAdmissionContext",
    "ServiceOperationAuthorizationRef",
    "ServiceParticipantAdmission",
    "ServiceSessionScope",
    "build_service_participant_admission",
    "normalize_service_operation_admission_context",
    "service_actor_context_payload",
    "service_contract_access_context_ref_payload",
    "service_operation_admission_context_payload",
    "service_operation_authorization_ref_payload",
    "service_participant_admission_blocking_reasons",
    "service_participant_admission_payload",
    "service_session_scope_payload",
]
