from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config_attribute_config import (
        ProgramConfigAttributeConfig,
    )
    from aware_meta_ontology_orm_models.attribute.attribute import Attribute


class ProgramAttribute(ORMModel):
    # Relationships
    config: ProgramConfigAttributeConfig | None = Field(default=None, exclude=True)
    attribute: Attribute | None = Field(default=None, exclude=True)

    # Foreign Keys
    program_id: UUID = Field(description="Foreign key for Program.attributes")
    config_id: UUID = Field(description="Foreign key for ProgramAttribute.config")
    attribute_id: UUID = Field(description="Foreign key for ProgramAttribute.attribute")
