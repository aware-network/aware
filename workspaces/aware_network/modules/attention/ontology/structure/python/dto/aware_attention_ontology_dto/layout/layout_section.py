from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.section.section import Section


class LayoutSection(BaseModel):
    """Canonical section geometry/visibility entry inside a Layout."""

    # Relationships
    section: Section | None = Field(default=None)

    # Attributes
    order: int = Field(default=0)
    flex: float = Field(default=1.0)
    is_visible: bool = Field(default=True)
