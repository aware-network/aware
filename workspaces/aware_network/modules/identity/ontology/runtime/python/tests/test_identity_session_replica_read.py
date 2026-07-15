from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar
from uuid import UUID, uuid4

import pytest

from aware_identity.session_read import IdentitySessionReplicaReadModels
from aware_identity.session_read import describe_session_from_identity_replica
from aware_identity.session_read import list_actor_sessions_from_identity_replica
from aware_identity.session_read import list_child_sessions_from_identity_replica
from aware_identity.session_read import list_session_members_from_identity_replica
from aware_identity_service_dto.session.session import ActorSessionsListRequest
from aware_identity_service_dto.session.session import ChildSessionsListRequest
from aware_identity_service_dto.session.session import SessionDescribeRequest
from aware_identity_service_dto.session.session import SessionMembersListRequest


@dataclass(frozen=True, slots=True)
class _Condition:
    field_name: str
    value: object


class _FakeQuery:
    def __init__(self, records: list[object]) -> None:
        self._records = records
        self._conditions: list[_Condition] = []

    def match(self, **eq_fields: object) -> _FakeQuery:
        for field_name, value in eq_fields.items():
            self._conditions.append(_Condition(field_name=field_name, value=value))
        return self

    def match_if_present(self, **eq_fields: object) -> _FakeQuery:
        return self.match(
            **{
                field_name: value
                for field_name, value in eq_fields.items()
                if value is not None
            }
        )

    async def all(self) -> list[object]:
        return [
            record
            for record in self._records
            if all(
                getattr(record, condition.field_name) == condition.value
                for condition in self._conditions
            )
        ]

    async def first(self) -> object | None:
        records = await self.all()
        return records[0] if records else None


class _OrmModel:
    records: ClassVar[list[object]] = []

    @classmethod
    def where(cls, **eq_fields: object) -> _FakeQuery:
        return _FakeQuery(cls.records).match(**eq_fields)

    @classmethod
    async def one(cls, **eq_fields: object) -> object | None:
        return await cls.where(**eq_fields).first()

    @classmethod
    async def by_id(cls, obj_id: UUID) -> object | None:
        return await cls.one(id=obj_id)

    @classmethod
    async def many(cls, **eq_fields: object) -> list[object]:
        return await cls.where(**eq_fields).all()


class _SessionOrmModel(_OrmModel):
    records: ClassVar[list[object]] = []


class _SessionMemberOrmModel(_OrmModel):
    records: ClassVar[list[object]] = []


class _SessionMemberActorRoleOrmModel(_OrmModel):
    records: ClassVar[list[object]] = []


class _SessionProviderSessionOrmModel(_OrmModel):
    records: ClassVar[list[object]] = []


@dataclass(frozen=True, slots=True)
class _Record:
    id: UUID
    session_config_id: UUID | None = None
    key: str | None = None
    title: str | None = None
    description: str | None = None
    purpose: str | None = None
    status: str = "active"
    parent_session_id: UUID | None = None
    created_by_actor_id: UUID | None = None
    source_kind: str | None = None
    source_ref: str | None = None
    metadata_json: dict[str, object] | None = None
    session_id: UUID | None = None
    actor_id: UUID | None = None
    session_actor_config_id: UUID | None = None
    joined_at_unix_ms: int | None = None
    left_at_unix_ms: int | None = None
    session_member_id: UUID | None = None
    actor_role_id: UUID | None = None
    source_kind_override: str | None = None
    evidence_json: dict[str, object] | None = None
    provider_session_config_id: UUID | None = None
    provider_session_key: str | None = None
    provider_session_ref: str | None = None
    provider_object_instance_graph_identity_id: UUID | None = None
    provider_class_instance_identity_id: UUID | None = None
    provider_object_instance_graph_branch_id: UUID | None = None


def _read_models() -> IdentitySessionReplicaReadModels:
    return IdentitySessionReplicaReadModels(
        session_model=_SessionOrmModel,
        session_member_model=_SessionMemberOrmModel,
        session_member_actor_role_model=_SessionMemberActorRoleOrmModel,
        session_provider_session_model=_SessionProviderSessionOrmModel,
    )


