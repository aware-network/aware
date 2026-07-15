from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.part.content_part_text import ContentPartText
    from aware_meta_ontology_orm_models.graph.config.object_config_graph_binding_formula_segment_reference import (
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
