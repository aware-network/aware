from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_interface_ontology_dto.render.render_component_contract import RenderComponentContract


class RenderComponentConfig(BaseModel):
    # Relationships
    contracts: list[RenderComponentContract] = Field(default_factory=list)

    # Attributes
    name: str
    description: str | None = Field(default=None)
