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
    from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
    from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig


class ObjectConfigGraphBindingFormulaSegmentReference(ORMModel):
    """
    Meta-owned reference from one formula placeholder segment to one source class
    attribute config.
    Contract:
    - `content_part_text_segment` identifies the placeholder span inside the
    formula-owned `ContentPartText`.
    - `source_class_config_attribute_config` identifies which source attribute
    the placeholder resolves against.
    - `content` stays generic; binding semantics live here.
    """

    # Relationships
    content_part_text_segment: ContentPartTextSegment
    source_class_config_attribute_config: ClassConfigAttributeConfig

    # Foreign Keys
    object_config_graph_binding_formula_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphBindingFormula.object_config_graph_binding_formula_segment_references"
    )
    content_part_text_segment_id: UUID | None = Field(
        default=None,
        description="Foreign key for ObjectConfigGraphBindingFormulaSegmentReference.content_part_text_segment",
    )
    source_class_config_attribute_config_id: UUID | None = Field(
        default=None,
        description="Foreign key for ObjectConfigGraphBindingFormulaSegmentReference.source_class_config_attribute_config",
    )

    @classmethod
    async def build_via_object_config_graph_binding_formula(
        cls,
        object_config_graph_binding_formula_id: UUID,
        content_part_text_segment_id: UUID,
        source_class_config_attribute_config_id: UUID,
    ) -> ObjectConfigGraphBindingFormulaSegmentReference:
        """
        Build deterministic placeholder/source-attribute reference within an
        ObjectConfigGraphBindingFormula scope.

        Contract:
        - Parent formula scope is propagated via
        `ObjectConfigGraphBindingFormula ->
        ObjectConfigGraphBindingFormulaSegmentReference`.
        - Stable identity resolves from
        `(object_config_graph_binding_formula_id via path,
        content_part_text_segment_id,
        source_class_config_attribute_config_id)`.
        """

        payload = {
            "object_config_graph_binding_formula_id": object_config_graph_binding_formula_id,
            "content_part_text_segment_id": content_part_text_segment_id,
            "source_class_config_attribute_config_id": source_class_config_attribute_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_object_config_graph_binding_formula", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ObjectConfigGraphBindingFormulaSegmentReference):
            return value
        return ObjectConfigGraphBindingFormulaSegmentReference.validate_invocation_value(value)


class ObjectConfigGraphBindingFormulaSegmentReferenceBuildViaObjectConfigGraphBindingFormulaInput(BaseModel):
    object_config_graph_binding_formula_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphBindingFormula.object_config_graph_binding_formula_segment_references"
    )
    content_part_text_segment_id: UUID
    source_class_config_attribute_config_id: UUID


class ObjectConfigGraphBindingFormulaSegmentReferenceBuildViaObjectConfigGraphBindingFormulaOutput(BaseModel):
    value: ObjectConfigGraphBindingFormulaSegmentReference


FUNCTIONS = {
    "ObjectConfigGraphBindingFormulaSegmentReference": {
        "build_via_object_config_graph_binding_formula": {
            "canonical": {
                "name": "build_via_object_config_graph_binding_formula",
                "description": "Build deterministic placeholder/source-attribute reference within an\nObjectConfigGraphBindingFormula scope.\n\nContract:\n- Parent formula scope is propagated via\n`ObjectConfigGraphBindingFormula ->\nObjectConfigGraphBindingFormulaSegmentReference`.\n- Stable identity resolves from\n`(object_config_graph_binding_formula_id via path,\ncontent_part_text_segment_id,\nsource_class_config_attribute_config_id)`.",
                "is_constructor": True,
            },
            "input": ObjectConfigGraphBindingFormulaSegmentReferenceBuildViaObjectConfigGraphBindingFormulaInput,
            "output": ObjectConfigGraphBindingFormulaSegmentReferenceBuildViaObjectConfigGraphBindingFormulaOutput,
        },
    },
}

__all__ = [
    "ObjectConfigGraphBindingFormulaSegmentReference",
    "ObjectConfigGraphBindingFormulaSegmentReferenceBuildViaObjectConfigGraphBindingFormulaInput",
    "ObjectConfigGraphBindingFormulaSegmentReferenceBuildViaObjectConfigGraphBindingFormulaOutput",
    "FUNCTIONS",
]
