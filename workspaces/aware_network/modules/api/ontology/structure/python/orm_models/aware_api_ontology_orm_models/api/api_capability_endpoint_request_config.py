from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_capability_endpoint_response_config import (
        ApiCapabilityEndpointResponseConfig,
    )
    from aware_api_ontology_orm_models.api.api_capability_endpoint_stream_config import (
        ApiCapabilityEndpointStreamConfig,
    )
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig


class ApiCapabilityEndpointRequestConfig(ORMModel):
    """
    Required request contract under one endpoint.
    Caller-facing contract truth:
    - owns the endpoint request DTO `ClassConfig`
    - may own one terminal response contract
    - may own one stream contract
    """

    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)
    response_config: ApiCapabilityEndpointResponseConfig | None = Field(default=None, exclude=True)
    stream_config: ApiCapabilityEndpointStreamConfig | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    api_capability_endpoint_id: UUID = Field(description="Foreign key for ApiCapabilityEndpoint.request_config")
    class_config_id: UUID = Field(description="Foreign key for ApiCapabilityEndpointRequestConfig.class_config")
