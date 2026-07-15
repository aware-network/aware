from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Reactivity Ontology Orm Models
from aware_reactivity_ontology_orm_models.condition.condition_enums import (
    ClassSelectionMode,
    ConditionLogicStrategy,
)

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig
    from aware_reactivity_ontology_orm_models.condition.condition_config_attribute_config import (
        ConditionConfigAttributeConfig,
    )


class ConditionConfigClassConfig(ORMModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)
    condition_config_attribute_configs: list[ConditionConfigAttributeConfig] = Field(default_factory=list)

    # Attributes
    class_logic: ConditionLogicStrategy = Field(default=ConditionLogicStrategy.all)
    class_selection: ClassSelectionMode = Field(default=ClassSelectionMode.base_class)
    require_existence: bool = Field(default=True)

    # Foreign Keys
    condition_config_id: UUID = Field(description="Foreign key for ConditionConfig.condition_config_class_configs")
    class_config_id: UUID = Field(description="Foreign key for ConditionConfigClassConfig.class_config")
