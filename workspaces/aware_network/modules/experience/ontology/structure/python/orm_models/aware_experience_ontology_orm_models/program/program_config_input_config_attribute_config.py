from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_config import AttributeConfig


class ProgramConfigInputConfigAttributeConfig(ORMModel):
    """
    Signature slot for ProgramConfigInputConfig.
    Contract:
    - Keeps input signatures explicit via AttributeConfig references.
    - Association identity is deterministic from `(input_config_id, attribute_config_id)`.
    """

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)

    # Attributes
    position: int | None = Field(default=None)

    # Foreign Keys
    program_config_input_config_id: UUID = Field(
        description="Foreign key for ProgramConfigInputConfig.attribute_configs"
    )
    attribute_config_id: UUID = Field(
        description="Foreign key for ProgramConfigInputConfigAttributeConfig.attribute_config"
    )
