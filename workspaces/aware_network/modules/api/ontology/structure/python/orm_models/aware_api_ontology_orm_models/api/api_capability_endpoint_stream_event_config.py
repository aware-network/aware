from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Api Ontology Orm Models
from aware_api_ontology_orm_models.api.api_capability_endpoint_stream_enums import ApiCapabilityEndpointStreamEventKind

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig


class ApiCapabilityEndpointStreamEventConfig(ORMModel):
    """Typed event contract beneath one endpoint stream contract."""

    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)

    # Attributes
    kind: ApiCapabilityEndpointStreamEventKind
    description: str | None = Field(default=None)

    # Foreign Keys
    api_capability_endpoint_stream_config_id: UUID = Field(
        description="Foreign key for ApiCapabilityEndpointStreamConfig.api_capability_endpoint_stream_event_configs"
    )
    class_config_id: UUID = Field(description="Foreign key for ApiCapabilityEndpointStreamEventConfig.class_config")
