from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_content_ontology_dto.part.content_part_text import ContentPartText
    from aware_meta_ontology_dto.graph.config.object_config_graph_binding_formula_segment_reference import (
        ObjectConfigGraphBindingFormulaSegmentReference,
    )


class ObjectConfigGraphBindingFormula(BaseModel):
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
