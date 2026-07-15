from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.primitive.primitive_config import PrimitiveConfig


class ConditionConfigPrimitiveConfig(ORMModel):
    # Relationships
    primitive_config: PrimitiveConfig | None = Field(default=None, exclude=True)

    # Attributes
    primitive_value: str
    range_max: str | None = Field(default=None)
    range_min: str | None = Field(default=None)

    # Foreign Keys
    condition_config_attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for ConditionConfigAttributeConfig.condition_config_primitive_config"
    )
    primitive_config_id: UUID = Field(description="Foreign key for ConditionConfigPrimitiveConfig.primitive_config")
