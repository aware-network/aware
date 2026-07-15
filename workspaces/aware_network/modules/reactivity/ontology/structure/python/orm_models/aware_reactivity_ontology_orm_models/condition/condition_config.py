from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Reactivity Ontology Orm Models
from aware_reactivity_ontology_orm_models.condition.condition_enums import ConditionLogicStrategy

if TYPE_CHECKING:
    from aware_reactivity_ontology_orm_models.condition.condition_config_class_config import ConditionConfigClassConfig


class ConditionConfig(ORMModel):
    # Relationships
    condition_config_class_configs: list[ConditionConfigClassConfig] = Field(default_factory=list)

    # Attributes
    name: str
    description: str
    is_enabled: bool = Field(default=True)
    is_system: bool = Field(default=False)
    logic_strategy: ConditionLogicStrategy = Field(default=ConditionLogicStrategy.all)
