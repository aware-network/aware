from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_capability import ApiCapability
    from aware_api_ontology_orm_models.api.api_graph_capability_function import ApiGraphCapabilityFunction


class ApiGraphCapability(ORMModel):
    # Relationships
    api_capability: ApiCapability | None = Field(default=None, exclude=True)
    api_graph_capability_functions: list[ApiGraphCapabilityFunction] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    api_graph_id: UUID = Field(description="Foreign key for ApiGraph.api_graph_capabilities")
    api_capability_id: UUID = Field(description="Foreign key for ApiGraphCapability.api_capability")
