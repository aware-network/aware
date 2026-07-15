from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.actuator.actuator_invocation_action_config import ActuatorInvocationActionConfig
    from aware_experience_ontology_dto.invocation.experience_invocation_action import ExperienceInvocationAction


class ActuatorInvocationAction(BaseModel):
    """
    Actuator-owned provenance bridge for one concrete invocation action.
    Contract:
    - `ActuatorInvocationActionConfig` is actuator-level configuration.
    - `ExperienceInvocationAction` is the actual invocation receipt.
    - This bridge records that the invocation happened through one concrete
    Actuator instance.
    """

    # Relationships
    actuator_invocation_action_config: ActuatorInvocationActionConfig | None = Field(default=None)
    experience_invocation_action: ExperienceInvocationAction | None = Field(default=None)
