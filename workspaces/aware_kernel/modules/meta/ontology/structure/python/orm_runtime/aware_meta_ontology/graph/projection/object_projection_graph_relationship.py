from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology.graph.instance.object_instance_graph_relationship import ObjectInstanceGraphRelationship
    from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph
    from aware_meta_ontology.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode


class ObjectProjectionGraphRelationship(ORMModel):
    """A Relationship between two OPGs with optional related nodes."""

    # Relationships
    target_object_projection_graph: ObjectProjectionGraph | None = Field(default=None, exclude=True)
    class_config_relationship: ClassConfigRelationship | None = Field(default=None, exclude=True)
    source_object_projection_graph_node: ObjectProjectionGraphNode | None = Field(default=None, exclude=True)
    target_object_projection_graph_node: ObjectProjectionGraphNode | None = Field(default=None, exclude=True)
    object_instance_graph_relationships: list[ObjectInstanceGraphRelationship] = Field(
        default_factory=list, exclude=True
    )
    object_projection_graph: ObjectProjectionGraph | None = Field(
        default=None,
        exclude=True,
        description="Reverse view for ObjectProjectionGraph.object_projection_graph_relationships",
    )

    # Foreign Keys
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraph.object_projection_graph_relationships"
    )
    target_object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphRelationship.target_object_projection_graph"
    )
    class_config_relationship_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphRelationship.class_config_relationship"
    )
    source_object_projection_graph_node_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphRelationship.source_object_projection_graph_node"
    )
    target_object_projection_graph_node_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphRelationship.target_object_projection_graph_node"
    )

    @classmethod
    async def build_via_object_projection_graph(
        cls,
        object_projection_graph_id: UUID,
        target_object_projection_graph_id: UUID,
        class_config_relationship_id: UUID,
        source_object_projection_graph_node_id: UUID,
        target_object_projection_graph_node_id: UUID,
    ) -> ObjectProjectionGraphRelationship:
        """
        Create deterministic ObjectProjectionGraphRelationship under one ObjectProjectionGraph.

        Contract:
        - Parent `object_projection_graph_id` is propagated by constructor lowering.
        - Identity is always source-OPG-scoped.
        """

        payload = {
            "object_projection_graph_id": object_projection_graph_id,
            "target_object_projection_graph_id": target_object_projection_graph_id,
            "class_config_relationship_id": class_config_relationship_id,
            "source_object_projection_graph_node_id": source_object_projection_graph_node_id,
            "target_object_projection_graph_node_id": target_object_projection_graph_node_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_object_projection_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectProjectionGraphRelationship):
            return value
        return ObjectProjectionGraphRelationship.validate_invocation_value(value)


class ObjectProjectionGraphRelationshipBuildViaObjectProjectionGraphInput(BaseModel):
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraph.object_projection_graph_relationships"
    )
    target_object_projection_graph_id: UUID
    class_config_relationship_id: UUID
    source_object_projection_graph_node_id: UUID
    target_object_projection_graph_node_id: UUID


class ObjectProjectionGraphRelationshipBuildViaObjectProjectionGraphOutput(BaseModel):
    value: ObjectProjectionGraphRelationship


FUNCTIONS = {
    "ObjectProjectionGraphRelationship": {
        "build_via_object_projection_graph": {
            "canonical": {
                "name": "build_via_object_projection_graph",
                "description": "Create deterministic ObjectProjectionGraphRelationship under one ObjectProjectionGraph.\n\nContract:\n- Parent `object_projection_graph_id` is propagated by constructor lowering.\n- Identity is always source-OPG-scoped.",
                "is_constructor": True,
            },
            "input": ObjectProjectionGraphRelationshipBuildViaObjectProjectionGraphInput,
            "output": ObjectProjectionGraphRelationshipBuildViaObjectProjectionGraphOutput,
        },
    },
}

__all__ = [
    "ObjectProjectionGraphRelationship",
    "ObjectProjectionGraphRelationshipBuildViaObjectProjectionGraphInput",
    "ObjectProjectionGraphRelationshipBuildViaObjectProjectionGraphOutput",
    "FUNCTIONS",
]
