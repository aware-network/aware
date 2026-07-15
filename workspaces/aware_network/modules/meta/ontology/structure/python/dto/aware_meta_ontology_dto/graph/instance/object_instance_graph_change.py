from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.graph.instance.object_instance_graph_change_enums import ObjectInstanceGraphChangeType

if TYPE_CHECKING:
    from aware_history_ontology_dto.change.change import Change
    from aware_meta_ontology_dto.class_.class_instance_change import ClassInstanceChange
    from aware_meta_ontology_dto.class_.class_instance_relationship_change import ClassInstanceRelationshipChange
    from aware_meta_ontology_dto.graph.instance.object_instance_graph import ObjectInstanceGraph


class ObjectInstanceGraphChange(BaseModel):
    # Relationships
    object_instance_graph: ObjectInstanceGraph | None = Field(
        default=None, description="Explicit payload worldline target for this change tree."
    )
    change: Change
    class_instance_changes: list[ClassInstanceChange] = Field(default_factory=list)
    class_instance_relationship_changes: list[ClassInstanceRelationshipChange] = Field(default_factory=list)

    # Attributes
    type: ObjectInstanceGraphChangeType
