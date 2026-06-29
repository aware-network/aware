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
    from aware_meta_ontology.attribute.attribute import Attribute
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_meta_ontology.class_.class_instance_attribute import ClassInstanceAttribute
    from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange


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

    async def create_attribute(
        self, attribute_config_id: UUID, value_root_id: UUID | None = None
    ) -> ClassInstanceAttribute:
        """
        Create deterministic Attribute membership under this ClassInstance.

        Contract:
        - ClassInstance owns membership and topology only.
        - Attribute identity resolves from `(source_object_id, attribute_config_id)` via shared owner key.
        """

        payload = {"attribute_config_id": attribute_config_id, "value_root_id": value_root_id}
        result = await invoke_instance(orm_model=self, function_name="create_attribute", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.class_.class_instance_attribute import ClassInstanceAttribute

        if isinstance(value, ClassInstanceAttribute):
            return value
        return ClassInstanceAttribute.validate_invocation_value(value)

    @classmethod
    async def create_via_object_instance_graph(
        cls, object_instance_graph_id: UUID, class_config_id: UUID, source_object_id: UUID
    ) -> ClassInstance:
        """
        Create deterministic ClassInstance under one ObjectInstanceGraph scope.

        Contract:
        - Parent `object_instance_graph_id` is propagated by constructor lowering.
        - Identity resolves from `(object_instance_graph_id via path, class_config_id, source_object_id)`.
        - `source_object_id` is the semantic source-object/worldline anchor, not a synthesized FK.
        """

        payload = {
            "object_instance_graph_id": object_instance_graph_id,
            "class_config_id": class_config_id,
            "source_object_id": source_object_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_object_instance_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ClassInstance):
            return value
        return ClassInstance.validate_invocation_value(value)


class ClassInstanceCreateAttributeInput(BaseModel):
    attribute_config_id: UUID
    value_root_id: UUID | None = Field(default=None)


class ClassInstanceCreateAttributeOutput(BaseModel):
    value: ClassInstanceAttribute


class ClassInstanceCreateViaObjectInstanceGraphInput(BaseModel):
    object_instance_graph_id: UUID = Field(description="Foreign key for ObjectInstanceGraph.class_instances")
    class_config_id: UUID
    source_object_id: UUID


class ClassInstanceCreateViaObjectInstanceGraphOutput(BaseModel):
    value: ClassInstance


FUNCTIONS = {
    "ClassInstance": {
        "create_attribute": {
            "canonical": {
                "name": "create_attribute",
                "description": "Create deterministic Attribute membership under this ClassInstance.\n\nContract:\n- ClassInstance owns membership and topology only.\n- Attribute identity resolves from `(source_object_id, attribute_config_id)` via shared owner key.",
                "is_constructor": False,
            },
            "input": ClassInstanceCreateAttributeInput,
            "output": ClassInstanceCreateAttributeOutput,
        },
        "create_via_object_instance_graph": {
            "canonical": {
                "name": "create_via_object_instance_graph",
                "description": "Create deterministic ClassInstance under one ObjectInstanceGraph scope.\n\nContract:\n- Parent `object_instance_graph_id` is propagated by constructor lowering.\n- Identity resolves from `(object_instance_graph_id via path, class_config_id, source_object_id)`.\n- `source_object_id` is the semantic source-object/worldline anchor, not a synthesized FK.",
                "is_constructor": True,
            },
            "input": ClassInstanceCreateViaObjectInstanceGraphInput,
            "output": ClassInstanceCreateViaObjectInstanceGraphOutput,
        },
    },
}

__all__ = [
    "ClassInstance",
    "ClassInstanceCreateAttributeInput",
    "ClassInstanceCreateAttributeOutput",
    "ClassInstanceCreateViaObjectInstanceGraphInput",
    "ClassInstanceCreateViaObjectInstanceGraphOutput",
    "FUNCTIONS",
]
