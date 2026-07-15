from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor import Actor
    from aware_identity_ontology_dto.session.session_config_actor_config import SessionConfigActorConfig
    from aware_identity_ontology_dto.session.session_member_actor_role import SessionMemberActorRole


class SessionMember(BaseModel):
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
