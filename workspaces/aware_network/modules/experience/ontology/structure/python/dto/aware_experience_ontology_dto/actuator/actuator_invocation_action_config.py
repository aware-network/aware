from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )


class ActuatorInvocationActionConfig(BaseModel):
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
