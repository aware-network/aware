from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_reactivity_ontology_orm_models.event.event_config_condition_config import EventConfigConditionConfig
    from aware_reactivity_ontology_orm_models.event.event_config_condition_config_scope import (
        EventConfigConditionConfigScope,
    )


class EnvironmentExperienceEventNodeScope(ORMModel):
    # Relationships
    event_config_condition_config: EventConfigConditionConfig | None = Field(default=None, exclude=True)
    projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None, exclude=True)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)
    event_config_condition_config_scope: EventConfigConditionConfigScope | None = Field(default=None, exclude=True)

    # Foreign Keys
    environment_experience_event_id: UUID = Field(description="Foreign key for EnvironmentExperienceEvent.node_scopes")
    event_config_condition_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceEventNodeScope.event_config_condition_config"
    )
    projection_experience_node_identity_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceEventNodeScope.projection_experience_node_identity"
    )
    object_instance_graph_branch_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentExperienceEventNodeScope.object_instance_graph_branch"
    )
    event_config_condition_config_scope_id: UUID | None = Field(
        default=None,
        description="Foreign key for EnvironmentExperienceEventNodeScope.event_config_condition_config_scope",
    )
