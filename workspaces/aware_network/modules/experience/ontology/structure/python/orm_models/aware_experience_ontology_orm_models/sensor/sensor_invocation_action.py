from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.invocation.experience_invocation_action import ExperienceInvocationAction
    from aware_experience_ontology_orm_models.sensor.sensor_invocation_action_config import SensorInvocationActionConfig


class SensorInvocationAction(ORMModel):
    """
    Sensor-owned provenance bridge for one concrete invocation action.
    Contract:
    - `SensorInvocationActionConfig` is sensor-level configuration.
    - `ExperienceInvocationAction` is the actual invocation receipt.
    - This bridge records that the invocation happened through one concrete
    Sensor instance.
    """

    # Relationships
    sensor_invocation_action_config: SensorInvocationActionConfig | None = Field(default=None)
    experience_invocation_action: ExperienceInvocationAction | None = Field(default=None)

    # Foreign Keys
    sensor_id: UUID = Field(description="Foreign key for Sensor.invocation_actions")
    sensor_invocation_action_config_id: UUID = Field(
        description="Foreign key for SensorInvocationAction.sensor_invocation_action_config"
    )
    experience_invocation_action_id: UUID = Field(
        description="Foreign key for SensorInvocationAction.experience_invocation_action"
    )
