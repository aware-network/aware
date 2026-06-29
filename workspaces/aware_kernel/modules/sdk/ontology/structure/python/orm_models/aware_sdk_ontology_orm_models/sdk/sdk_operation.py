from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_sdk_ontology_orm_models.sdk.sdk_operation_api_capability_endpoint import (
        SdkOperationApiCapabilityEndpoint,
    )
    from aware_sdk_ontology_orm_models.sdk.sdk_operation_call import SdkOperationCall
    from aware_sdk_ontology_orm_models.sdk.sdk_operation_dependency import SdkOperationDependency


class SdkOperation(ORMModel):
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

    # Foreign Keys
    sdk_config_id: UUID = Field(description="Foreign key for SdkConfig.operations")
