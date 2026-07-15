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
    from aware_meta_ontology.class_.class_config_function_config import ClassConfigFunctionConfig
    from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph
    from aware_meta_ontology.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode


class ObjectProjectionGraphConstructor(ORMModel):
    # Relationships
    root_node: ObjectProjectionGraphNode | None = Field(default=None, exclude=True)
    function_constructor: ClassConfigFunctionConfig | None = Field(default=None, exclude=True)
    object_projection_graph: ObjectProjectionGraph | None = Field(
        default=None,
        exclude=True,
        description="Reverse view for ObjectProjectionGraph.object_projection_graph_constructors",
    )

    # Foreign Keys
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraph.object_projection_graph_constructors"
    )
    root_node_id: UUID = Field(description="Foreign key for ObjectProjectionGraphConstructor.root_node")
    function_constructor_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphConstructor.function_constructor"
    )

    @classmethod
    async def build_via_object_projection_graph(
        cls, object_projection_graph_id: UUID, root_node_id: UUID, function_constructor_id: UUID
    ) -> ObjectProjectionGraphConstructor:
        """
        Create deterministic ObjectProjectionGraphConstructor under one ObjectProjectionGraph.

        Contract:
        - Parent `object_projection_graph_id` is propagated by constructor lowering.
        - Identity is always OPG-scoped.
        """

        payload = {
            "object_projection_graph_id": object_projection_graph_id,
            "root_node_id": root_node_id,
            "function_constructor_id": function_constructor_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_object_projection_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectProjectionGraphConstructor):
            return value
        return ObjectProjectionGraphConstructor.validate_invocation_value(value)


class ObjectProjectionGraphConstructorBuildViaObjectProjectionGraphInput(BaseModel):
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraph.object_projection_graph_constructors"
    )
    root_node_id: UUID
    function_constructor_id: UUID


class ObjectProjectionGraphConstructorBuildViaObjectProjectionGraphOutput(BaseModel):
    value: ObjectProjectionGraphConstructor


FUNCTIONS = {
    "ObjectProjectionGraphConstructor": {
        "build_via_object_projection_graph": {
            "canonical": {
                "name": "build_via_object_projection_graph",
                "description": "Create deterministic ObjectProjectionGraphConstructor under one ObjectProjectionGraph.\n\nContract:\n- Parent `object_projection_graph_id` is propagated by constructor lowering.\n- Identity is always OPG-scoped.",
                "is_constructor": True,
            },
            "input": ObjectProjectionGraphConstructorBuildViaObjectProjectionGraphInput,
            "output": ObjectProjectionGraphConstructorBuildViaObjectProjectionGraphOutput,
        },
    },
}

__all__ = [
    "ObjectProjectionGraphConstructor",
    "ObjectProjectionGraphConstructorBuildViaObjectProjectionGraphInput",
    "ObjectProjectionGraphConstructorBuildViaObjectProjectionGraphOutput",
    "FUNCTIONS",
]
