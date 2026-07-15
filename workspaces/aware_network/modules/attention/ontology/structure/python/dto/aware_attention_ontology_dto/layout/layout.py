from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.layout.layout_section import LayoutSection


class Layout(BaseModel):
    """
    Declarative layout for Attention Contracts.
    Contract:
    - Defines section topology for one attention contract.
    """

    # Relationships
    sections: list[LayoutSection] = Field(default_factory=list)

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)
