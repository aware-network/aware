from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.action.action_experience import ActionExperience


class EnvironmentExperienceEventAction(BaseModel):
    # Relationships
    action_experience: ActionExperience | None = Field(default=None)
