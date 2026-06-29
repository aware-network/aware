from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_sdk_ontology_dto.sdk.sdk_operation_api_capability_endpoint import SdkOperationApiCapabilityEndpoint
    from aware_sdk_ontology_dto.sdk.sdk_operation_call import SdkOperationCall
    from aware_sdk_ontology_dto.sdk.sdk_operation_dependency import SdkOperationDependency


class SdkOperation(BaseModel):
    """
    SDK-local operation truth.
    One operation may coordinate one or more API capability endpoints. The API
    endpoint remains the canonical ingress contract for request/response/stream
    payloads.
    """

    # Relationships
    api_capability_endpoints: list[SdkOperationApiCapabilityEndpoint] = Field(default_factory=list)
    sdk_operation_dependencies: list[SdkOperationDependency] = Field(default_factory=list)
    sdk_operation_calls: list[SdkOperationCall] = Field(default_factory=list)

    # Attributes
    name: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    implementation_ref: str | None = Field(default=None)
