from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_call import ApiCall
    from aware_api_ontology_orm_models.api.api_capability_endpoint_function import ApiCapabilityEndpointFunction
    from aware_api_ontology_orm_models.api.api_capability_endpoint_request_config import (
        ApiCapabilityEndpointRequestConfig,
    )


class ApiCapabilityEndpoint(ORMModel):
    """
    Public API caller hit surface.
    Caller-facing truth:
    - the caller hits one endpoint
    - the caller provides payload through this endpoint's request contract DTO `ClassConfig`
    - stage-one `ApiCall` anchors here, not on endpoint-function fulfillment
    This object is ingress contract truth, not graph-call fulfillment truth.
    Endpoint identity stays on the public port rail (`api_capability_id + name`).
    The required request contract is created beneath that one endpoint rail during
    endpoint construction; it is not a second public authoring step.
    """

    # Relationships
    api_calls: list[ApiCall] = Field(default_factory=list, exclude=True)
    request_config: ApiCapabilityEndpointRequestConfig | None = Field(default=None, exclude=True)
    api_capability_endpoint_functions: list[ApiCapabilityEndpointFunction] = Field(default_factory=list, exclude=True)

    # Attributes
    name: str
    description: str | None = Field(default=None)

    # Foreign Keys
    api_capability_id: UUID = Field(description="Foreign key for ApiCapability.api_capability_endpoints")
