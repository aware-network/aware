from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_config import AttributeConfig


class ClassConfigAttributeConfig(ORMModel):
    # Relationships
    attribute_config: AttributeConfig

    # Attributes
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)

    # Foreign Keys
    class_config_id: UUID = Field(description="Foreign key for ClassConfig.class_config_attribute_configs")
    attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for ClassConfigAttributeConfig.attribute_config"
    )
