from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Ontology Dto
from aware_reactivity_ontology_dto.condition.condition_enums import ConditionLogicStrategy

if TYPE_CHECKING:
    from aware_reactivity_ontology_dto.condition.condition_config_class_config import ConditionConfigClassConfig


class ConditionConfig(BaseModel):
    # Relationships
    condition_config_class_configs: list[ConditionConfigClassConfig] = Field(default_factory=list)

    # Attributes
    name: str
    description: str
    is_enabled: bool = Field(default=True)
    is_system: bool = Field(default=False)
    logic_strategy: ConditionLogicStrategy = Field(default=ConditionLogicStrategy.all)
