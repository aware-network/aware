from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_identity import ObjectInstanceGraphIdentity
    from aware_reactivity_ontology_dto.event.event_config_condition_config_scope_event import (
        EventConfigConditionConfigScopeEvent,
    )


class EventConfigConditionConfigScope(BaseModel):
    # Relationships
    event_config_condition_config_scope_events: list[EventConfigConditionConfigScopeEvent] = Field(default_factory=list)
    object_instance_graph_identity: ObjectInstanceGraphIdentity | None = Field(default=None)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None)
