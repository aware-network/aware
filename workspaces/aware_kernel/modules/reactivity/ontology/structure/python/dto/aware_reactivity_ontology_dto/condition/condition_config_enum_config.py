from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Reactivity Ontology Dto
from aware_reactivity_ontology_dto.condition.condition_enums import EnumMatchMode

if TYPE_CHECKING:
    from aware_meta_ontology_dto.enum.enum_config import EnumConfig
    from aware_reactivity_ontology_dto.condition.condition_config_enum_option import ConditionConfigEnumOption


class ConditionConfigEnumConfig(BaseModel):
    # Relationships
    condition_config_enum_options: list[ConditionConfigEnumOption] = Field(default_factory=list)
    enum_config: EnumConfig | None = Field(default=None)

    # Attributes
    match_mode: EnumMatchMode = Field(default=EnumMatchMode.any_of)
