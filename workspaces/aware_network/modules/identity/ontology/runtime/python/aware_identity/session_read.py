from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

from aware_code.types import JsonObject
from aware_identity_ontology_orm_models.session.session import Session as SessionOrmModel
from aware_identity_ontology_orm_models.session.session_member import (
    SessionMember as SessionMemberOrmModel,
)
from aware_identity_ontology_orm_models.session.session_member_actor_role import (
    SessionMemberActorRole as SessionMemberActorRoleOrmModel,
)
from aware_identity_ontology_orm_models.session.session_provider_session import (
    SessionProviderSession as SessionProviderSessionOrmModel,
)
from aware_identity_service_dto.session.session import (
    ActorSessionsListRequest,
    ActorSessionsListResult,
    ChildSessionsListRequest,
    ChildSessionsListResult,
    SessionDescribeRequest,
    SessionDescribeResult,
    SessionMemberActorRoleSummary,
    SessionMembersListRequest,
    SessionMembersListResult,
    SessionMemberSummary,
    SessionProviderSessionSummary,
    SessionSummary,
)


@dataclass(frozen=True, slots=True)
class IdentitySessionReplicaReadModels:
    session_model: Any
    session_member_model: Any
    session_member_actor_role_model: Any
    session_provider_session_model: Any


DEFAULT_IDENTITY_SESSION_REPLICA_READ_MODELS = IdentitySessionReplicaReadModels(
    session_model=SessionOrmModel,
    session_member_model=SessionMemberOrmModel,
    session_member_actor_role_model=SessionMemberActorRoleOrmModel,
    session_provider_session_model=SessionProviderSessionOrmModel,
)


async def list_actor_sessions_from_identity_replica(
    *,
    request: ActorSessionsListRequest,
    models: IdentitySessionReplicaReadModels | None = None,
) -> ActorSessionsListResult:
    read_models = _resolve_models(models)
    member_query = read_models.session_member_model.where(actor_id=request.actor_id)
    member_query = _apply_status_filter(
        query=member_query,
        field_name="status",
        status=request.status,
        include_inactive=request.include_inactive,
    )
    members = list(await member_query.all())
    sessions: list[SessionSummary] = []
    seen_session_ids: set[UUID] = set()
    for member in members:
        session_id = _uuid_attr(member, "session_id")
        if session_id in seen_session_ids:
            continue
        session_obj = await read_models.session_model.by_id(session_id)
        if session_obj is None:
            continue
        if (
            request.parent_session_id is not None
            and _optional_uuid_attr(session_obj, "parent_session_id")
            != request.parent_session_id
        ):
            continue
        seen_session_ids.add(session_id)
        sessions.append(
            await _session_summary_from_orm(
                session_obj=session_obj,
                read_models=read_models,
            )
        )
    sessions.sort(key=lambda item: (item.key, str(item.session_id)))
    return ActorSessionsListResult(
        request_id=request.request_id,
        actor_id=request.actor_id,
        sessions=sessions,
        info="identity actor sessions listed",
    )


async def describe_session_from_identity_replica(
    *,
    request: SessionDescribeRequest,
    models: IdentitySessionReplicaReadModels | None = None,
) -> SessionDescribeResult:
    read_models = _resolve_models(models)
    session_obj = await read_models.session_model.by_id(request.session_id)
    session = (
        await _session_summary_from_orm(
            session_obj=session_obj,
            read_models=read_models,
        )
        if session_obj is not None
        else None
    )
    return SessionDescribeResult(
        request_id=request.request_id,
        session=session,
        info=(
            "identity session described"
            if session is not None
            else "identity session not found"
        ),
    )


