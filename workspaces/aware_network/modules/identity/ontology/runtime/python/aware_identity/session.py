from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_code.types import JsonObject
from aware_identity.meta_runtime import IdentityMetaRuntimeLaneBinder
from aware_identity_ontology.session.session import Session
from aware_identity_ontology.session.session_config import SessionConfig
from aware_identity_ontology.session.session_member import SessionMember
from aware_identity_ontology.session.session_provider import SessionProvider
from aware_identity_ontology.stable_ids import (
    stable_session_config_actor_config_id,
    stable_session_config_id,
    stable_session_id,
    stable_session_member_actor_role_id,
    stable_session_member_id,
    stable_session_provider_id,
    stable_session_provider_session_config_id,
    stable_session_provider_session_id,
)


@dataclass(frozen=True, slots=True)
class IdentitySessionOperationContext:
    actor_id: UUID


@dataclass(frozen=True, slots=True)
class IdentitySessionRuntimeContext:
    lane_binder: IdentityMetaRuntimeLaneBinder


def resolve_identity_session_runtime_context(
    *,
    lane_binder: IdentityMetaRuntimeLaneBinder,
) -> IdentitySessionRuntimeContext:
    return IdentitySessionRuntimeContext(lane_binder=lane_binder)


async def ensure_session_config(
    *,
    runtime_context: IdentitySessionRuntimeContext,
    operation_context: IdentitySessionOperationContext,
    key: str,
    title: str | None,
    description: str | None,
    purpose: str | None,
    status: str,
    metadata_json: JsonObject,
) -> UUID:
    session_config_id = stable_session_config_id(key=key)
    lane = runtime_context.lane_binder.bind(
        projection="SessionConfig",
        branch_id=session_config_id,
        actor_id=operation_context.actor_id,
    )
    with lane.activate():
        session_config = await SessionConfig.create(
            key=key,
            title=title,
            description=description,
            purpose=purpose,
            status=status,
            metadata_json=metadata_json,
        )
    if session_config.id != session_config_id:
        raise ValueError(
            "session_config.create returned an unexpected id: "
            + f"expected={session_config_id} actual={session_config.id}"
        )
    return session_config_id


async def bind_session_config_actor_config(
    *,
    runtime_context: IdentitySessionRuntimeContext,
    operation_context: IdentitySessionOperationContext,
    session_config_id: UUID,
    actor_config_id: UUID,
    status: str,
    purpose: str | None,
    metadata_json: JsonObject,
) -> UUID:
    binding_id = stable_session_config_actor_config_id(
        session_config_id=session_config_id,
        actor_config_id=actor_config_id,
    )
    lane = runtime_context.lane_binder.bind(
        projection="SessionConfig",
        branch_id=session_config_id,
        actor_id=operation_context.actor_id,
    )
    session_config = _session_config_ref(session_config_id)
    with lane.activate():
        binding = await session_config.add_actor_config(
            actor_config_id=actor_config_id,
            status=status,
            purpose=purpose,
            metadata_json=metadata_json,
        )
    if binding.id != binding_id:
        raise ValueError(
            "session_config.add_actor_config returned an unexpected id: "
            + f"expected={binding_id} actual={binding.id}"
        )
    return binding_id


async def register_session_provider(
    *,
    runtime_context: IdentitySessionRuntimeContext,
    operation_context: IdentitySessionOperationContext,
    provider_key: str,
    provider_kind: str,
    title: str | None,
    status: str,
    contract_ref: str | None,
    metadata_json: JsonObject,
) -> UUID:
    session_provider_id = stable_session_provider_id(provider_key=provider_key)
    lane = runtime_context.lane_binder.bind(
        projection="SessionProvider",
        branch_id=session_provider_id,
        actor_id=operation_context.actor_id,
    )
    with lane.activate():
        provider = await SessionProvider.register(
            provider_key=provider_key,
            provider_kind=provider_kind,
            title=title,
            status=status,
            contract_ref=contract_ref,
            metadata_json=metadata_json,
        )
    if provider.id != session_provider_id:
        raise ValueError(
            "session_provider.register returned an unexpected id: "
            + f"expected={session_provider_id} actual={provider.id}"
        )
    return session_provider_id


