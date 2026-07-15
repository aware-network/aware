from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Reactivity Ontology Orm Models
from aware_reactivity_ontology_orm_models.condition.condition_enums import ConditionOperator

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_config import AttributeConfig
    from aware_reactivity_ontology_orm_models.condition.condition_config_enum_config import ConditionConfigEnumConfig
    from aware_reactivity_ontology_orm_models.condition.condition_config_primitive_config import (
        ConditionConfigPrimitiveConfig,
    )
    from aware_reactivity_ontology_orm_models.condition.condition_config_relationship_config import (
        ConditionConfigRelationshipConfig,
    )


class ConditionConfigAttributeConfig(ORMModel):
    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)
    condition_config_enum_config: ConditionConfigEnumConfig | None = Field(default=None)
    condition_config_primitive_config: ConditionConfigPrimitiveConfig | None = Field(default=None)
    condition_config_relationship_config: ConditionConfigRelationshipConfig | None = Field(default=None)

    # Attributes
    operator: ConditionOperator
    negate: bool = Field(default=False)

    # Foreign Keys
    condition_config_class_config_id: UUID = Field(
        description="Foreign key for ConditionConfigClassConfig.condition_config_attribute_configs"
    )
    attribute_config_id: UUID = Field(description="Foreign key for ConditionConfigAttributeConfig.attribute_config")
