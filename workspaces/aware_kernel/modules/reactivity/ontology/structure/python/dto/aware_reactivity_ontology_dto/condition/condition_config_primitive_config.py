from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.primitive.primitive_config import PrimitiveConfig


class ConditionConfigPrimitiveConfig(BaseModel):
    # Relationships
    primitive_config: PrimitiveConfig | None = Field(default=None)

    # Attributes
    primitive_value: str
    range_max: str | None = Field(default=None)
    range_min: str | None = Field(default=None)
