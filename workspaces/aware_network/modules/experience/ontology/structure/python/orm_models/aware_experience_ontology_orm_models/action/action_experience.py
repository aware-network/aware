from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.action.action_experience_invocation import ActionExperienceInvocation
    from aware_experience_ontology_orm_models.action.action_experience_program import ActionExperienceProgram
    from aware_reactivity_ontology_orm_models.action.action_config import ActionConfig


class ActionExperience(ORMModel):
    # Relationships
    action_config: ActionConfig | None = Field(default=None, exclude=True)
    action_experience_programs: list[ActionExperienceProgram] = Field(default_factory=list, exclude=True)
    action_experience_invocations: list[ActionExperienceInvocation] = Field(default_factory=list, exclude=True)

    # Foreign Keys
    action_config_id: UUID = Field(description="Foreign key for ActionExperience.action_config")
