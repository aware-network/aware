from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.environment.environment_experience_event_action import (
        EnvironmentExperienceEventAction,
    )
    from aware_experience_ontology_orm_models.environment.environment_experience_event_node_scope import (
        EnvironmentExperienceEventNodeScope,
    )
    from aware_reactivity_ontology_orm_models.event.event_config import EventConfig


class EnvironmentExperienceEvent(ORMModel):
    # Relationships
    event_config: EventConfig | None = Field(default=None, exclude=True)
    actions: list[EnvironmentExperienceEventAction] = Field(default_factory=list, exclude=True)
    node_scopes: list[EnvironmentExperienceEventNodeScope] = Field(
        default_factory=list,
        exclude=True,
        description="Declared trigger-node scopes for this environment event.\nContract:\n- Trigger scope is separate from action request target composition.\n- Each row binds one EventConfigConditionConfig to one\nProjectionExperienceNodeIdentity declared by this profile's graph\nbinding.\n- Lowering resolves the node identity through\nProjectionExperienceNodeClassIdentity into a Reactivity\nEventConfigConditionConfigScope carrying Meta ClassInstanceIdentity.",
    )

    # Foreign Keys
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.events"
    )
    event_config_id: UUID = Field(description="Foreign key for EnvironmentExperienceEvent.event_config")
