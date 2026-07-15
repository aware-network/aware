from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Reactivity Ontology Orm Models
from aware_reactivity_ontology_orm_models.condition.condition_enums import EnumMatchMode

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.enum.enum_config import EnumConfig
    from aware_reactivity_ontology_orm_models.condition.condition_config_enum_option import ConditionConfigEnumOption


class ConditionConfigEnumConfig(ORMModel):
    # Relationships
    condition_config_enum_options: list[ConditionConfigEnumOption] = Field(default_factory=list)
    enum_config: EnumConfig | None = Field(default=None, exclude=True)

    # Attributes
    match_mode: EnumMatchMode = Field(default=EnumMatchMode.any_of)

    # Foreign Keys
    condition_config_attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for ConditionConfigAttributeConfig.condition_config_enum_config"
    )
    enum_config_id: UUID = Field(description="Foreign key for ConditionConfigEnumConfig.enum_config")
