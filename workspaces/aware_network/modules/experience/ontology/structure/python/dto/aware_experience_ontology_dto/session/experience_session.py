from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology Dto
from aware_experience_ontology_dto.session.experience_session_enums import ExperienceSessionState

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment_session import EnvironmentSession
    from aware_experience_ontology_dto.session.experience_session_profile import ExperienceSessionProfile
    from aware_identity_ontology_dto.session.session import Session


class ExperienceSession(BaseModel):
    """
    Experience-owned committed resolution state for one child Identity Session.
    Contract:
    - Identity Session owns participation, roles, lifecycle, and providers.
    - EnvironmentSession owns shared thread/layout and Attention portals.
    - ExperienceSession owns session-local profile mount rows and local state.
    - Concrete visible/active state remains scoped through Attention and
    Experience view bindings; there is no session-global active projection.
    """

    # Relationships
    identity_session: Session | None = Field(default=None)
    environment_session: EnvironmentSession | None = Field(default=None)
    profiles: list[ExperienceSessionProfile] = Field(default_factory=list)

    # Attributes
    state: ExperienceSessionState