async def list_child_sessions_from_identity_replica(
    *,
    request: ChildSessionsListRequest,
    models: IdentitySessionReplicaReadModels | None = None,
) -> ChildSessionsListResult:
    read_models = _resolve_models(models)
    session_query = read_models.session_model.where(
        parent_session_id=request.parent_session_id
    ).match_if_present(session_config_id=request.session_config_id)
    session_query = _apply_status_filter(
        query=session_query,
        field_name="status",
        status=request.status,
        include_inactive=request.include_inactive,
    )
    sessions = [
        await _session_summary_from_orm(
            session_obj=session_obj,
            read_models=read_models,
        )
        for session_obj in await session_query.all()
    ]
    sessions.sort(key=lambda item: (item.key, str(item.session_id)))
    return ChildSessionsListResult(
        request_id=request.request_id,
        parent_session_id=request.parent_session_id,
        sessions=sessions,
        info="identity child sessions listed",
    )


async def list_session_members_from_identity_replica(
    *,
    request: SessionMembersListRequest,
    models: IdentitySessionReplicaReadModels | None = None,
) -> SessionMembersListResult:
    read_models = _resolve_models(models)
    member_query = read_models.session_member_model.where(session_id=request.session_id)
    member_query = _apply_status_filter(
        query=member_query,
        field_name="status",
        status=request.status,
        include_inactive=request.include_inactive,
    )
    members = [
        await _session_member_summary_from_orm(
            member_obj=member,
            read_models=read_models,
        )
        for member in await member_query.all()
    ]
    members.sort(key=lambda item: (str(item.actor_id), str(item.session_member_id)))
    return SessionMembersListResult(
        request_id=request.request_id,
        session_id=request.session_id,
        members=members,
        info="identity session members listed",
    )

def _apply_status_filter(
    *,
    query: Any,
    field_name: str,
    status: str | None,
    include_inactive: bool,
) -> Any:
    if status is not None:
        return query.match(**{field_name: status})
    if not include_inactive:
        return query.match(**{field_name: "active"})
    return query


def _resolve_models(
    models: IdentitySessionReplicaReadModels | None,
) -> IdentitySessionReplicaReadModels:
    return models if models is not None else DEFAULT_IDENTITY_SESSION_REPLICA_READ_MODELS


async def _session_summary_from_orm(
    *,
    session_obj: object,
    read_models: IdentitySessionReplicaReadModels,
) -> SessionSummary:
    session_id = _uuid_attr(session_obj, "id")
    active_members = await read_models.session_member_model.many(
        session_id=session_id,
        status="active",
    )
    provider_sessions = [
        _session_provider_session_summary_from_orm(provider_session)
        for provider_session in await read_models.session_provider_session_model.many(
            session_id=session_id
        )
    ]
    provider_sessions.sort(
        key=lambda item: (
            item.provider_session_key,
            str(item.session_provider_session_id),
        )
    )
    return SessionSummary(
        session_id=session_id,
        session_config_id=_uuid_attr(session_obj, "session_config_id"),
        key=_str_attr(session_obj, "key"),
        title=_optional_str_attr(session_obj, "title"),
        description=_optional_str_attr(session_obj, "description"),
        purpose=_optional_str_attr(session_obj, "purpose"),
        status=_str_attr(session_obj, "status", default="active"),
        parent_session_id=_optional_uuid_attr(session_obj, "parent_session_id"),
        created_by_actor_id=_optional_uuid_attr(session_obj, "created_by_actor_id"),
        source_kind=_optional_str_attr(session_obj, "source_kind"),
        source_ref=_optional_str_attr(session_obj, "source_ref"),
        metadata_json=_json_object_attr(session_obj, "metadata_json"),
        provider_sessions=provider_sessions,
        member_count=len(list(active_members)),
    )


