from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Experience Ontology Orm Models
from aware_experience_ontology_orm_models.program.program_enums import ProgramAttributeType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_config import AttributeConfig


class ProgramConfigAttributeConfig(ORMModel):
    """
    Program-level typed attribute contract edge.
    Contract:
    - Declares canonical program I/O schema via AttributeConfig references.
    - Type is explicit (`input` / `output`) for future parity with function schema rails.
    """

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)

    # Attributes
    position: int | None = Field(default=None)
    required: bool = Field(default=True)
    type: ProgramAttributeType = Field(default=ProgramAttributeType.input)

    # Foreign Keys
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.attribute_configs")
    attribute_config_id: UUID = Field(description="Foreign key for ProgramConfigAttributeConfig.attribute_config")
