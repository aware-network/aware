from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_history_ontology_orm_models.change.change import Change
    from aware_meta_ontology_orm_models.class_.class_instance_change import ClassInstanceChange
    from aware_meta_ontology_orm_models.class_.class_instance_relationship_change import ClassInstanceRelationshipChange
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph import ObjectInstanceGraph


class ObjectInstanceGraphChange(ORMModel):
    # Relationships
    object_instance_graph: ObjectInstanceGraph | None = Field(
        default=None, exclude=True, description="Explicit payload worldline target for this change tree."
    )
    change: Change
    class_instance_changes: list[ClassInstanceChange] = Field(default_factory=list)
    class_instance_relationship_changes: list[ClassInstanceRelationshipChange] = Field(default_factory=list)

    # Attributes
    type: ObjectInstanceGraphChangeType

    # Foreign Keys
    object_instance_graph_identity_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphIdentity.object_instance_graph_changes"
    )
    object_instance_graph_id: UUID = Field(
        description="Foreign key for ObjectInstanceGraphChange.object_instance_graph"
    )
    change_id: UUID | None = Field(default=None, description="Foreign key for ObjectInstanceGraphChange.change")
