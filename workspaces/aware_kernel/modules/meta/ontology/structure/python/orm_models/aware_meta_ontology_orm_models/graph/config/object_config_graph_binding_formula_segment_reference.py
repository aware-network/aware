from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.part.content_part_text_segment import ContentPartTextSegment
    from aware_meta_ontology_orm_models.class_.class_config_attribute_config import ClassConfigAttributeConfig


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
