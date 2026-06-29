from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import BaseModel

if TYPE_CHECKING:
    from aware_content_ontology_dto.part.content_part_text_segment import ContentPartTextSegment
    from aware_meta_ontology_dto.class_.class_config_attribute_config import ClassConfigAttributeConfig


class ObjectConfigGraphBindingFormulaSegmentReference(BaseModel):
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
