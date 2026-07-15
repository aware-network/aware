from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_instance import ClassInstance
    from aware_meta_ontology_orm_models.class_.class_instance_relationship import ClassInstanceRelationship


class ObjectInstanceGraph(ORMModel):
    # Relationships
    root_class_instance: ClassInstance
    class_instances: list[ClassInstance] = Field(default_factory=list)
    class_instance_relationships: list[ClassInstanceRelationship] = Field(default_factory=list)

    # Attributes
    key: str
    name: str
    description: str | None = Field(default=None)
    hash: str

    # Foreign Keys
    object_projection_graph_id: UUID = Field(description="Foreign key for ObjectProjectionGraph.object_instance_graphs")
    root_class_instance_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectInstanceGraph.root_class_instance"
    )
