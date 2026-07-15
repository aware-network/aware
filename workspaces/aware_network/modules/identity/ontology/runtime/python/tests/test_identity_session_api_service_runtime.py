from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_identity_ontology.session.session import Session
from aware_identity_ontology.session.session_config import SessionConfig
from aware_identity_ontology.session.session_member import SessionMember
from aware_identity_ontology.session.session_member_actor_role import (
    SessionMemberActorRole,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    reset_invocation_provider,
    set_invocation_provider,
)
from aware_types import JsonObject


@dataclass(frozen=True, slots=True)
class _RecordedInvocation:
    call_target: str
    class_name: str
    function_name: str
    object_id: UUID | None
    payload: dict[str, Any]


class _RecordingLaneBinder:
    def __init__(self) -> None:
        self.binds: list[dict[str, Any]] = []
        self.invocations: list[_RecordedInvocation] = []

    def bind(
        self,
        *,
        projection: str,
        branch_id: UUID,
        actor_id: UUID | None = None,
    ) -> _RecordingLane:
        self.binds.append(
            {
                "projection": projection,
                "branch_id": branch_id,
                "actor_id": actor_id,
            }
        )
        return _RecordingLane(binder=self)


@dataclass(frozen=True, slots=True)
class _RecordingLane:
    binder: _RecordingLaneBinder

    @property
    def branch_id(self) -> UUID:
        return self.binder.binds[-1]["branch_id"]

    @contextmanager
    def activate(
        self,
        *,
        commit: bool = True,
        publish: bool = False,
    ) -> Iterator[object]:
        _ = commit, publish
        token = set_invocation_provider(_RecordingProvider(binder=self.binder))
        try:
            yield self
        finally:
            reset_invocation_provider(token)


@dataclass(frozen=True, slots=True)
class _RecordingProvider:
    binder: _RecordingLaneBinder

    async def invoke_instance(
        self,
        *,
        orm_model: ORMModel,
        function_name: str,
        payload: Mapping[str, Any],
    ) -> Any:
        object_id = orm_model.id if isinstance(orm_model.id, UUID) else None
        self.binder.invocations.append(
            _RecordedInvocation(
                call_target="instance",
                class_name=type(orm_model).__name__,
                function_name=function_name,
                object_id=object_id,
                payload=dict(payload),
            )
        )
        if isinstance(orm_model, SessionConfig) and function_name == "start_session":
            from aware_identity_ontology.stable_ids import stable_session_id

            session_id = stable_session_id(
                session_config_id=cast(UUID, orm_model.id),
                parent_session_scope_key=str(payload["parent_session_scope_key"]),
                key=str(payload["key"]),
            )
            return {
                "value": Session.model_construct(
                    id=session_id,
                    session_config_id=orm_model.id,
                    key=payload["key"],
                    parent_session_scope_key=payload["parent_session_scope_key"],
                )
            }
        if isinstance(orm_model, Session) and function_name == "join_actor":
            from aware_identity_ontology.stable_ids import stable_session_member_id

            member_id = stable_session_member_id(
                session_id=cast(UUID, orm_model.id),
                actor_id=cast(UUID, payload["actor_id"]),
            )
            return {
                "value": SessionMember.model_construct(
                    id=member_id,
                    session_id=orm_model.id,
                    actor_id=payload["actor_id"],
                )
            }
        if isinstance(orm_model, SessionMember) and function_name == "add_actor_role":
            from aware_identity_ontology.stable_ids import (
                stable_session_member_actor_role_id,
            )

            edge_id = stable_session_member_actor_role_id(
                session_member_id=cast(UUID, orm_model.id),
                actor_role_id=cast(UUID, payload["actor_role_id"]),
            )
            return {
                "value": SessionMemberActorRole.model_construct(
                    id=edge_id,
                    session_member_id=orm_model.id,
                    actor_role_id=payload["actor_role_id"],
                )
            }
        raise AssertionError(
            f"unexpected instance invocation: {orm_model}.{function_name}"
        )

    async def invoke_constructor(
        self,
        *,
        orm_class: type[ORMModel],
        function_name: str,
        payload: Mapping[str, Any],
    ) -> Any:
        raise AssertionError(
            f"unexpected constructor invocation: {orm_class}.{function_name}"
        )


@pytest.mark.asyncio
async def test_identity_session_runtime_starts_session_with_semantic_facade() -> None:
    from aware_identity.session import (
        IdentitySessionOperationContext,
        resolve_identity_session_runtime_context,
        start_session,
    )
    from aware_identity_ontology.stable_ids import stable_session_id

    binder = _RecordingLaneBinder()
    actor_id = uuid4()
    runtime_context = resolve_identity_session_runtime_context(lane_binder=binder)
    operation_context = IdentitySessionOperationContext(actor_id=actor_id)
    session_config_id = uuid4()

    session_id = await start_session(
        runtime_context=runtime_context,
        operation_context=operation_context,
        session_config_id=session_config_id,
        key="planning",
        title="Planning",
        description=None,
        purpose="proof",
        status="active",
        created_by_actor_id=None,
        source_kind="pytest",
        source_ref=None,
        metadata_json=cast(JsonObject, {"source": "test"}),
    )

    assert session_id == stable_session_id(
        session_config_id=session_config_id,
        parent_session_scope_key="root",
        key="planning",
    )
    assert binder.binds == [
        {
            "projection": "SessionConfig",
            "branch_id": session_config_id,
            "actor_id": actor_id,
        }
    ]
    assert len(binder.invocations) == 1
    invocation = binder.invocations[0]
    assert invocation.call_target == "instance"
    assert invocation.class_name == "SessionConfig"
    assert invocation.function_name == "start_session"
    assert invocation.object_id == session_config_id
    assert invocation.payload["parent_session_scope_key"] == "root"
    assert invocation.payload["parent_session_id"] is None
    assert invocation.payload["key"] == "planning"


