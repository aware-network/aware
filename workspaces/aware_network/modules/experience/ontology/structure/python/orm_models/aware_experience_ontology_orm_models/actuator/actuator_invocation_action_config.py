from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )


class ActuatorInvocationActionConfig(ORMModel):
    """
    Actuator-owned binding to one generic Experience invocation action config.
    Contract:
    - An Actuator config can expose one or more reusable invocation action targets.
    - API/SDK/service target metadata lives on `ExperienceInvocationActionConfig`.
    - Actual invocation receipts are linked to concrete Actuator instances by
    `ActuatorInvocationAction`.
    """

    # Relationships
    experience_invocation_action_config: ExperienceInvocationActionConfig | None = Field(default=None)

    # Foreign Keys
    actuator_config_id: UUID = Field(description="Foreign key for ActuatorConfig.invocation_action_configs")
    experience_invocation_action_config_id: UUID = Field(
        description="Foreign key for ActuatorInvocationActionConfig.experience_invocation_action_config"
    )
