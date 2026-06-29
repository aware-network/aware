from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_graph_capability_function import ApiGraphCapabilityFunction


class ApiCapabilityEndpointFunction(ORMModel):
    """
    downstream fulfillment contract under one endpoint.
    Config-side truth:
    - this is the API-owned agreement for how an endpoint may be fulfilled toward graph callable truth
    - this is not the caller-facing hit surface
    - stage-one `ApiCall` must not anchor here
    Service/runtime fulfills this contract downstream.
    """

    # Relationships
    api_graph_capability_function: ApiGraphCapabilityFunction | None = Field(default=None, exclude=True)

    # Attributes
    name: str
    description: str | None = Field(default=None)

    # Foreign Keys
    api_capability_endpoint_id: UUID = Field(
        description="Foreign key for ApiCapabilityEndpoint.api_capability_endpoint_functions"
    )
    api_graph_capability_function_id: UUID = Field(
        description="Foreign key for ApiCapabilityEndpointFunction.api_graph_capability_function"
    )
