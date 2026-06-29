from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Ontology Dto
from aware_reactivity_ontology_dto.condition.condition_enums import ConditionOperator

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig
    from aware_reactivity_ontology_dto.condition.condition_config_enum_config import ConditionConfigEnumConfig
    from aware_reactivity_ontology_dto.condition.condition_config_primitive_config import ConditionConfigPrimitiveConfig
    from aware_reactivity_ontology_dto.condition.condition_config_relationship_config import (
        ConditionConfigRelationshipConfig,
    )


class ConditionConfigAttributeConfig(BaseModel):
    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None)
    condition_config_enum_config: ConditionConfigEnumConfig | None = Field(default=None)
    condition_config_primitive_config: ConditionConfigPrimitiveConfig | None = Field(default=None)
    condition_config_relationship_config: ConditionConfigRelationshipConfig | None = Field(default=None)

    # Attributes
    operator: ConditionOperator
    negate: bool = Field(default=False)
