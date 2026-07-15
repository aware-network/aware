from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.enum.enum_option import EnumOption


class EnumOptionOverlay(BaseModel):
    """Per-language overrides for EnumOption entities"""

    # Relationships
    enum_option: EnumOption | None = Field(default=None, description="Association target reference to EnumOption")

    # Attributes
    rendered_name: str | None = Field(default=None)
    wire_name: str | None = Field(default=None)
