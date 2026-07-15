from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_capability_endpoint_stream_event_config import (
        ApiCapabilityEndpointStreamEventConfig,
    )
    from aware_meta_ontology_dto.class_.inline_value_instance import InlineValueInstance


class ApiCallStreamEvent(BaseModel):
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
