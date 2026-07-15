from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_view import ApiView
    from aware_api_ontology_orm_models.api.api_view_capability_endpoint import ApiViewCapabilityEndpoint
    from aware_sdk_ontology_orm_models.sdk.sdk_operation_api_capability_endpoint import (
        SdkOperationApiCapabilityEndpoint,
    )


class SdkOperationApiViewCapabilityEndpoint(ORMModel):
    """
    SDK operation to API view endpoint bridge.
    This binds an SDK operation endpoint to the API-owned view action that exposes
    it. The API remains the source of endpoint and action-key truth.
    """

    # Relationships
    sdk_operation_api_capability_endpoint: SdkOperationApiCapabilityEndpoint | None = Field(default=None)
    api_view: ApiView | None = Field(default=None)
    api_view_capability_endpoint: ApiViewCapabilityEndpoint | None = Field(default=None)

    # Attributes
    api_view_ref: str
    action_key: str
    endpoint_ref: str

    # Foreign Keys
    sdk_operation_id: UUID = Field(description="Foreign key for SdkOperation.api_view_capability_endpoints")
    sdk_operation_api_capability_endpoint_id: UUID = Field(
        description="Foreign key for SdkOperationApiViewCapabilityEndpoint.sdk_operation_api_capability_endpoint"
    )
    api_view_id: UUID = Field(description="Foreign key for SdkOperationApiViewCapabilityEndpoint.api_view")
    api_view_capability_endpoint_id: UUID = Field(
        description="Foreign key for SdkOperationApiViewCapabilityEndpoint.api_view_capability_endpoint"
    )