async def _session_member_summary_from_orm(
    *,
    member_obj: object,
    read_models: IdentitySessionReplicaReadModels,
) -> SessionMemberSummary:
    member_id = _uuid_attr(member_obj, "id")
    actor_roles = [
        _session_member_actor_role_summary_from_orm(actor_role)
        for actor_role in await read_models.session_member_actor_role_model.many(
            session_member_id=member_id
        )
    ]
    actor_roles.sort(key=lambda item: str(item.session_member_actor_role_id))
    return SessionMemberSummary(
        session_member_id=member_id,
        session_id=_uuid_attr(member_obj, "session_id"),
        actor_id=_uuid_attr(member_obj, "actor_id"),
        session_actor_config_id=_uuid_attr(member_obj, "session_actor_config_id"),
        status=_str_attr(member_obj, "status", default="active"),
        joined_at_unix_ms=_optional_int_attr(member_obj, "joined_at_unix_ms"),
        left_at_unix_ms=_optional_int_attr(member_obj, "left_at_unix_ms"),
        metadata_json=_json_object_attr(member_obj, "metadata_json"),
        actor_roles=actor_roles,
    )


def _session_member_actor_role_summary_from_orm(
    actor_role_obj: object,
) -> SessionMemberActorRoleSummary:
    return SessionMemberActorRoleSummary(
        session_member_actor_role_id=_uuid_attr(actor_role_obj, "id"),
        session_member_id=_uuid_attr(actor_role_obj, "session_member_id"),
        actor_role_id=_uuid_attr(actor_role_obj, "actor_role_id"),
        source_kind=_str_attr(
            actor_role_obj,
            "source_kind",
            default="identity_session",
        ),
        status=_str_attr(actor_role_obj, "status", default="active"),
        evidence_json=_json_object_attr(actor_role_obj, "evidence_json"),
    )


def _session_provider_session_summary_from_orm(
    provider_session_obj: object,
) -> SessionProviderSessionSummary:
    return SessionProviderSessionSummary(
        session_provider_session_id=_uuid_attr(provider_session_obj, "id"),
        session_id=_uuid_attr(provider_session_obj, "session_id"),
        provider_session_config_id=_uuid_attr(
            provider_session_obj,
            "provider_session_config_id",
        ),
        provider_session_key=_str_attr(provider_session_obj, "provider_session_key"),
        provider_session_ref=_optional_str_attr(
            provider_session_obj,
            "provider_session_ref",
        ),
        provider_object_instance_graph_identity_id=_optional_uuid_attr(
            provider_session_obj,
            "provider_object_instance_graph_identity_id",
        ),
        provider_class_instance_identity_id=_optional_uuid_attr(
            provider_session_obj,
            "provider_class_instance_identity_id",
        ),
        provider_object_instance_graph_branch_id=_optional_uuid_attr(
            provider_session_obj,
            "provider_object_instance_graph_branch_id",
        ),
        status=_str_attr(provider_session_obj, "status", default="active"),
        metadata_json=_json_object_attr(provider_session_obj, "metadata_json"),
    )


def _uuid_attr(obj: object, name: str) -> UUID:
    return UUID(str(getattr(obj, name)))


def _optional_uuid_attr(obj: object, name: str) -> UUID | None:
    value = getattr(obj, name, None)
    if value is None:
        return None
    return UUID(str(value))


def _str_attr(obj: object, name: str, *, default: str | None = None) -> str:
    value = getattr(obj, name, None)
    if value is None:
        if default is None:
            raise ValueError(f"required string attribute is missing: {name}")
        return default
    return str(value)


def _optional_str_attr(obj: object, name: str) -> str | None:
    value = getattr(obj, name, None)
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _optional_int_attr(obj: object, name: str) -> int | None:
    value = getattr(obj, name, None)
    if value is None:
        return None
    return int(value)


def _json_object_attr(obj: object, name: str) -> JsonObject:
    value = getattr(obj, name, None)
    if isinstance(value, Mapping):
        return cast(JsonObject, dict(value))
    return cast(JsonObject, {})


__all__ = [
    "DEFAULT_IDENTITY_SESSION_REPLICA_READ_MODELS",
    "IdentitySessionReplicaReadModels",
    "describe_session_from_identity_replica",
    "list_actor_sessions_from_identity_replica",
    "list_child_sessions_from_identity_replica",
    "list_session_members_from_identity_replica",
]
