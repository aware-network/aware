from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity
    from aware_reactivity_ontology_orm_models.event.event_config_condition_config_scope_event import (
        EventConfigConditionConfigScopeEvent,
    )


class EventConfigConditionConfigScope(ORMModel):
    # Relationships
    event_config_condition_config_scope_events: list[EventConfigConditionConfigScopeEvent] = Field(
        default_factory=list, exclude=True
    )
    object_instance_graph_identity: ObjectInstanceGraphIdentity | None = Field(default=None, exclude=True)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)

    # Foreign Keys
    event_config_condition_config_id: UUID = Field(
        description="Foreign key for EventConfigConditionConfig.event_config_condition_config_scopes"
    )
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for EventConfigConditionConfigScope.object_instance_graph_identity"
    )
    object_instance_graph_branch_id: UUID | None = Field(
        default=None, description="Foreign key for EventConfigConditionConfigScope.object_instance_graph_branch"
    )
