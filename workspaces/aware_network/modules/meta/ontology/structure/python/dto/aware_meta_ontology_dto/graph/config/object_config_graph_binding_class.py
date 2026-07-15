from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config import ClassConfig
    from aware_meta_ontology_dto.class_.class_config_attribute_config import ClassConfigAttributeConfig
    from aware_meta_ontology_dto.graph.config.object_config_graph_binding_formula import ObjectConfigGraphBindingFormula


class ObjectConfigGraphBindingClass(BaseModel):
    """
    One concrete class-level cross-OCG binding anchor.
    Contract:
    - Source may be `Class` or `Class.attr`.
    - Target must terminate at `Class.attr`.
    - ProjectionKey later sits on top of this rail for executable identity resolution.
    """

    # Relationships
    binding_formula: ObjectConfigGraphBindingFormula | None = Field(default=None)
    source_class: ClassConfig | None = Field(default=None)
    source_attr: ClassConfigAttributeConfig | None = Field(default=None)
    target_class: ClassConfig | None = Field(default=None)
    target_attribute: ClassConfigAttributeConfig | None = Field(default=None)

    # Attributes
    name: str
    description: str | None = Field(default=None)
