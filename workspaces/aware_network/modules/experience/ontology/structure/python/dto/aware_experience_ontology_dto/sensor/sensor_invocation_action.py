from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.invocation.experience_invocation_action import ExperienceInvocationAction
    from aware_experience_ontology_dto.sensor.sensor_invocation_action_config import SensorInvocationActionConfig


class SensorInvocationAction(BaseModel):
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
