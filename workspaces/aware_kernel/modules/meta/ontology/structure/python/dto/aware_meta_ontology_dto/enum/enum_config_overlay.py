from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.enum.enum_config import EnumConfig


class EnumConfigOverlay(BaseModel):
    """Per-language overrides for EnumConfig entities"""

    # Relationships
    enum_config: EnumConfig | None = Field(default=None, description="Association target reference to EnumConfig")

    # Attributes
    rendered_name: str | None = Field(default=None)
