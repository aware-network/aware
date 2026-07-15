from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_capability_endpoint_stream_event_config import (
        ApiCapabilityEndpointStreamEventConfig,
    )
    from aware_meta_ontology_orm_models.class_.inline_value_instance import InlineValueInstance


class ApiCallStreamEvent(ORMModel):
    """
    API-owned stream event receipt for one committed ApiCall.
    Contract:
    - one row records one stream event observed for one ApiCall
    - identity is `(api_call, sequence)` via parent containment + sequence key
    - kind and schema are derivable from the referenced endpoint stream event
    config; this receipt does not duplicate either field
    - normalized event-model truth is one `InlineValueInstance`
    """

    # Relationships
    api_capability_endpoint_stream_event_config: ApiCapabilityEndpointStreamEventConfig
    event_model: InlineValueInstance

    # Attributes
    description: str | None = Field(default=None)
    sequence: int

    # Foreign Keys
    api_call_id: UUID = Field(description="Foreign key for ApiCall.stream_events")
    api_capability_endpoint_stream_event_config_id: UUID | None = Field(
        default=None, description="Foreign key for ApiCallStreamEvent.api_capability_endpoint_stream_event_config"
    )
    event_model_id: UUID | None = Field(default=None, description="Foreign key for ApiCallStreamEvent.event_model")