async def bind_session_provider_config(
    *,
    runtime_context: IdentitySessionRuntimeContext,
    operation_context: IdentitySessionOperationContext,
    session_provider_id: UUID,
    config_key: str,
    session_config_id: UUID,
    title: str | None,
    status: str,
    provider_contract_ref: str | None,
    selection_policy: str,
    metadata_json: JsonObject,
) -> UUID:
    binding_id = stable_session_provider_session_config_id(
        session_provider_id=session_provider_id,
        config_key=config_key,
        session_config_id=session_config_id,
    )
    lane = runtime_context.lane_binder.bind(
        projection="SessionProvider",
        branch_id=session_provider_id,
        actor_id=operation_context.actor_id,
    )
    provider = _session_provider_ref(session_provider_id)
    with lane.activate():
        binding = await provider.bind_session_config(
            config_key=config_key,
            session_config_id=session_config_id,
            title=title,
            status=status,
            provider_contract_ref=provider_contract_ref,
            selection_policy=selection_policy,
            metadata_json=metadata_json,
        )
    if binding.id != binding_id:
        raise ValueError(
            "session_provider.bind_session_config returned an unexpected id: "
            + f"expected={binding_id} actual={binding.id}"
        )
    return binding_id


async def start_session(
    *,
    runtime_context: IdentitySessionRuntimeContext,
    operation_context: IdentitySessionOperationContext,
    session_config_id: UUID,
    key: str,
    title: str | None,
    description: str | None,
    purpose: str | None,
    status: str,
    created_by_actor_id: UUID | None,
    source_kind: str | None,
    source_ref: str | None,
    metadata_json: JsonObject,
    parent_session_id: UUID | None = None,
    parent_session_scope_key: str = "root",
) -> UUID:
    resolved_parent_scope_key = _session_parent_scope_key(
        parent_session_id=parent_session_id,
        parent_session_scope_key=parent_session_scope_key,
    )
    session_id = stable_session_id(
        session_config_id=session_config_id,
        parent_session_scope_key=resolved_parent_scope_key,
        key=key,
    )
    lane = runtime_context.lane_binder.bind(
        projection="SessionConfig",
        branch_id=session_config_id,
        actor_id=operation_context.actor_id,
    )
    session_config = _session_config_ref(session_config_id)
    with lane.activate():
        session = await session_config.start_session(
            parent_session_scope_key=resolved_parent_scope_key,
            key=key,
            parent_session_id=parent_session_id,
            title=title,
            description=description,
            purpose=purpose,
            status=status,
            created_by_actor_id=created_by_actor_id,
            source_kind=source_kind,
            source_ref=source_ref,
            metadata_json=metadata_json,
        )
    if session.id != session_id:
        raise ValueError(
            "session_config.start_session returned an unexpected session id: "
            + f"expected={session_id} actual={session.id}"
        )
    return session_id


def _session_parent_scope_key(
    *,
    parent_session_id: UUID | None,
    parent_session_scope_key: str | None,
) -> str:
    normalized = (parent_session_scope_key or "root").strip()
    if parent_session_id is None:
        if normalized != "root":
            raise ValueError(
                "Root Identity sessions must use parent_session_scope_key='root'."
            )
        return "root"
    expected = str(parent_session_id)
    if normalized != expected:
        raise ValueError(
            "Child Identity sessions must use parent_session_scope_key equal to "
            "parent_session_id."
        )
    return expected


