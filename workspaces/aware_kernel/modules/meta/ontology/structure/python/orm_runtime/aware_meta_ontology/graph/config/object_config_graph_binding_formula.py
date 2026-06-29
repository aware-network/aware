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
    from aware_content_ontology.part.content_part_text import ContentPartText
    from aware_meta_ontology.graph.config.object_config_graph_binding_formula_segment_reference import (
        ObjectConfigGraphBindingFormulaSegmentReference,
    )


class ObjectConfigGraphBindingFormula(ORMModel):
    """
    Deterministic encode substrate for one binding-class anchor.
    Contract:
    - Formula stays directional and encodes one source class instance into the
    target attribute owned by the parent `ObjectConfigGraphBindingClass`.
    - `ContentPartText` stores canonical authored template text.
    - Placeholder semantics remain Meta-owned through
    `ObjectConfigGraphBindingFormulaSegmentReference`.
    """

    # Relationships
    content_part_text: ContentPartText | None = Field(default=None)
    object_config_graph_binding_formula_segment_references: list[ObjectConfigGraphBindingFormulaSegmentReference] = (
        Field(default_factory=list)
    )

    # Attributes
    key: str = Field(default="default")

    # Foreign Keys
    object_config_graph_binding_class_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphBindingClass.binding_formula"
    )
    content_part_text_id: UUID | None = Field(
        default=None, description="Foreign key for ObjectConfigGraphBindingFormula.content_part_text"
    )

    async def create_segment_reference(
        self, content_part_text_segment_id: UUID, source_class_config_attribute_config_id: UUID
    ) -> ObjectConfigGraphBindingFormulaSegmentReference:
        """
        Create deterministic placeholder/source-attribute reference within this
        formula scope.

        Contract:
        - Placeholder semantics stay in Meta; `content` remains generic.
        - The referenced segment must belong to this formula's `content_part_text`.
        - Stable identity resolves from formula scope plus the referenced segment
        and source class attribute config.
        """

        payload = {
            "content_part_text_segment_id": content_part_text_segment_id,
            "source_class_config_attribute_config_id": source_class_config_attribute_config_id,
        }
        result = await invoke_instance(orm_model=self, function_name="create_segment_reference", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.graph.config.object_config_graph_binding_formula_segment_reference import (
            ObjectConfigGraphBindingFormulaSegmentReference,
        )

        if isinstance(value, ObjectConfigGraphBindingFormulaSegmentReference):
            return value
        return ObjectConfigGraphBindingFormulaSegmentReference.validate_invocation_value(value)

    @classmethod
    async def build_via_object_config_graph_binding_class(
        cls, object_config_graph_binding_class_id: UUID, key: str = "default", content_part_text_id: UUID | None = None
    ) -> ObjectConfigGraphBindingFormula:
        """
        Build deterministic ObjectConfigGraphBindingFormula within an
        ObjectConfigGraphBindingClass scope.

        Contract:
        - Parent binding-class scope is propagated via
        `ObjectConfigGraphBindingClass -> ObjectConfigGraphBindingFormula`.
        - Stable identity resolves from
        `(object_config_graph_binding_class_id via path, key)`.
        - `content_part_text_id` may be set during construction or later.
        """

        payload = {
            "object_config_graph_binding_class_id": object_config_graph_binding_class_id,
            "key": key,
            "content_part_text_id": content_part_text_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_object_config_graph_binding_class", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectConfigGraphBindingFormula):
            return value
        return ObjectConfigGraphBindingFormula.validate_invocation_value(value)


class ObjectConfigGraphBindingFormulaCreateSegmentReferenceInput(BaseModel):
    content_part_text_segment_id: UUID
    source_class_config_attribute_config_id: UUID


class ObjectConfigGraphBindingFormulaCreateSegmentReferenceOutput(BaseModel):
    value: ObjectConfigGraphBindingFormulaSegmentReference


class ObjectConfigGraphBindingFormulaBuildViaObjectConfigGraphBindingClassInput(BaseModel):
    object_config_graph_binding_class_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphBindingClass.binding_formula"
    )
    key: str = Field(default="default")
    content_part_text_id: UUID | None = Field(default=None)


class ObjectConfigGraphBindingFormulaBuildViaObjectConfigGraphBindingClassOutput(BaseModel):
    value: ObjectConfigGraphBindingFormula


FUNCTIONS = {
    "ObjectConfigGraphBindingFormula": {
        "create_segment_reference": {
            "canonical": {
                "name": "create_segment_reference",
                "description": "Create deterministic placeholder/source-attribute reference within this\nformula scope.\n\nContract:\n- Placeholder semantics stay in Meta; `content` remains generic.\n- The referenced segment must belong to this formula's `content_part_text`.\n- Stable identity resolves from formula scope plus the referenced segment\nand source class attribute config.",
                "is_constructor": False,
            },
            "input": ObjectConfigGraphBindingFormulaCreateSegmentReferenceInput,
            "output": ObjectConfigGraphBindingFormulaCreateSegmentReferenceOutput,
        },
        "build_via_object_config_graph_binding_class": {
            "canonical": {
                "name": "build_via_object_config_graph_binding_class",
                "description": "Build deterministic ObjectConfigGraphBindingFormula within an\nObjectConfigGraphBindingClass scope.\n\nContract:\n- Parent binding-class scope is propagated via\n`ObjectConfigGraphBindingClass -> ObjectConfigGraphBindingFormula`.\n- Stable identity resolves from\n`(object_config_graph_binding_class_id via path, key)`.\n- `content_part_text_id` may be set during construction or later.",
                "is_constructor": True,
            },
            "input": ObjectConfigGraphBindingFormulaBuildViaObjectConfigGraphBindingClassInput,
            "output": ObjectConfigGraphBindingFormulaBuildViaObjectConfigGraphBindingClassOutput,
        },
    },
}

__all__ = [
    "ObjectConfigGraphBindingFormula",
    "ObjectConfigGraphBindingFormulaCreateSegmentReferenceInput",
    "ObjectConfigGraphBindingFormulaCreateSegmentReferenceOutput",
    "ObjectConfigGraphBindingFormulaBuildViaObjectConfigGraphBindingClassInput",
    "ObjectConfigGraphBindingFormulaBuildViaObjectConfigGraphBindingClassOutput",
    "FUNCTIONS",
]
