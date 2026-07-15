from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_config_input_config_attribute_config import (
        ProgramConfigInputConfigAttributeConfig,
    )


class ProgramConfigInputConfig(BaseModel):
    """
    Declarative program input configuration unit under a ProgramConfig.
    Contract:
    - Declares runtime-injected symbols.
    - Pure config (no runtime effects).
    """

    # Relationships
    attribute_configs: list[ProgramConfigInputConfigAttributeConfig] = Field(default_factory=list)

    # Attributes
    name: str
    source: str
    required: bool = Field(default=True)
    default_expr: JsonObject | None = Field(default=None)
