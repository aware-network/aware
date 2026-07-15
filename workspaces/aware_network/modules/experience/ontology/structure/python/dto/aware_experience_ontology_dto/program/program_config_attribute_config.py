from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology Dto
from aware_experience_ontology_dto.program.program_enums import ProgramAttributeType

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig


class ProgramConfigAttributeConfig(BaseModel):
    """
    Program-level typed attribute contract edge.
    Contract:
    - Declares canonical program I/O schema via AttributeConfig references.
    - Type is explicit (`input` / `output`) for future parity with function schema rails.
    """

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None)

    # Attributes
    position: int | None = Field(default=None)
    required: bool = Field(default=True)
    type: ProgramAttributeType = Field(default=ProgramAttributeType.input)
