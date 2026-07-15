from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_graph_function import ApiGraphFunction


class ApiGraphCapabilityFunction(ORMModel):
    # Relationships
    api_graph_function: ApiGraphFunction | None = Field(default=None, exclude=True)

    # Attributes
    name: str
    description: str | None = Field(default=None)

    # Foreign Keys
    api_graph_capability_id: UUID = Field(
        description="Foreign key for ApiGraphCapability.api_graph_capability_functions"
    )
    api_graph_function_id: UUID = Field(description="Foreign key for ApiGraphCapabilityFunction.api_graph_function")
