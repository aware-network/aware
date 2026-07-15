from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Experience Ontology Orm Models
from aware_experience_ontology_orm_models.session.experience_session_enums import ExperienceSessionState

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment_session import EnvironmentSession
    from aware_experience_ontology_orm_models.session.experience_session_profile import ExperienceSessionProfile
    from aware_identity_ontology_orm_models.session.session import Session


class ExperienceSession(ORMModel):
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

    # Foreign Keys
    environment_experience_id: UUID = Field(description="Foreign key for EnvironmentExperience.sessions")
    identity_session_id: UUID = Field(description="Foreign key for ExperienceSession.identity_session")
    environment_session_id: UUID = Field(description="Foreign key for ExperienceSession.environment_session")