async def join_session(
    *,
    runtime_context: IdentitySessionRuntimeContext,
    operation_context: IdentitySessionOperationContext,
    session_id: UUID,
    actor_id: UUID,
    session_actor_config_id: UUID,
    status: str,
    joined_at_unix_ms: int | None,
    left_at_unix_ms: int | None,
    metadata_json: JsonObject,
) -> UUID:
    session_member_id = stable_session_member_id(
        session_id=session_id,
        actor_id=actor_id,
    )
    lane = runtime_context.lane_binder.bind(
        projection="Session",
        branch_id=session_id,
        actor_id=operation_context.actor_id,
    )
    session = _session_ref(session_id)
    with lane.activate():
        member = await session.join_actor(
            actor_id=actor_id,
            session_actor_config_id=session_actor_config_id,
            status=status,
            joined_at_unix_ms=joined_at_unix_ms,
            left_at_unix_ms=left_at_unix_ms,
            metadata_json=metadata_json,
        )
    if member.id != session_member_id:
        raise ValueError(
            "session.join_actor returned an unexpected member id: "
            + f"expected={session_member_id} actual={member.id}"
        )
    return session_member_id


async def record_session_member_actor_role(
    *,
    runtime_context: IdentitySessionRuntimeContext,
    operation_context: IdentitySessionOperationContext,
    session_id: UUID,
    session_member_id: UUID,
    actor_role_id: UUID,
    source_kind: str,
    status: str,
    evidence_json: JsonObject,
) -> UUID:
    edge_id = stable_session_member_actor_role_id(
        session_member_id=session_member_id,
        actor_role_id=actor_role_id,
    )
    lane = runtime_context.lane_binder.bind(
        projection="Session",
        branch_id=session_id,
        actor_id=operation_context.actor_id,
    )
    session_member = _session_member_ref(
        session_member_id=session_member_id,
        session_id=session_id,
    )
    with lane.activate():
        edge = await session_member.add_actor_role(
            actor_role_id=actor_role_id,
            source_kind=source_kind,
            status=status,
            evidence_json=evidence_json,
        )
    if edge.id != edge_id:
        raise ValueError(
            "session_member.add_actor_role returned an unexpected edge id: "
            + f"expected={edge_id} actual={edge.id}"
        )
    return edge_id


async def attach_session_provider_session(
    *,
    runtime_context: IdentitySessionRuntimeContext,
    operation_context: IdentitySessionOperationContext,
    session_id: UUID,
    provider_session_config_id: UUID,
    provider_session_key: str,
    provider_session_ref: str | None,
    provider_object_instance_graph_identity_id: UUID | None,
    provider_class_instance_identity_id: UUID | None,
    provider_object_instance_graph_branch_id: UUID | None,
    status: str,
    metadata_json: JsonObject,
) -> UUID:
    attached_id = stable_session_provider_session_id(
        session_id=session_id,
        provider_session_config_id=provider_session_config_id,
        provider_session_key=provider_session_key,
    )
    lane = runtime_context.lane_binder.bind(
        projection="Session",
        branch_id=session_id,
        actor_id=operation_context.actor_id,
    )
    session = _session_ref(session_id)
    with lane.activate():
        attached = await session.attach_provider_session(
            provider_session_config_id=provider_session_config_id,
            provider_session_key=provider_session_key,
            provider_session_ref=provider_session_ref,
            provider_object_instance_graph_identity_id=(
                provider_object_instance_graph_identity_id
            ),
            provider_class_instance_identity_id=provider_class_instance_identity_id,
            provider_object_instance_graph_branch_id=(
                provider_object_instance_graph_branch_id
            ),
            status=status,
            metadata_json=metadata_json,
        )
    if attached.id != attached_id:
        raise ValueError(
            "session.attach_provider_session returned an unexpected attachment id: "
            + f"expected={attached_id} actual={attached.id}"
        )
    return attached_id


def _session_config_ref(session_config_id: UUID) -> SessionConfig:
    return SessionConfig.model_construct(id=session_config_id)


def _session_provider_ref(session_provider_id: UUID) -> SessionProvider:
    return SessionProvider.model_construct(id=session_provider_id)


def _session_ref(session_id: UUID) -> Session:
    return Session.model_construct(id=session_id)


def _session_member_ref(
    *,
    session_member_id: UUID,
    session_id: UUID,
) -> SessionMember:
    return SessionMember.model_construct(
        id=session_member_id,
        session_id=session_id,
    )
