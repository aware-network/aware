from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute import Attribute
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig
    from aware_meta_ontology_orm_models.class_.class_instance_attribute import ClassInstanceAttribute
    from aware_meta_ontology_orm_models.class_.class_instance_change import ClassInstanceChange


class ClassInstance(ORMModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)
    class_instance_changes: list[ClassInstanceChange] = Field(default_factory=list, exclude=True)

    # Attributes
    source_object_id: UUID = Field(
        description="Stable external object anchor for this projected instance within one OIG worldline."
    )

    # Foreign Keys
    object_instance_graph_id: UUID = Field(description="Foreign key for ObjectInstanceGraph.class_instances")
    class_config_id: UUID = Field(description="Foreign key for ClassInstance.class_config")

    # Edges
    class_instance_attributes: list[ClassInstanceAttribute] = Field(
        default_factory=list, description="Edge association helper for attributes"
    )

    @property
    def attributes(self) -> list[Attribute]:
        return [edge.attribute for edge in self.class_instance_attributes if edge.attribute is not None]
