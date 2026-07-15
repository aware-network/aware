from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_interface_ontology_orm_models.render.render_component_contract import RenderComponentContract


class RenderComponentConfig(ORMModel):
    # Relationships
    contracts: list[RenderComponentContract] = Field(default_factory=list)

    # Attributes
    name: str
    description: str | None = Field(default=None)