@pytest.mark.asyncio
async def test_identity_session_runtime_starts_child_session_with_parent_scope() -> (
    None
):
    from aware_identity.session import (
        IdentitySessionOperationContext,
        resolve_identity_session_runtime_context,
        start_session,
    )
    from aware_identity_ontology.stable_ids import stable_session_id

    binder = _RecordingLaneBinder()
    runtime_context = resolve_identity_session_runtime_context(lane_binder=binder)
    operation_context = IdentitySessionOperationContext(actor_id=uuid4())
    session_config_id = uuid4()
    parent_session_id = uuid4()

    session_id = await start_session(
        runtime_context=runtime_context,
        operation_context=operation_context,
        session_config_id=session_config_id,
        parent_session_id=parent_session_id,
        parent_session_scope_key=str(parent_session_id),
        key="software-dev",
        title="Software Dev",
        description=None,
        purpose="Experience child scope",
        status="active",
        created_by_actor_id=None,
        source_kind="experience",
        source_ref=None,
        metadata_json=cast(JsonObject, {"source": "test"}),
    )

    assert session_id == stable_session_id(
        session_config_id=session_config_id,
        parent_session_scope_key=str(parent_session_id),
        key="software-dev",
    )
    invocation = binder.invocations[0]
    assert invocation.payload["parent_session_scope_key"] == str(parent_session_id)
    assert invocation.payload["parent_session_id"] == parent_session_id


@pytest.mark.asyncio
async def test_identity_session_runtime_records_membership_via_session_facade() -> None:
    from aware_identity.session import (
        IdentitySessionOperationContext,
        join_session,
        resolve_identity_session_runtime_context,
    )

    binder = _RecordingLaneBinder()
    actor_id = uuid4()
    runtime_context = resolve_identity_session_runtime_context(lane_binder=binder)
    operation_context = IdentitySessionOperationContext(actor_id=uuid4())
    session_id = uuid4()
    session_actor_config_id = uuid4()

    member_id = await join_session(
        runtime_context=runtime_context,
        operation_context=operation_context,
        session_id=session_id,
        actor_id=actor_id,
        session_actor_config_id=session_actor_config_id,
        status="active",
        joined_at_unix_ms=123,
        left_at_unix_ms=None,
        metadata_json=cast(JsonObject, {"source": "test"}),
    )

    assert member_id is not None
    assert binder.binds[0]["projection"] == "Session"
    assert binder.binds[0]["branch_id"] == session_id
    assert len(binder.invocations) == 1
    invocation = binder.invocations[0]
    assert invocation.class_name == "Session"
    assert invocation.function_name == "join_actor"
    assert invocation.object_id == session_id
    assert invocation.payload["actor_id"] == actor_id
    assert invocation.payload["session_actor_config_id"] == session_actor_config_id


@pytest.mark.asyncio
async def test_identity_session_runtime_records_actor_role_on_member_facade() -> None:
    from aware_identity.session import (
        IdentitySessionOperationContext,
        record_session_member_actor_role,
        resolve_identity_session_runtime_context,
    )
    from aware_identity_ontology.stable_ids import stable_session_member_actor_role_id

    binder = _RecordingLaneBinder()
    runtime_context = resolve_identity_session_runtime_context(lane_binder=binder)
    operation_context = IdentitySessionOperationContext(actor_id=uuid4())
    session_id = uuid4()
    session_member_id = uuid4()
    actor_role_id = uuid4()

    edge_id = await record_session_member_actor_role(
        runtime_context=runtime_context,
        operation_context=operation_context,
        session_id=session_id,
        session_member_id=session_member_id,
        actor_role_id=actor_role_id,
        source_kind="environment_admission",
        status="active",
        evidence_json=cast(JsonObject, {"receipt": "environment"}),
    )

    assert edge_id == stable_session_member_actor_role_id(
        session_member_id=session_member_id,
        actor_role_id=actor_role_id,
    )
    assert binder.binds[0]["projection"] == "Session"
    assert binder.binds[0]["branch_id"] == session_id
    assert len(binder.invocations) == 1
    invocation = binder.invocations[0]
    assert invocation.class_name == "SessionMember"
    assert invocation.function_name == "add_actor_role"
    assert invocation.object_id == session_member_id
    assert invocation.payload["actor_role_id"] == actor_role_id
    assert invocation.payload["source_kind"] == "environment_admission"
    assert invocation.payload["status"] == "active"
    assert invocation.payload["evidence_json"] == {"receipt": "environment"}
