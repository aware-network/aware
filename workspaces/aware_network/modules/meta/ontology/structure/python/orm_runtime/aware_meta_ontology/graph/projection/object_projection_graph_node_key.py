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
    from aware_meta_ontology.graph.config.object_config_graph_binding_class import ObjectConfigGraphBindingClass


class ObjectProjectionGraphNodeKey(ORMModel):
    """
    Canonical ProjectionKey owner rail under one ObjectProjectionGraphNode.
    Contract:
    - Binds one projected node to one canonical OCG binding-class anchor.
    - Consumes binding + formula semantics without reintroducing encode logic here.
    - Must fail closed if the binding-class target class/attr is incompatible with the projected node.
    """

    # Relationships
    object_config_graph_binding_class: ObjectConfigGraphBindingClass

    # Attributes
    key: str
    position: int | None = Field(default=None)
    required: bool = Field(default=True)

    # Foreign Keys
    object_projection_graph_node_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphNode.object_projection_graph_node_keys"
    )
    object_config_graph_binding_class_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectProjectionGraphNodeKey.object_config_graph_binding_class"
    )

    @classmethod
    async def build_via_object_projection_graph_node(
        cls,
        object_projection_graph_node_id: UUID,
        object_config_graph_binding_class_id: UUID,
        key: str,
        position: int | None = None,
        required: bool = True,
    ) -> ObjectProjectionGraphNodeKey:
        """
        Create deterministic ObjectProjectionGraphNodeKey under one ObjectProjectionGraphNode.

        Contract:
        - Parent `object_projection_graph_node_id` is propagated by constructor lowering.
        - Identity resolves from `(object_projection_graph_node_id via path,
        object_config_graph_binding_class_id, key)`.
        - The binding-class target class must match the projected node class.
        - The binding-class target attribute must be an identity-resolution anchor.
        """

        payload = {
            "object_projection_graph_node_id": object_projection_graph_node_id,
            "object_config_graph_binding_class_id": object_config_graph_binding_class_id,
            "key": key,
            "position": position,
            "required": required,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_object_projection_graph_node", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectProjectionGraphNodeKey):
            return value
        return ObjectProjectionGraphNodeKey.validate_invocation_value(value)


class ObjectProjectionGraphNodeKeyBuildViaObjectProjectionGraphNodeInput(BaseModel):
    object_projection_graph_node_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraphNode.object_projection_graph_node_keys"
    )
    object_config_graph_binding_class_id: UUID
    key: str
    position: int | None = Field(default=None)
    required: bool = Field(default=True)


class ObjectProjectionGraphNodeKeyBuildViaObjectProjectionGraphNodeOutput(BaseModel):
    value: ObjectProjectionGraphNodeKey


FUNCTIONS = {
    "ObjectProjectionGraphNodeKey": {
        "build_via_object_projection_graph_node": {
            "canonical": {
                "name": "build_via_object_projection_graph_node",
                "description": "Create deterministic ObjectProjectionGraphNodeKey under one ObjectProjectionGraphNode.\n\nContract:\n- Parent `object_projection_graph_node_id` is propagated by constructor lowering.\n- Identity resolves from `(object_projection_graph_node_id via path, object_config_graph_binding_class_id, key)`.\n- The binding-class target class must match the projected node class.\n- The binding-class target attribute must be an identity-resolution anchor.",
                "is_constructor": True,
            },
            "input": ObjectProjectionGraphNodeKeyBuildViaObjectProjectionGraphNodeInput,
            "output": ObjectProjectionGraphNodeKeyBuildViaObjectProjectionGraphNodeOutput,
        },
    },
}

__all__ = [
    "ObjectProjectionGraphNodeKey",
    "ObjectProjectionGraphNodeKeyBuildViaObjectProjectionGraphNodeInput",
    "ObjectProjectionGraphNodeKeyBuildViaObjectProjectionGraphNodeOutput",
    "FUNCTIONS",
]
