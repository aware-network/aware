from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import Json

if TYPE_CHECKING:
    from aware_meta_ontology_dto.primitive.primitive_change import PrimitiveChange
    from aware_meta_ontology_dto.primitive.primitive_config import PrimitiveConfig


class Primitive(BaseModel):
    # Relationships
    primitive_changes: list[PrimitiveChange] = Field(default_factory=list)
    primitive_config: PrimitiveConfig | None = Field(default=None)

    # Attributes
    value: Json
