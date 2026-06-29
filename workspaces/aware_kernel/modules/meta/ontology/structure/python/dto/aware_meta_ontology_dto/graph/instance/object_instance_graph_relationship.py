from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_instance import ClassInstance
    from aware_meta_ontology_dto.graph.instance.object_instance_graph import ObjectInstanceGraph


class ObjectInstanceGraphRelationship(BaseModel):
    """A Relationship between two OIGs with optional related nodes."""

    # Relationships
    target_object_instance_graph: ObjectInstanceGraph | None = Field(default=None)
    source_class_instance: ClassInstance | None = Field(default=None)
    target_class_instance: ClassInstance | None = Field(default=None)
