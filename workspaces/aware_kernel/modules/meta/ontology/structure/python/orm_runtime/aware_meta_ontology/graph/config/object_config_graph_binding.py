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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology.graph.config.object_config_graph_binding_class import ObjectConfigGraphBindingClass


class ObjectConfigGraphBinding(ORMModel):
    """
    Entry linking one source ObjectConfigGraph scope to one target ObjectConfigGraph
    through cross-layer zoom/binding semantics.
    """

    # Relationships
    target_object_config_graph: ObjectConfigGraph | None = Field(
        default=None, description="Target OCG for this binding. Source OCG scope is propagated by parent containment."
    )
    object_config_graph_binding_classes: list[ObjectConfigGraphBindingClass] = Field(default_factory=list)

    # Foreign Keys
    object_config_graph_id: UUID = Field(description="Foreign key for ObjectConfigGraph.object_config_graph_bindings")
    target_object_config_graph_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphBinding.target_object_config_graph"
    )

    async def create_class(
        self,
        name: str,
        source_class_id: UUID,
        target_class_id: UUID,
        target_attribute_id: UUID,
        source_attr_id: UUID | None = None,
    ) -> ObjectConfigGraphBindingClass:
        """
        Create deterministic ObjectConfigGraphBindingClass under this binding.

        Contract:
        - Parent binding scope is propagated by constructor lowering.
        - `source_attr_id` is optional at the binding layer and does not widen source-scope identity.
        - `target_attribute_id` is required as the target anchor.
        """

        payload = {
            "name": name,
            "source_class_id": source_class_id,
            "target_class_id": target_class_id,
            "target_attribute_id": target_attribute_id,
            "source_attr_id": source_attr_id,
        }
        result = await invoke_instance(orm_model=self, function_name="create_class", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.config.object_config_graph_binding_class import ObjectConfigGraphBindingClass

        if isinstance(value, ObjectConfigGraphBindingClass):
            return value
        return ObjectConfigGraphBindingClass.validate_invocation_value(value)

    @classmethod
    async def build_via_object_config_graph(
        cls, object_config_graph_id: UUID, target_object_config_graph_id: UUID
    ) -> ObjectConfigGraphBinding:
        """
        Build deterministic ObjectConfigGraphBinding within an ObjectConfigGraph scope.

        Contract:
        - Source OCG scope is propagated via `ObjectConfigGraph -> ObjectConfigGraphBinding`.
        - Binding identity resolves from `(object_config_graph_id via path, target_object_config_graph_id)`.
        """

        payload = {
            "object_config_graph_id": object_config_graph_id,
            "target_object_config_graph_id": target_object_config_graph_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_object_config_graph", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectConfigGraphBinding):
            return value
        return ObjectConfigGraphBinding.validate_invocation_value(value)


class ObjectConfigGraphBindingCreateClassInput(BaseModel):
    name: str
    source_class_id: UUID
    target_class_id: UUID
    target_attribute_id: UUID
    source_attr_id: UUID | None = Field(default=None)


class ObjectConfigGraphBindingCreateClassOutput(BaseModel):
    value: ObjectConfigGraphBindingClass


class ObjectConfigGraphBindingBuildViaObjectConfigGraphInput(BaseModel):
    object_config_graph_id: UUID = Field(description="Foreign key for ObjectConfigGraph.object_config_graph_bindings")
    target_object_config_graph_id: UUID


class ObjectConfigGraphBindingBuildViaObjectConfigGraphOutput(BaseModel):
    value: ObjectConfigGraphBinding


FUNCTIONS = {
    "ObjectConfigGraphBinding": {
        "create_class": {
            "canonical": {
                "name": "create_class",
                "description": "Create deterministic ObjectConfigGraphBindingClass under this binding.\n\nContract:\n- Parent binding scope is propagated by constructor lowering.\n- `source_attr_id` is optional at the binding layer and does not widen source-scope identity.\n- `target_attribute_id` is required as the target anchor.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphBindingCreateClassInput,
            "output": ObjectConfigGraphBindingCreateClassOutput,
        },
        "build_via_object_config_graph": {
            "canonical": {
                "name": "build_via_object_config_graph",
                "description": "Build deterministic ObjectConfigGraphBinding within an ObjectConfigGraph scope.\n\nContract:\n- Source OCG scope is propagated via `ObjectConfigGraph -> ObjectConfigGraphBinding`.\n- Binding identity resolves from `(object_config_graph_id via path, target_object_config_graph_id)`.",
                "is_constructor": True,
            },
            "input": ObjectConfigGraphBindingBuildViaObjectConfigGraphInput,
            "output": ObjectConfigGraphBindingBuildViaObjectConfigGraphOutput,
        },
    },
}

__all__ = [
    "ObjectConfigGraphBinding",
    "ObjectConfigGraphBindingCreateClassInput",
    "ObjectConfigGraphBindingCreateClassOutput",
    "ObjectConfigGraphBindingBuildViaObjectConfigGraphInput",
    "ObjectConfigGraphBindingBuildViaObjectConfigGraphOutput",
    "FUNCTIONS",
]
