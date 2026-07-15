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
from aware_meta_ontology.graph.projection.object_projection_graph_enums import ObjectProjectionGraphNodeSelection

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_meta_ontology.graph.projection.object_projection_graph import ObjectProjectionGraph
    from aware_meta_ontology.graph.projection.object_projection_graph_node_key import ObjectProjectionGraphNodeKey


class ObjectProjectionGraphNode(ORMModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)
    object_projection_graph_node_keys: list[ObjectProjectionGraphNodeKey] = Field(default_factory=list)
    object_projection_graph: ObjectProjectionGraph | None = Field(
        default=None, exclude=True, description="Reverse view for ObjectProjectionGraph.object_projection_graph_nodes"
    )

    # Attributes
    is_root: bool
    policy_refs: list[str] = Field(default_factory=list)
    required_for_validity: bool = Field(default=False)
    selection: ObjectProjectionGraphNodeSelection = Field(default=ObjectProjectionGraphNodeSelection.all)
    selector_condition_id: UUID | None = Field(default=None)
    top_n: int | None = Field(default=None)

    # Foreign Keys
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraph.object_projection_graph_nodes"
    )
    class_config_id: UUID = Field(description="Foreign key for ObjectProjectionGraphNode.class_config")

    async def create_key(
        self, object_config_graph_binding_class_id: UUID, key: str, position: int | None = None, required: bool = True
    ) -> ObjectProjectionGraphNodeKey:
        """
        Create deterministic ObjectProjectionGraphNodeKey under this ObjectProjectionGraphNode.

        Contract:
        - Parent `object_projection_graph_node_id` is propagated by constructor lowering.
        - NodeKey consumes one `ObjectConfigGraphBindingClass` on top of binding + formula.
        - Identity resolves from `(object_projection_graph_node_id via path,
        object_config_graph_binding_class_id, key)`.
        """

        payload = {
            "object_config_graph_binding_class_id": object_config_graph_binding_class_id,
            "key": key,
            "position": position,
            "required": required,
        }
        result = await invoke_instance(orm_model=self, function_name="create_key", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.projection.object_projection_graph_node_key import ObjectProjectionGraphNodeKey

        if isinstance(value, ObjectProjectionGraphNodeKey):
            return value
        return ObjectProjectionGraphNodeKey.validate_invocation_value(value)

    @classmethod
    async def build_via_object_projection_graph(
        cls,
        object_projection_graph_id: UUID,
        class_config_id: UUID,
        is_root: bool = False,
        required_for_validity: bool = False,
        selection: ObjectProjectionGraphNodeSelection = ObjectProjectionGraphNodeSelection.all,
        top_n: int | None = None,
        selector_condition_id: UUID | None = None,
        policy_refs: list[str] = [],
    ) -> ObjectProjectionGraphNode:
        """
        Create deterministic ObjectProjectionGraphNode under one ObjectProjectionGraph.

        Contract:
        - Parent `object_projection_graph_id` is propagated by constructor lowering.
        - Identity is always OPG-scoped.
        """

        payload = {
            "object_projection_graph_id": object_projection_graph_id,
            "class_config_id": class_config_id,
            "is_root": is_root,
            "required_for_validity": required_for_validity,
            "selection": selection,
            "top_n": top_n,
            "selector_condition_id": selector_condition_id,
            "policy_refs": policy_refs,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_object_projection_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectProjectionGraphNode):
            return value
        return ObjectProjectionGraphNode.validate_invocation_value(value)


class ObjectProjectionGraphNodeCreateKeyInput(BaseModel):
    object_config_graph_binding_class_id: UUID
    key: str
    position: int | None = Field(default=None)
    required: bool = Field(default=True)


class ObjectProjectionGraphNodeCreateKeyOutput(BaseModel):
    value: ObjectProjectionGraphNodeKey


class ObjectProjectionGraphNodeBuildViaObjectProjectionGraphInput(BaseModel):
    object_projection_graph_id: UUID = Field(
        description="Foreign key for ObjectProjectionGraph.object_projection_graph_nodes"
    )
    class_config_id: UUID
    is_root: bool = Field(default=False)
    required_for_validity: bool = Field(default=False)
    selection: ObjectProjectionGraphNodeSelection = Field(default=ObjectProjectionGraphNodeSelection.all)
    top_n: int | None = Field(default=None)
    selector_condition_id: UUID | None = Field(default=None)
    policy_refs: list[str] = Field(default_factory=list)


class ObjectProjectionGraphNodeBuildViaObjectProjectionGraphOutput(BaseModel):
    value: ObjectProjectionGraphNode


FUNCTIONS = {
    "ObjectProjectionGraphNode": {
        "create_key": {
            "canonical": {
                "name": "create_key",
                "description": "Create deterministic ObjectProjectionGraphNodeKey under this ObjectProjectionGraphNode.\n\nContract:\n- Parent `object_projection_graph_node_id` is propagated by constructor lowering.\n- NodeKey consumes one `ObjectConfigGraphBindingClass` on top of binding + formula.\n- Identity resolves from `(object_projection_graph_node_id via path, object_config_graph_binding_class_id, key)`.",
                "is_constructor": False,
            },
            "input": ObjectProjectionGraphNodeCreateKeyInput,
            "output": ObjectProjectionGraphNodeCreateKeyOutput,
        },
        "build_via_object_projection_graph": {
            "canonical": {
                "name": "build_via_object_projection_graph",
                "description": "Create deterministic ObjectProjectionGraphNode under one ObjectProjectionGraph.\n\nContract:\n- Parent `object_projection_graph_id` is propagated by constructor lowering.\n- Identity is always OPG-scoped.",
                "is_constructor": True,
            },
            "input": ObjectProjectionGraphNodeBuildViaObjectProjectionGraphInput,
            "output": ObjectProjectionGraphNodeBuildViaObjectProjectionGraphOutput,
        },
    },
}

__all__ = [
    "ObjectProjectionGraphNode",
    "ObjectProjectionGraphNodeCreateKeyInput",
    "ObjectProjectionGraphNodeCreateKeyOutput",
    "ObjectProjectionGraphNodeBuildViaObjectProjectionGraphInput",
    "ObjectProjectionGraphNodeBuildViaObjectProjectionGraphOutput",
    "FUNCTIONS",
]
