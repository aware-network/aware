from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.section.section_focus_scope import SectionFocusScope


class Section(BaseModel):
    """Declarative "representation unit" as section for Attention contract via FocusScope."""

    # Relationships
    focus_scopes: list[SectionFocusScope] = Field(default_factory=list)
    active_focus_scope: SectionFocusScope | None = Field(default=None)

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)
