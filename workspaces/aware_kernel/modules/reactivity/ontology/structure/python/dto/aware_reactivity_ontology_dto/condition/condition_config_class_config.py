from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Ontology Dto
from aware_reactivity_ontology_dto.condition.condition_enums import (
    ClassSelectionMode,
    ConditionLogicStrategy,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.class_.class_config import ClassConfig
    from aware_reactivity_ontology_dto.condition.condition_config_attribute_config import ConditionConfigAttributeConfig


class ConditionConfigClassConfig(BaseModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None)
    condition_config_attribute_configs: list[ConditionConfigAttributeConfig] = Field(default_factory=list)

    # Attributes
    class_logic: ConditionLogicStrategy = Field(default=ConditionLogicStrategy.all)
    class_selection: ClassSelectionMode = Field(default=ClassSelectionMode.base_class)
    require_existence: bool = Field(default=True)
