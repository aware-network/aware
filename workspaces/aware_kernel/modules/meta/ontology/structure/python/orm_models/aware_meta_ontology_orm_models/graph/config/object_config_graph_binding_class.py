from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig
    from aware_meta_ontology_orm_models.class_.class_config_attribute_config import ClassConfigAttributeConfig
    from aware_meta_ontology_orm_models.graph.config.object_config_graph_binding_formula import (
        ObjectConfigGraphBindingFormula,
    )


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
