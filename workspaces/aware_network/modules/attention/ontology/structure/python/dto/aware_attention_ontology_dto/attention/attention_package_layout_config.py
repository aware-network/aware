from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.layout.layout_config import LayoutConfig


class AttentionPackageLayoutConfig(BaseModel):
    # Relationships
    layout_config: LayoutConfig | None = Field(default=None)
