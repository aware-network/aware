from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_change import AttributeChange
    from aware_meta_ontology_orm_models.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology_orm_models.attribute.attribute_value import AttributeValue


class Attribute(ORMModel):
    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)
    attribute_changes: list[AttributeChange] = Field(default_factory=list, exclude=True)
    value_root: AttributeValue = Field(description="Canonical value representation (descriptor-driven value tree).")

    # Attributes
    owner_key: UUID = Field(description="Stable owner anchor for shared contained structural Attribute identity.")

    # Foreign Keys
    attribute_config_id: UUID = Field(description="Foreign key for Attribute.attribute_config")
    value_root_id: UUID | None = Field(default=None, description="Foreign key for Attribute.value_root")
