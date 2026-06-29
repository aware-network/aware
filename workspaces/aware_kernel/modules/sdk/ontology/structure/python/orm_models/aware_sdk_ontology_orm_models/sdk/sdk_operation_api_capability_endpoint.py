from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_capability_endpoint import ApiCapabilityEndpoint


class SdkOperationApiCapabilityEndpoint(ORMModel):
    """SDK operation to API endpoint bridge."""

    # Relationships
    api_capability_endpoint: ApiCapabilityEndpoint | None = Field(default=None)

    # Attributes
    name: str
    endpoint_ref: str | None = Field(default=None)
    discriminant: str | None = Field(default=None)
    role: str = Field(default="primary")
    order: int = Field(default=1)
    required: bool = Field(default=True)

    # Foreign Keys
    sdk_operation_id: UUID = Field(description="Foreign key for SdkOperation.api_capability_endpoints")
    api_capability_endpoint_id: UUID = Field(
        description="Foreign key for SdkOperationApiCapabilityEndpoint.api_capability_endpoint"
    )
