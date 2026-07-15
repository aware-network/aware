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
    from aware_identity_ontology_dto.session.session_member import SessionMember
    from aware_identity_ontology_dto.session.session_provider_session import SessionProviderSession


class Session(BaseModel):
    """
    Identity-owned concrete actor-session container.
    Contract:
    - Parent constructor is SessionConfig.
    - Session is generic actor participation state, not Environment,
    Experience, or Attention topology.
    - Domains wrap/bridge to this object when they need domain-specific
    session meaning.
    """

    # Relationships
    parent_session: Session | None = Field(default=None)
    created_by_actor: Actor | None = Field(default=None)
    members: list[SessionMember] = Field(default_factory=list)
    provider_sessions: list[SessionProviderSession] = Field(default_factory=list)

    # Attributes
    key: str
    parent_session_scope_key: str = Field(default="root")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
