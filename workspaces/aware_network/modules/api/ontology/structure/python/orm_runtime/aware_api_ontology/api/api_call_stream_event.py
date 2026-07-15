from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_api_ontology.api.api_capability_endpoint_stream_event_config import (
        ApiCapabilityEndpointStreamEventConfig,
    )
    from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance


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

    @classmethod
    async def create_via_api_call(
        cls,
        api_call_id: UUID,
        sequence: int,
        api_capability_endpoint_stream_event_config_id: UUID,
        description: str | None = None,
    ) -> ApiCallStreamEvent:
        """
        Create one API-owned typed stream event receipt beneath ApiCall.
        Runtime derives the event_model owner key from this receipt identity and
        builds the InlineValueInstance from the referenced stream event
        ClassConfig; callers do not supply a schema/id shortcut.
        """

        payload = {
            "api_call_id": api_call_id,
            "sequence": sequence,
            "api_capability_endpoint_stream_event_config_id": api_capability_endpoint_stream_event_config_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_api_call", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiCallStreamEvent):
            return value
        return ApiCallStreamEvent.validate_invocation_value(value)


class ApiCallStreamEventCreateViaApiCallInput(BaseModel):
    api_call_id: UUID = Field(description="Foreign key for ApiCall.stream_events")
    sequence: int
    api_capability_endpoint_stream_event_config_id: UUID
    description: str | None = Field(default=None)


class ApiCallStreamEventCreateViaApiCallOutput(BaseModel):
    value: ApiCallStreamEvent


FUNCTIONS = {
    "ApiCallStreamEvent": {
        "create_via_api_call": {
            "canonical": {
                "name": "create_via_api_call",
                "description": "Create one API-owned typed stream event receipt beneath ApiCall.\nRuntime derives the event_model owner key from this receipt identity and\nbuilds the InlineValueInstance from the referenced stream event\nClassConfig; callers do not supply a schema/id shortcut.",
                "is_constructor": True,
            },
            "input": ApiCallStreamEventCreateViaApiCallInput,
            "output": ApiCallStreamEventCreateViaApiCallOutput,
        },
    },
}

__all__ = [
    "ApiCallStreamEvent",
    "ApiCallStreamEventCreateViaApiCallInput",
    "ApiCallStreamEventCreateViaApiCallOutput",
    "FUNCTIONS",
]
