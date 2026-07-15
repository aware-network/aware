from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.actor.actor_role import ActorRole


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
