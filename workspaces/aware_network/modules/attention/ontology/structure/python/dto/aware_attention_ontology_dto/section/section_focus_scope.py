from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.focus.focus_scope import FocusScope


class SectionFocusScope(BaseModel):
    """FocusScope binding at Section level."""

    # Relationships
    focus_scope: FocusScope | None = Field(default=None)

    # Attributes
    title: str
    description: str | None = Field(default=None)
