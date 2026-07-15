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


class SensorInvocationActionConfig(ORMModel):
    """
    Sensor-owned binding to one generic Experience invocation action config.
    Contract:
    - A Sensor config can expose one or more reusable invocation action targets.
    - API/SDK/service target metadata lives on `ExperienceInvocationActionConfig`.
    - Actual invocation receipts are linked to concrete Sensor instances by
    `SensorInvocationAction`.
    """

    # Relationships
    experience_invocation_action_config: ExperienceInvocationActionConfig | None = Field(default=None)

    # Foreign Keys
    sensor_config_id: UUID = Field(description="Foreign key for SensorConfig.invocation_action_configs")
    experience_invocation_action_config_id: UUID = Field(
        description="Foreign key for SensorInvocationActionConfig.experience_invocation_action_config"
    )
