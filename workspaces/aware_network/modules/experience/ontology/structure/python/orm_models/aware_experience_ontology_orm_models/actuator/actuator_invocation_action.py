from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.actuator.actuator_invocation_action_config import (
        ActuatorInvocationActionConfig,
    )
    from aware_experience_ontology_orm_models.invocation.experience_invocation_action import ExperienceInvocationAction


class ActuatorInvocationAction(ORMModel):
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

    # Foreign Keys
    actuator_id: UUID = Field(description="Foreign key for Actuator.invocation_actions")
    actuator_invocation_action_config_id: UUID = Field(
        description="Foreign key for ActuatorInvocationAction.actuator_invocation_action_config"
    )
    experience_invocation_action_id: UUID = Field(
        description="Foreign key for ActuatorInvocationAction.experience_invocation_action"
    )
