from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout_section import LayoutSection


class Layout(ORMModel):
    """
    Declarative layout for Attention Contracts.
    Contract:
    - Defines section topology for one attention contract.
    """

    # Relationships
    sections: list[LayoutSection] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)
