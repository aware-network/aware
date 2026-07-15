from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.action.action_experience_invocation_action import (
        ActionExperienceInvocationAction,
    )
    from aware_experience_ontology_orm_models.action.action_experience_invocation_request_field import (
        ActionExperienceInvocationRequestField,
    )
    from aware_experience_ontology_orm_models.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )


class ActionExperienceInvocation(ORMModel):
    """
    ActionExperience-owned binding to a reusable invocation action config.
    Contract:
    - `ActionExperience` remains environment-scoped policy for Reactivity
    action vocabulary.
    - `ExperienceInvocationActionConfig` remains the shared API/SDK target and
    typed contract binding.
    - Many invocation configs may bind to one action experience; later dispatch
    lanes choose among them.
    """

    # Relationships
    experience_invocation_action_config: ExperienceInvocationActionConfig | None = Field(default=None)
    invocation_actions: list[ActionExperienceInvocationAction] = Field(default_factory=list)
    request_fields: list[ActionExperienceInvocationRequestField] = Field(default_factory=list)

    # Foreign Keys
    action_experience_id: UUID = Field(description="Foreign key for ActionExperience.action_experience_invocations")
    experience_invocation_action_config_id: UUID = Field(
        description="Foreign key for ActionExperienceInvocation.experience_invocation_action_config"
    )