@pytest.mark.asyncio
async def test_identity_session_replica_lists_actor_sessions_and_members() -> None:
    actor_id = uuid4()
    other_actor_id = uuid4()
    session_id = uuid4()
    session_config_id = uuid4()
    member_id = uuid4()
    actor_role_id = uuid4()
    session_actor_config_id = uuid4()
    provider_session_config_id = uuid4()

    _SessionOrmModel.records = [
        _Record(
            id=session_id,
            session_config_id=session_config_id,
            key="coordination-main",
            title="Coordination Main",
            status="active",
            created_by_actor_id=actor_id,
            source_kind="goal",
            source_ref="goal://experience-attention-os",
            metadata_json={"scope": "coordination"},
        )
    ]
    _SessionMemberOrmModel.records = [
        _Record(
            id=member_id,
            session_id=session_id,
            actor_id=actor_id,
            session_actor_config_id=session_actor_config_id,
            status="active",
            joined_at_unix_ms=10,
            metadata_json={"admission": "accepted"},
        ),
        _Record(
            id=uuid4(),
            session_id=session_id,
            actor_id=other_actor_id,
            session_actor_config_id=session_actor_config_id,
            status="left",
        ),
    ]
    _SessionMemberActorRoleOrmModel.records = [
        _Record(
            id=uuid4(),
            session_member_id=member_id,
            actor_role_id=actor_role_id,
            source_kind="environment_admission",
            status="active",
            evidence_json={"receipt": "env"},
        )
    ]
    _SessionProviderSessionOrmModel.records = [
        _Record(
            id=uuid4(),
            session_id=session_id,
            provider_session_config_id=provider_session_config_id,
            provider_session_key="conversation-main",
            provider_session_ref="conversation://main",
            status="active",
            metadata_json={"provider": "conversation"},
        )
    ]

    actor_sessions = await list_actor_sessions_from_identity_replica(
        request=ActorSessionsListRequest(actor_id=actor_id),
        models=_read_models(),
    )
    session_members = await list_session_members_from_identity_replica(
        request=SessionMembersListRequest(session_id=session_id),
        models=_read_models(),
    )

    assert [session.session_id for session in actor_sessions.sessions] == [session_id]
    assert actor_sessions.sessions[0].member_count == 1
    assert (
        actor_sessions.sessions[0].provider_sessions[0].provider_session_key
        == "conversation-main"
    )
    assert [member.session_member_id for member in session_members.members] == [
        member_id
    ]
    assert session_members.members[0].actor_roles[0].actor_role_id == actor_role_id
    assert (
        session_members.members[0].actor_roles[0].source_kind == "environment_admission"
    )


@pytest.mark.asyncio
async def test_identity_session_replica_reads_session_hierarchy() -> None:
    actor_id = uuid4()
    parent_session_id = uuid4()
    child_session_id = uuid4()
    root_config_id = uuid4()
    child_config_id = uuid4()

    _SessionOrmModel.records = [
        _Record(
            id=parent_session_id,
            session_config_id=root_config_id,
            key="environment-root",
            status="active",
            created_by_actor_id=actor_id,
        ),
        _Record(
            id=child_session_id,
            session_config_id=child_config_id,
            parent_session_id=parent_session_id,
            key="experience-child",
            status="active",
            created_by_actor_id=actor_id,
        ),
        _Record(
            id=uuid4(),
            session_config_id=child_config_id,
            parent_session_id=parent_session_id,
            key="closed-child",
            status="closed",
            created_by_actor_id=actor_id,
        ),
    ]
    _SessionMemberOrmModel.records = [
        _Record(
            id=uuid4(),
            session_id=child_session_id,
            actor_id=actor_id,
            session_actor_config_id=uuid4(),
            status="active",
        ),
    ]
    _SessionMemberActorRoleOrmModel.records = []
    _SessionProviderSessionOrmModel.records = []

    described = await describe_session_from_identity_replica(
        request=SessionDescribeRequest(session_id=child_session_id),
        models=_read_models(),
    )
    children = await list_child_sessions_from_identity_replica(
        request=ChildSessionsListRequest(parent_session_id=parent_session_id),
        models=_read_models(),
    )
    actor_sessions = await list_actor_sessions_from_identity_replica(
        request=ActorSessionsListRequest(
            actor_id=actor_id,
            parent_session_id=parent_session_id,
        ),
        models=_read_models(),
    )

    assert described.session is not None
    assert described.session.session_id == child_session_id
    assert described.session.parent_session_id == parent_session_id
    assert [session.session_id for session in children.sessions] == [child_session_id]
    assert [session.session_id for session in actor_sessions.sessions] == [
        child_session_id
    ]
