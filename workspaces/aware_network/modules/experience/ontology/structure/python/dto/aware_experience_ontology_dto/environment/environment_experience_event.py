from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.environment.environment_experience_event_action import (
        EnvironmentExperienceEventAction,
    )
    from aware_experience_ontology_dto.environment.environment_experience_event_node_scope import (
        EnvironmentExperienceEventNodeScope,
    )
    from aware_reactivity_ontology_dto.event.event_config import EventConfig


class EnvironmentExperienceEvent(BaseModel):
    # Relationships
    event_config: EventConfig | None = Field(default=None)
    actions: list[EnvironmentExperienceEventAction] = Field(default_factory=list)
    node_scopes: list[EnvironmentExperienceEventNodeScope] = Field(
        default_factory=list,
        description="Declared trigger-node scopes for this environment event.\nContract:\n- Trigger scope is separate from action request target composition.\n- Each row binds one EventConfigConditionConfig to one\nProjectionExperienceNodeIdentity declared by this profile's graph\nbinding.\n- Lowering resolves the node identity through\nProjectionExperienceNodeClassIdentity into a Reactivity\nEventConfigConditionConfigScope carrying Meta ClassInstanceIdentity.",
    )
