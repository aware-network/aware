from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_config_input_config_attribute_config import (
        ProgramConfigInputConfigAttributeConfig,
    )
    from aware_meta_ontology_dto.attribute.attribute import Attribute


class ProgramInputAttribute(BaseModel):
    # Relationships
    config: ProgramConfigInputConfigAttributeConfig | None = Field(default=None)
    attribute: Attribute | None = Field(default=None)
