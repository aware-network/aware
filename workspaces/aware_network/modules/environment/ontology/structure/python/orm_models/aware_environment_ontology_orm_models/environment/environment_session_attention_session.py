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
    from aware_attention_ontology_orm_models.session.attention_session import AttentionSession


class EnvironmentSessionAttentionSession(ORMModel):
    """
    EnvironmentSession-owned portal to one AttentionSession.
    Contract:
    - Environment does not own or inspect AttentionSession internals.
    - One EnvironmentSession may resolve against many AttentionSessions.
    - The same AttentionSession may be shared by other EnvironmentSessions.
    - This is a pure relationship object, not a capability.
    """

    # Relationships
    attention_session: AttentionSession | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    environment_session_id: UUID = Field(description="Foreign key for EnvironmentSession.attention_sessions")
    attention_session_id: UUID = Field(
        description="Foreign key for EnvironmentSessionAttentionSession.attention_session"
    )
