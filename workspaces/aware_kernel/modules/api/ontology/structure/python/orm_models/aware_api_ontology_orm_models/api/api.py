from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_capability import ApiCapability
    from aware_api_ontology_orm_models.api.api_graph import ApiGraph


class Api(ORMModel):
    # Relationships
    api_graphs: list[ApiGraph] = Field(default_factory=list, exclude=True)
    api_capabilities: list[ApiCapability] = Field(default_factory=list, exclude=True)

    # Attributes
    name: str
    description: str | None = Field(default=None)
