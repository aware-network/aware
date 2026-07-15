from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphAttributeRole,
    ObjectProjectionGraphEdgeInclude,
    ObjectProjectionGraphEdgeMultiplicity,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
    from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph


class ObjectProjectionGraphEdge(ORMModel):
    # Relationships
    class_config_relationship: ClassConfigRelationship | None = Field(default=None, exclude=True)
    object_projection_graph: ObjectProjectionGraph | None = Field(
        default=None, exclude=True, description="Reverse view for ObjectProjectionGraph.object_projection_graph_edges"
    )

    # Attributes
    attribute_role: ObjectProjectionGraphAttributeRole = Field(default=ObjectProjectionGraphAttributeRole.reference)
    depth_limit: int | None = Field(default=None)
    include: ObjectProjectionGraphEdgeInclude = Field(default=ObjectProjectionGraphEdgeInclude.required)
    loading_override: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)
    multiplicity: ObjectProjectionGraphEdgeMultiplicity = Field(default=ObjectProjectionGraphEdgeMultiplicity.many)
    traversal_direction: ClassConfigRelationshipDirection = Field(default=ClassConfigRelationshipDirection.forward)

    # Foreign Keys
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraph.object_projection_graph_edges"
    )
    class_config_relationship_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphEdge.class_config_relationship"
    )

    @classmethod
    async def build_via_object_projection_graph(
        cls,
        object_projection_graph_id: UUID,
        class_config_relationship_id: UUID,
        include: ObjectProjectionGraphEdgeInclude = ObjectProjectionGraphEdgeInclude.required,
        multiplicity: ObjectProjectionGraphEdgeMultiplicity = ObjectProjectionGraphEdgeMultiplicity.many,
        traversal_direction: ClassConfigRelationshipDirection = ClassConfigRelationshipDirection.forward,
        depth_limit: int | None = None,
        attribute_role: ObjectProjectionGraphAttributeRole = ObjectProjectionGraphAttributeRole.reference,
        loading_override: ClassConfigRelationshipSideLoadingStrategy | None = None,
    ) -> ObjectProjectionGraphEdge:
        """
        Create deterministic ObjectProjectionGraphEdge under one ObjectProjectionGraph.

        Contract:
        - Parent `object_projection_graph_id` is propagated by constructor lowering.
        - Identity is always OPG-scoped.
        """

        payload = {
            "object_projection_graph_id": object_projection_graph_id,
            "class_config_relationship_id": class_config_relationship_id,
            "include": include,
            "multiplicity": multiplicity,
            "traversal_direction": traversal_direction,
            "depth_limit": depth_limit,
            "attribute_role": attribute_role,
            "loading_override": loading_override,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_object_projection_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectProjectionGraphEdge):
            return value
        return ObjectProjectionGraphEdge.validate_invocation_value(value)


class ObjectProjectionGraphEdgeBuildViaObjectProjectionGraphInput(BaseModel):
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraph.object_projection_graph_edges"
    )
    class_config_relationship_id: UUID
    include: ObjectProjectionGraphEdgeInclude = Field(default=ObjectProjectionGraphEdgeInclude.required)
    multiplicity: ObjectProjectionGraphEdgeMultiplicity = Field(default=ObjectProjectionGraphEdgeMultiplicity.many)
    traversal_direction: ClassConfigRelationshipDirection = Field(default=ClassConfigRelationshipDirection.forward)
    depth_limit: int | None = Field(default=None)
    attribute_role: ObjectProjectionGraphAttributeRole = Field(default=ObjectProjectionGraphAttributeRole.reference)
    loading_override: ClassConfigRelationshipSideLoadingStrategy | None = Field(default=None)


class ObjectProjectionGraphEdgeBuildViaObjectProjectionGraphOutput(BaseModel):
    value: ObjectProjectionGraphEdge


FUNCTIONS = {
    "ObjectProjectionGraphEdge": {
        "build_via_object_projection_graph": {
            "canonical": {
                "name": "build_via_object_projection_graph",
                "description": "Create deterministic ObjectProjectionGraphEdge under one ObjectProjectionGraph.\n\nContract:\n- Parent `object_projection_graph_id` is propagated by constructor lowering.\n- Identity is always OPG-scoped.",
                "is_constructor": True,
            },
            "input": ObjectProjectionGraphEdgeBuildViaObjectProjectionGraphInput,
            "output": ObjectProjectionGraphEdgeBuildViaObjectProjectionGraphOutput,
        },
    },
}

__all__ = [
    "ObjectProjectionGraphEdge",
    "ObjectProjectionGraphEdgeBuildViaObjectProjectionGraphInput",
    "ObjectProjectionGraphEdgeBuildViaObjectProjectionGraphOutput",
    "FUNCTIONS",
]
