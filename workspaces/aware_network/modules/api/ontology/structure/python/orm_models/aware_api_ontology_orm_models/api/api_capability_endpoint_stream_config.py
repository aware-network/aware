from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Api Ontology Orm Models
from aware_api_ontology_orm_models.api.api_capability_endpoint_stream_enums import ApiCapabilityEndpointStreamMode

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_capability_endpoint_stream_event_config import (
        ApiCapabilityEndpointStreamEventConfig,
    )


class ApiCapabilityEndpointStreamConfig(ORMModel):
    """Optional stream contract beneath one request contract."""

    # Relationships
    api_capability_endpoint_stream_event_configs: list[ApiCapabilityEndpointStreamEventConfig] = Field(
        default_factory=list, exclude=True
    )

    # Attributes
    stream_mode: ApiCapabilityEndpointStreamMode
    description: str | None = Field(default=None)

    # Foreign Keys
    api_capability_endpoint_request_config_id: UUID | None = Field(
        default=None, description="Foreign key for ApiCapabilityEndpointRequestConfig.stream_config"
    )
