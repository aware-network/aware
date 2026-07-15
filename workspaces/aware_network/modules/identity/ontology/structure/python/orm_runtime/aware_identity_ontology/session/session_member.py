from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology.actor.actor import Actor
    from aware_identity_ontology.session.session_config_actor_config import SessionConfigActorConfig
    from aware_identity_ontology.session.session_member_actor_role import SessionMemberActorRole


class SessionMember(ORMModel):
    """
    Actor participation in one Identity-owned Session.
    Contract:
    - Parent constructor is Session.
    - Member points to Actor directly and to required SessionConfigActorConfig.
    - ActorRole evidence is stored through SessionMemberActorRole child edges.
    - This object is domain-neutral and does not own Environment/Experience/
    Attention-specific state.
    """

    # Relationships
    actor: Actor | None = Field(default=None)
    session_actor_config: SessionConfigActorConfig | None = Field(default=None)
    actor_roles: list[SessionMemberActorRole] = Field(default_factory=list)

    # Attributes
    status: str = Field(default="active")
    joined_at_unix_ms: int | None = Field(default=None)
    left_at_unix_ms: int | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    session_id: UUID = Field(description="Foreign key for Session.members")
    actor_id: UUID = Field(description="Foreign key for SessionMember.actor")
    session_actor_config_id: UUID = Field(description="Foreign key for SessionMember.session_actor_config")

    async def add_actor_role(
        self,
        actor_role_id: UUID,
        source_kind: str = "identity_session",
        status: str = "active",
        evidence_json: JsonObject | None = {},
    ) -> SessionMemberActorRole:
        """
        Record an existing Identity ActorRole as SessionMember evidence.

        Contract:
        - This does not grant, revoke, scope, or expire permission.
        - Identity owns ActorRole lifecycle and any future temporal semantics.
        """

        payload = {
            "actor_role_id": actor_role_id,
            "source_kind": source_kind,
            "status": status,
            "evidence_json": evidence_json,
        }
        result = await invoke_instance(orm_model=self, function_name="add_actor_role", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_identity_ontology.session.session_member_actor_role import SessionMemberActorRole

        if isinstance(value, SessionMemberActorRole):
            return value
        return SessionMemberActorRole.validate_invocation_value(value)

    @classmethod
    async def create_via_session(
        cls,
        session_id: UUID,
        actor_id: UUID,
        session_actor_config_id: UUID,
        status: str = "active",
        joined_at_unix_ms: int | None = None,
        left_at_unix_ms: int | None = None,
        metadata_json: JsonObject | None = {},
    ) -> SessionMember:
        """
        Construct one SessionMember under a Session.

        Contract:
        - Identity is Session-scoped by Actor.
        - Session participation policy is selected by SessionConfigActorConfig.
        - Role evidence must be added as child ActorRole edges, not scalar UUIDs.
        """

        payload = {
            "session_id": session_id,
            "actor_id": actor_id,
            "session_actor_config_id": session_actor_config_id,
            "status": status,
            "joined_at_unix_ms": joined_at_unix_ms,
            "left_at_unix_ms": left_at_unix_ms,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SessionMember):
            return value
        return SessionMember.validate_invocation_value(value)


class SessionMemberAddActorRoleInput(BaseModel):
    actor_role_id: UUID
    source_kind: str = Field(default="identity_session")
    status: str = Field(default="active")
    evidence_json: JsonObject | None = Field(default_factory=JsonObject)


class SessionMemberAddActorRoleOutput(BaseModel):
    value: SessionMemberActorRole


class SessionMemberCreateViaSessionInput(BaseModel):
    session_id: UUID = Field(description="Foreign key for Session.members")
    actor_id: UUID
    session_actor_config_id: UUID
    status: str = Field(default="active")
    joined_at_unix_ms: int | None = Field(default=None)
    left_at_unix_ms: int | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class SessionMemberCreateViaSessionOutput(BaseModel):
    value: SessionMember


FUNCTIONS = {
    "SessionMember": {
        "add_actor_role": {
            "canonical": {
                "name": "add_actor_role",
                "description": "Record an existing Identity ActorRole as SessionMember evidence.\n\nContract:\n- This does not grant, revoke, scope, or expire permission.\n- Identity owns ActorRole lifecycle and any future temporal semantics.",
                "is_constructor": False,
            },
            "input": SessionMemberAddActorRoleInput,
            "output": SessionMemberAddActorRoleOutput,
        },
        "create_via_session": {
            "canonical": {
                "name": "create_via_session",
                "description": "Construct one SessionMember under a Session.\n\nContract:\n- Identity is Session-scoped by Actor.\n- Session participation policy is selected by SessionConfigActorConfig.\n- Role evidence must be added as child ActorRole edges, not scalar UUIDs.",
                "is_constructor": True,
            },
            "input": SessionMemberCreateViaSessionInput,
            "output": SessionMemberCreateViaSessionOutput,
        },
    },
}

__all__ = [
    "SessionMember",
    "SessionMemberAddActorRoleInput",
    "SessionMemberAddActorRoleOutput",
    "SessionMemberCreateViaSessionInput",
    "SessionMemberCreateViaSessionOutput",
    "FUNCTIONS",
]
