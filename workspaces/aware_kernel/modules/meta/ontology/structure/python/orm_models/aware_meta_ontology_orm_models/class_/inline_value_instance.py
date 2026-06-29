from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute import Attribute
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig
    from aware_meta_ontology_orm_models.class_.inline_value_instance_attribute import InlineValueInstanceAttribute


class InlineValueInstance(ORMModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)

    # Attributes
    owner_key: UUID = Field(
        description="Stable owner anchor for this value-world instance within one enclosing payload tree."
    )

    # Foreign Keys
    class_config_id: UUID = Field(description="Foreign key for InlineValueInstance.class_config")

    # Edges
    inline_value_instance_attributes: list[InlineValueInstanceAttribute] = Field(
        default_factory=list, description="Edge association helper for attributes"
    )

    @property
    def attributes(self) -> list[Attribute]:
        return [edge.attribute for edge in self.inline_value_instance_attributes if edge.attribute is not None]
