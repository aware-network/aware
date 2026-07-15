from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Api Ontology
from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_api_ontology.api.api_call_outcome import ApiCallOutcome
    from aware_api_ontology.api.api_call_stream_event import ApiCallStreamEvent
    from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance


class ApiCall(ORMModel):
    """
    Stage-one API-owned ingress/provenance receipt.
    Contract:
    - one `ApiCall` means one caller hit on one `ApiCapabilityEndpoint`
    - normalized request-model truth is one `InlineValueInstance`
    - this object is ingress truth only and must not collapse into endpoint-function or Service fulfillment rails
    """

    # Relationships
    outcome: ApiCallOutcome | None = Field(default=None)
    request_model: InlineValueInstance
    stream_events: list[ApiCallStreamEvent] = Field(default_factory=list)

    # Attributes
    call_key: UUID = Field(description="Stable external/request identity for one endpoint hit.")
    description: str | None = Field(default=None)
    request_hash: str

    # Foreign Keys
    api_capability_endpoint_id: UUID = Field(description="Foreign key for ApiCapabilityEndpoint.api_calls")
    request_model_id: UUID | None = Field(default=None, description="Foreign key for ApiCall.request_model")

    async def create_outcome(
        self, status: ApiCallOutcomeStatus = ApiCallOutcomeStatus.succeeded, error: str | None = None
    ) -> ApiCallOutcome:
        """Create one terminal response receipt under this ApiCall."""

        payload = {"status": status, "error": error}
        result = await invoke_instance(orm_model=self, function_name="create_outcome", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_call_outcome import ApiCallOutcome

        if isinstance(value, ApiCallOutcome):
            return value
        return ApiCallOutcome.validate_invocation_value(value)

    async def record_stream_event(
        self, sequence: int, api_capability_endpoint_stream_event_config_id: UUID, description: str | None = None
    ) -> ApiCallStreamEvent:
        """
        Record one typed stream event receipt under this ApiCall.

        Contract:
        - Identity is `(api_call, sequence)`.
        - Kind and ClassConfig are derivable from the referenced endpoint
          stream event config; this object does not duplicate them.
        - Runtime must fail closed when the referenced stream event config does
          not belong to this call's endpoint stream contract.
        """

        payload = {
            "sequence": sequence,
            "api_capability_endpoint_stream_event_config_id": api_capability_endpoint_stream_event_config_id,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="record_stream_event", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_call_stream_event import ApiCallStreamEvent

        if isinstance(value, ApiCallStreamEvent):
            return value
        return ApiCallStreamEvent.validate_invocation_value(value)

    @classmethod
    async def create_via_api_capability_endpoint(
        cls,
        api_capability_endpoint_id: UUID,
        call_key: UUID,
        request_class_config_id: UUID,
        description: str | None = None,
    ) -> ApiCall:
        """Create one stage-one API call receipt under ApiCapabilityEndpoint."""

        payload = {
            "api_capability_endpoint_id": api_capability_endpoint_id,
            "call_key": call_key,
            "request_class_config_id": request_class_config_id,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_api_capability_endpoint", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiCall):
            return value
        return ApiCall.validate_invocation_value(value)


class ApiCallCreateOutcomeInput(BaseModel):
    status: ApiCallOutcomeStatus = Field(default=ApiCallOutcomeStatus.succeeded)
    error: str | None = Field(default=None)


class ApiCallCreateOutcomeOutput(BaseModel):
    value: ApiCallOutcome


class ApiCallRecordStreamEventInput(BaseModel):
    sequence: int
    api_capability_endpoint_stream_event_config_id: UUID
    description: str | None = Field(default=None)


class ApiCallRecordStreamEventOutput(BaseModel):
    value: ApiCallStreamEvent


class ApiCallCreateViaApiCapabilityEndpointInput(BaseModel):
    api_capability_endpoint_id: UUID = Field(description="Foreign key for ApiCapabilityEndpoint.api_calls")
    call_key: UUID
    request_class_config_id: UUID
    description: str | None = Field(default=None)


class ApiCallCreateViaApiCapabilityEndpointOutput(BaseModel):
    value: ApiCall


FUNCTIONS = {
    "ApiCall": {
        "create_outcome": {
            "canonical": {
                "name": "create_outcome",
                "description": "Create one terminal response receipt under this ApiCall.",
                "is_constructor": False,
            },
            "input": ApiCallCreateOutcomeInput,
            "output": ApiCallCreateOutcomeOutput,
        },
        "record_stream_event": {
            "canonical": {
                "name": "record_stream_event",
                "description": "Record one typed stream event receipt under this ApiCall.\n\nContract:\n- Identity is `(api_call, sequence)`.\n- Kind and ClassConfig are derivable from the referenced endpoint\n  stream event config; this object does not duplicate them.\n- Runtime must fail closed when the referenced stream event config does\n  not belong to this call's endpoint stream contract.",
                "is_constructor": False,
            },
            "input": ApiCallRecordStreamEventInput,
            "output": ApiCallRecordStreamEventOutput,
        },
        "create_via_api_capability_endpoint": {
            "canonical": {
                "name": "create_via_api_capability_endpoint",
                "description": "Create one stage-one API call receipt under ApiCapabilityEndpoint.",
                "is_constructor": True,
            },
            "input": ApiCallCreateViaApiCapabilityEndpointInput,
            "output": ApiCallCreateViaApiCapabilityEndpointOutput,
        },
    },
}

__all__ = [
    "ApiCall",
    "ApiCallCreateOutcomeInput",
    "ApiCallCreateOutcomeOutput",
    "ApiCallRecordStreamEventInput",
    "ApiCallRecordStreamEventOutput",
    "ApiCallCreateViaApiCapabilityEndpointInput",
    "ApiCallCreateViaApiCapabilityEndpointOutput",
    "FUNCTIONS",
]
