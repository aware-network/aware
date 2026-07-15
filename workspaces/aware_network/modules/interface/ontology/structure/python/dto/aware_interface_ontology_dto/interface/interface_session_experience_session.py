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
    from aware_experience_ontology_dto.session.experience_session import ExperienceSession


class InterfaceSessionExperienceSession(BaseModel):
    """
    InterfaceSession-owned portal to one committed ExperienceSession.
    Contract:
    - Interface owns only the mount/provenance row.
    - Experience owns ExperienceSession and all profile, Environment, lens,
    action, and downstream Attention resolution state.
    - One InterfaceSession may mount many ExperienceSessions.
    - The same ExperienceSession may be mounted by other InterfaceSessions.
    """

    # Relationships
    experience_session: ExperienceSession | None = Field(default=None)

    # Attributes
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
