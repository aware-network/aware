from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config_input_config_attribute_config import (
        ProgramConfigInputConfigAttributeConfig,
    )


class ProgramConfigInputConfig(ORMModel):
    """
    Declarative program input configuration unit under a ProgramConfig.
    Contract:
    - Declares runtime-injected symbols.
    - Pure config (no runtime effects).
    """

    # Relationships
    attribute_configs: list[ProgramConfigInputConfigAttributeConfig] = Field(default_factory=list, exclude=True)

    # Attributes
    name: str
    source: str
    required: bool = Field(default=True)
    default_expr: JsonObject | None = Field(default=None)

    # Foreign Keys
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.input_configs")
