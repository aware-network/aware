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
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology.actor.actor_role import ActorRole


class SessionMemberActorRole(ORMModel):
    """
    Existing Identity ActorRole evidence for one SessionMember.
    Contract:
    - Parent constructor is SessionMember.
    - References an existing ActorRole.
    - Does not grant, revoke, scope, or expire permission.
    """

    # Relationships
    actor_role: ActorRole | None = Field(default=None)

    # Attributes
    source_kind: str = Field(default="identity_session")
    status: str = Field(default="active")
    evidence_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    session_member_id: UUID = Field(description="Foreign key for SessionMember.actor_roles")
    actor_role_id: UUID = Field(description="Foreign key for SessionMemberActorRole.actor_role")

    @classmethod
    async def create_via_session_member(
        cls,
        session_member_id: UUID,
        actor_role_id: UUID,
        source_kind: str = "identity_session",
        status: str = "active",
        evidence_json: JsonObject | None = {},
    ) -> SessionMemberActorRole:
        """
        Construct one ActorRole evidence edge under a SessionMember.

        Contract:
        - `actor_role_id` resolves an existing Identity ActorRole.
        - This object records evidence only; permission lifecycle remains
          ActorRole-owned.
        """

        payload = {
            "session_member_id": session_member_id,
            "actor_role_id": actor_role_id,
            "source_kind": source_kind,
            "status": status,
            "evidence_json": evidence_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_session_member", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SessionMemberActorRole):
            return value
        return SessionMemberActorRole.validate_invocation_value(value)


class SessionMemberActorRoleCreateViaSessionMemberInput(BaseModel):
    session_member_id: UUID = Field(description="Foreign key for SessionMember.actor_roles")
    actor_role_id: UUID
    source_kind: str = Field(default="identity_session")
    status: str = Field(default="active")
    evidence_json: JsonObject | None = Field(default_factory=JsonObject)


class SessionMemberActorRoleCreateViaSessionMemberOutput(BaseModel):
    value: SessionMemberActorRole


FUNCTIONS = {
    "SessionMemberActorRole": {
        "create_via_session_member": {
            "canonical": {
                "name": "create_via_session_member",
                "description": "Construct one ActorRole evidence edge under a SessionMember.\n\nContract:\n- `actor_role_id` resolves an existing Identity ActorRole.\n- This object records evidence only; permission lifecycle remains\n  ActorRole-owned.",
                "is_constructor": True,
            },
            "input": SessionMemberActorRoleCreateViaSessionMemberInput,
            "output": SessionMemberActorRoleCreateViaSessionMemberOutput,
        },
    },
}

__all__ = [
    "SessionMemberActorRole",
    "SessionMemberActorRoleCreateViaSessionMemberInput",
    "SessionMemberActorRoleCreateViaSessionMemberOutput",
    "FUNCTIONS",
]
