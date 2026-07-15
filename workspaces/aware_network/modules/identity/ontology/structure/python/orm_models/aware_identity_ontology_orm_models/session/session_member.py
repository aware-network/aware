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
    from aware_identity_ontology_orm_models.actor.actor import Actor
    from aware_identity_ontology_orm_models.session.session_config_actor_config import SessionConfigActorConfig
    from aware_identity_ontology_orm_models.session.session_member_actor_role import SessionMemberActorRole


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
