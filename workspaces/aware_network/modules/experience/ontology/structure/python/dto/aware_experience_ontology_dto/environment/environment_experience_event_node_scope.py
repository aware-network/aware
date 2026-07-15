from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_reactivity_ontology_dto.event.event_config_condition_config import EventConfigConditionConfig
    from aware_reactivity_ontology_dto.event.event_config_condition_config_scope import EventConfigConditionConfigScope


class EnvironmentExperienceEventNodeScope(BaseModel):
    # Relationships
    event_config_condition_config: EventConfigConditionConfig | None = Field(default=None)
    projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)
    event_config_condition_config_scope: EventConfigConditionConfigScope | None = Field(default=None)
