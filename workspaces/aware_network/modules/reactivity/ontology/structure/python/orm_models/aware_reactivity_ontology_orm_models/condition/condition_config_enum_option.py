from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.enum.enum_option import EnumOption


class ConditionConfigEnumOption(ORMModel):
    # Relationships
    enum_option: EnumOption | None = Field(default=None, exclude=True)

    # Foreign Keys
    condition_config_enum_config_id: UUID = Field(
        description="Foreign key for ConditionConfigEnumConfig.condition_config_enum_options"
    )
    enum_option_id: UUID = Field(description="Foreign key for ConditionConfigEnumOption.enum_option")
