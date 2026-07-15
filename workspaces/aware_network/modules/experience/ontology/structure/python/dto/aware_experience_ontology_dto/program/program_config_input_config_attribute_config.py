from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig


class ProgramConfigInputConfigAttributeConfig(BaseModel):
    """
    Signature slot for ProgramConfigInputConfig.
    Contract:
    - Keeps input signatures explicit via AttributeConfig references.
    - Association identity is deterministic from `(input_config_id, attribute_config_id)`.
    """

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None)

    # Attributes
    position: int | None = Field(default=None)
