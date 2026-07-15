from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.action.action_experience_invocation import ActionExperienceInvocation
    from aware_experience_ontology_dto.action.action_experience_program import ActionExperienceProgram
    from aware_reactivity_ontology_dto.action.action_config import ActionConfig


class ActionExperience(BaseModel):
    # Relationships
    action_config: ActionConfig | None = Field(default=None)
    action_experience_programs: list[ActionExperienceProgram] = Field(default_factory=list)
    action_experience_invocations: list[ActionExperienceInvocation] = Field(default_factory=list)
