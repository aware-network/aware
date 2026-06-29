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


class ClassConfigAttributeConfig(BaseModel):
    # Relationships
    attribute_config: AttributeConfig

    # Attributes
    position: int = Field(default=0)
    is_identity_key: bool = Field(default=False)
