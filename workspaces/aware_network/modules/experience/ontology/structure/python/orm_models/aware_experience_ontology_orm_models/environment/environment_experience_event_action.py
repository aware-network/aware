from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.action.action_experience import ActionExperience


class EnvironmentExperienceEventAction(ORMModel):
    # Relationships
    action_experience: ActionExperience | None = Field(default=None, exclude=True)

    # Foreign Keys
    environment_experience_event_id: UUID = Field(description="Foreign key for EnvironmentExperienceEvent.actions")
    action_experience_id: UUID = Field(description="Foreign key for EnvironmentExperienceEventAction.action_experience")
