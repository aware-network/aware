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
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
    from aware_meta_ontology.graph.config.object_config_graph_binding_formula import ObjectConfigGraphBindingFormula


class ObjectConfigGraphBindingClass(ORMModel):
    """
    One concrete class-level cross-OCG binding anchor.
    Contract:
    - Source may be `Class` or `Class.attr`.
    - Target must terminate at `Class.attr`.
    - ProjectionKey later sits on top of this rail for executable identity resolution.
    """

    # Relationships
    binding_formula: ObjectConfigGraphBindingFormula | None = Field(default=None)
    source_class: ClassConfig | None = Field(default=None, exclude=True)
    source_attr: ClassConfigAttributeConfig | None = Field(default=None, exclude=True)
    target_class: ClassConfig | None = Field(default=None, exclude=True)
    target_attribute: ClassConfigAttributeConfig | None = Field(default=None, exclude=True)

    # Attributes
    name: str
    description: str | None = Field(default=None)

    # Foreign Keys
    object_config_graph_binding_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphBinding.object_config_graph_binding_classes"
    )
    source_class_id: UUID = Field(description="Foreign key for ObjectConfigGraphBindingClass.source_class")
    source_attr_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphBindingClass.source_attr"
    )
    target_class_id: UUID = Field(description="Foreign key for ObjectConfigGraphBindingClass.target_class")
    target_attribute_id: UUID = Field(description="Foreign key for ObjectConfigGraphBindingClass.target_attribute")

    async def create_formula(
        self, key: str = "default", content_part_text_id: UUID | None = None
    ) -> ObjectConfigGraphBindingFormula:
        """
        Create deterministic formula ownership under this binding-class scope.

        Contract:
        - Parent binding-class scope is propagated by constructor lowering.
        - Formula identity resolves from `(object_config_graph_binding_class_id via path, key)`.
        - `content_part_text_id` may be attached later or during construction.
        """

        payload = {"key": key, "content_part_text_id": content_part_text_id}
        result = await invoke_instance(orm_model=self, function_name="create_formula", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.config.object_config_graph_binding_formula import ObjectConfigGraphBindingFormula

        if isinstance(value, ObjectConfigGraphBindingFormula):
            return value
        return ObjectConfigGraphBindingFormula.validate_invocation_value(value)

    @classmethod
    async def build_via_object_config_graph_binding(
        cls,
        object_config_graph_binding_id: UUID,
        name: str,
        source_class_id: UUID,
        target_class_id: UUID,
        target_attribute_id: UUID,
        source_attr_id: UUID | None = None,
    ) -> ObjectConfigGraphBindingClass:
        """
        Build deterministic ObjectConfigGraphBindingClass within an ObjectConfigGraphBinding scope.

        Contract:
        - Parent binding scope is propagated via `ObjectConfigGraphBinding ->
        ObjectConfigGraphBindingClass`.
        - Stable identity resolves from `(object_config_graph_binding_id via path, source_class_id,
        target_class_id, target_attribute_id)`.
        - `source_attr_id` is optional and does not participate in v0 stable identity.
        """

        payload = {
            "object_config_graph_binding_id": object_config_graph_binding_id,
            "name": name,
            "source_class_id": source_class_id,
            "target_class_id": target_class_id,
            "target_attribute_id": target_attribute_id,
            "source_attr_id": source_attr_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_object_config_graph_binding", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectConfigGraphBindingClass):
            return value
        return ObjectConfigGraphBindingClass.validate_invocation_value(value)


class ObjectConfigGraphBindingClassCreateFormulaInput(BaseModel):
    key: str = Field(default="default")
    content_part_text_id: UUID | None = Field(default=None)


class ObjectConfigGraphBindingClassCreateFormulaOutput(BaseModel):
    value: ObjectConfigGraphBindingFormula


class ObjectConfigGraphBindingClassBuildViaObjectConfigGraphBindingInput(BaseModel):
    object_config_graph_binding_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphBinding.object_config_graph_binding_classes"
    )
    name: str
    source_class_id: UUID
    target_class_id: UUID
    target_attribute_id: UUID
    source_attr_id: UUID | None = Field(default=None)


class ObjectConfigGraphBindingClassBuildViaObjectConfigGraphBindingOutput(BaseModel):
    value: ObjectConfigGraphBindingClass


FUNCTIONS = {
    "ObjectConfigGraphBindingClass": {
        "create_formula": {
            "canonical": {
                "name": "create_formula",
                "description": "Create deterministic formula ownership under this binding-class scope.\n\nContract:\n- Parent binding-class scope is propagated by constructor lowering.\n- Formula identity resolves from `(object_config_graph_binding_class_id via path, key)`.\n- `content_part_text_id` may be attached later or during construction.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphBindingClassCreateFormulaInput,
            "output": ObjectConfigGraphBindingClassCreateFormulaOutput,
        },
        "build_via_object_config_graph_binding": {
            "canonical": {
                "name": "build_via_object_config_graph_binding",
                "description": "Build deterministic ObjectConfigGraphBindingClass within an ObjectConfigGraphBinding scope.\n\nContract:\n- Parent binding scope is propagated via `ObjectConfigGraphBinding -> ObjectConfigGraphBindingClass`.\n- Stable identity resolves from `(object_config_graph_binding_id via path, source_class_id, target_class_id, target_attribute_id)`.\n- `source_attr_id` is optional and does not participate in v0 stable identity.",
                "is_constructor": True,
            },
            "input": ObjectConfigGraphBindingClassBuildViaObjectConfigGraphBindingInput,
            "output": ObjectConfigGraphBindingClassBuildViaObjectConfigGraphBindingOutput,
        },
    },
}

__all__ = [
    "ObjectConfigGraphBindingClass",
    "ObjectConfigGraphBindingClassCreateFormulaInput",
    "ObjectConfigGraphBindingClassCreateFormulaOutput",
    "ObjectConfigGraphBindingClassBuildViaObjectConfigGraphBindingInput",
    "ObjectConfigGraphBindingClassBuildViaObjectConfigGraphBindingOutput",
    "FUNCTIONS",
]
