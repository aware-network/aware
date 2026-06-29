from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig


class ApiCapabilityEndpointResponseConfig(ORMModel):
    """Optional terminal response contract beneath one request contract."""

    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    api_capability_endpoint_request_config_id: UUID | None = Field(
        default=None, description="Foreign key for ApiCapabilityEndpointRequestConfig.response_config"
    )
    class_config_id: UUID = Field(description="Foreign key for ApiCapabilityEndpointResponseConfig.class_config")
