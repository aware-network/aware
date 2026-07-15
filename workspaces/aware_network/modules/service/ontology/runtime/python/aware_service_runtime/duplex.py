from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Literal, TypeVar, cast
from uuid import UUID

from aware_comms import DuplexIpcEndpoint
from aware_comms import DuplexMessageFrame
from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_code.types import JsonObject, JsonValue
from pydantic import BaseModel, ConfigDict, SerializeAsAny, model_validator
from pydantic import field_validator

from aware_service_runtime.contracts import (
    RequestStatus,
    ServiceApiDispatchRequest,
    ServiceApiDispatchReceipt,
    ServiceHostApiIngressRequest,
    ServiceHostBootstrapStatus,
    ServiceHostCapabilityAdvertisement,
    ServiceHostCapabilityState,
    ServiceHostControlRequest,
    ServiceHostControlResponse,
    ServiceHostHandshakeRequest,
    ServiceHostHandshakeResponse,
    ServiceHostReadiness,
    ServiceOperationContext,
    ServiceOperationRequest,
    ServiceOperationResponse,
    ServiceStreamControlKind,
    ServiceStreamControlRequest,
    ServiceStreamControlResponse,
    ServiceStreamEventEnvelope,
    ServiceStreamEventKind,
    ServiceStreamSession,
    StreamLifecycle,
    parse_service_host_control_request,
    parse_service_host_control_response,
)

_TServiceDuplexModel = TypeVar("_TServiceDuplexModel", bound=BaseModel)


def dump_service_duplex_payload(value: object | None) -> JsonValue:
    """Normalize service payloads into JSON-safe values for duplex transport."""

    if value is None:
        return None
    if isinstance(value, BaseModel):
        return cast(JsonValue, value.model_dump(mode="json"))
    if isinstance(value, Enum):
        return cast(JsonValue, dump_service_duplex_payload(value.value))
    if isinstance(value, UUID):
        return str(value)
    if is_dataclass(value):
        return cast(JsonValue, dump_service_duplex_payload(asdict(cast(Any, value))))
    if isinstance(value, Mapping):
        return {
            str(key): dump_service_duplex_payload(item) for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [dump_service_duplex_payload(item) for item in value]
    if isinstance(value, (str, int, float, bool)):
        return cast(JsonValue, value)
    raise TypeError(
        "Service duplex payload must be JSON-serializable or expose "
        "Pydantic/dataclass serialization."
    )


def service_duplex_payload_from_model(model: BaseModel) -> JsonValue:
    """Return the typed JSON payload for a service duplex model."""

    return cast(JsonValue, model.model_dump(mode="json"))


def service_duplex_trusted_json_payload(value: JsonValue) -> JsonValue:
    """Return contract-typed JSON without recursive compatibility normalization."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (dict, list)):
        return value
    raise TypeError(
        "Trusted service duplex payload must already be a JSON value. "
        "Use dump_service_duplex_payload for compatibility normalization."
    )


def service_duplex_operation_response_payload_from_contract(
    response: ServiceOperationResponse,
    *,
    transport_diagnostics: JsonObject | None = None,
) -> JsonValue:
    """Return the duplex response envelope without constructing a response model."""

    return cast(
        JsonValue,
        {
            "status": response.status.value,
            "error": response.error,
            "response_payload": service_duplex_trusted_json_payload(
                response.response_payload
            ),
            "receipt": dump_service_duplex_payload(response.receipt),
            "stream_lifecycle": response.stream_lifecycle.value,
            "transport_diagnostics": service_duplex_trusted_json_payload(
                cast(JsonValue, transport_diagnostics)
            ),
        },
    )


def service_duplex_model_from_frame(
    *,
    frame: DuplexMessageFrame,
    model_type: type[_TServiceDuplexModel],
) -> _TServiceDuplexModel:
    """Decode a service duplex model from a typed payload or legacy data frame."""

    if frame.payload is not None:
        return model_type.model_validate(frame.payload)
    if frame.data:
        return model_type.model_validate_json(frame.data)
    raise ValueError(f"{model_type.__name__} frame must carry payload or legacy data.")


class ServiceDuplexOperationContext(BaseModel):
    """Transport-facing JSON model for one service operation context."""

    model_config = ConfigDict(extra="forbid")

    actor_id: UUID | None
    branch_id: UUID
    projection_hash: str

    @classmethod
    def from_contract(
        cls,
        context: ServiceOperationContext,
    ) -> "ServiceDuplexOperationContext":
        return cls(
            actor_id=context.actor_id,
            branch_id=context.branch_id,
            projection_hash=context.projection_hash,
        )

    def to_contract(self) -> ServiceOperationContext:
        return ServiceOperationContext(
            actor_id=self.actor_id,
            branch_id=self.branch_id,
            projection_hash=self.projection_hash,
        )


class ServiceDuplexOperationRequest(BaseModel):
    """JSON-safe request envelope for the standalone Service host."""

    model_config = ConfigDict(extra="forbid")

    context: ServiceDuplexOperationContext
    service: str
    operation: JsonValue = None
    api_dispatch: ServiceApiDispatchRequest | None = None
    stream_target_id: UUID | None = None
    stream_correlation_id: UUID | None = None
    network_request_id: UUID | None = None

    @classmethod
    def from_contract(
        cls,
        request: ServiceOperationRequest,
    ) -> "ServiceDuplexOperationRequest":
        return cls(
            context=ServiceDuplexOperationContext.from_contract(request.context),
            service=request.service,
            operation=dump_service_duplex_payload(request.operation),
            api_dispatch=request.api_dispatch,
            stream_target_id=request.stream_target_id,
            stream_correlation_id=request.stream_correlation_id,
            network_request_id=request.network_request_id,
        )

    def to_contract(self) -> ServiceOperationRequest:
        return ServiceOperationRequest(
            context=self.context.to_contract(),
            service=self.service,
            operation=self.operation,
            api_dispatch=self.api_dispatch,
            stream_target_id=self.stream_target_id,
            stream_correlation_id=self.stream_correlation_id,
            network_request_id=self.network_request_id,
        )


class ServiceDuplexApiIngressRequest(BaseModel):
    """JSON-safe host-private API ingress request for the standalone Service host."""

    model_config = ConfigDict(extra="forbid")

    actor_id: UUID | None = None
    endpoint_ref: str
    discriminant: str
    request_payload: JsonValue
    invocation_context: JsonObject | None = None
    network_request_id: UUID | None = None
    stream_requested: bool = False
    target_branch_id: UUID | None = None
    target_projection_hash: str | None = None

    @classmethod
    def from_contract(
        cls,
        request: ServiceHostApiIngressRequest,
    ) -> "ServiceDuplexApiIngressRequest":
        return cls(
            actor_id=request.actor_id,
            endpoint_ref=request.endpoint_ref,
            discriminant=request.discriminant,
            request_payload=dump_service_duplex_payload(request.request_payload),
            invocation_context=(
                cast(
                    JsonObject, dump_service_duplex_payload(request.invocation_context)
                )
                if request.invocation_context is not None
                else None
            ),
            network_request_id=request.network_request_id,
            stream_requested=request.stream_requested,
            target_branch_id=request.target_branch_id,
            target_projection_hash=request.target_projection_hash,
        )

    def to_contract(self) -> ServiceHostApiIngressRequest:
        if not isinstance(self.request_payload, dict):
            raise RuntimeError(
                "Service host API ingress request payload must be a JSON object."
            )
        return ServiceHostApiIngressRequest(
            actor_id=self.actor_id,
            endpoint_ref=self.endpoint_ref,
            discriminant=self.discriminant,
            request_payload=cast(JsonObject, self.request_payload),
            invocation_context=(
                cast(JsonObject, self.invocation_context)
                if self.invocation_context is not None
                else None
            ),
            network_request_id=self.network_request_id,
            stream_requested=self.stream_requested,
            target_branch_id=self.target_branch_id,
            target_projection_hash=self.target_projection_hash,
        )


class ServiceDuplexHostControlRequest(BaseModel):
    """JSON-safe host-control request for one standalone Service host."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["service_host_control"] = "service_host_control"
    request: SerializeAsAny[ServiceHostControlRequest]

    @field_validator("request", mode="before")
    @classmethod
    def _parse_request(cls, v):  # type: ignore[no-untyped-def]
        return parse_service_host_control_request(v)

    @classmethod
    def from_contract(
        cls,
        request: ServiceHostControlRequest,
    ) -> "ServiceDuplexHostControlRequest":
        return cls(request=request)

    def to_contract(self) -> ServiceHostControlRequest:
        return self.request


class ServiceDuplexHostControlResponse(BaseModel):
    """JSON-safe host-control response for one standalone Service host."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["service_host_control"] = "service_host_control"
    response: SerializeAsAny[ServiceHostControlResponse]

    @field_validator("response", mode="before")
    @classmethod
    def _parse_response(cls, v):  # type: ignore[no-untyped-def]
        return parse_service_host_control_response(v)

    @classmethod
    def from_contract(
        cls,
        response: ServiceHostControlResponse,
    ) -> "ServiceDuplexHostControlResponse":
        return cls(response=response)

    def to_contract(self) -> ServiceHostControlResponse:
        return self.response


class ServiceDuplexOperationResponse(BaseModel):
    """JSON-safe response envelope for the standalone Service host."""

    model_config = ConfigDict(extra="forbid")

    status: RequestStatus
    error: str | None = None
    response_payload: JsonValue = None
    receipt: ServiceApiDispatchReceipt | None = None
    stream_lifecycle: StreamLifecycle = StreamLifecycle.auto_close
    transport_diagnostics: JsonObject | None = None

    @classmethod
    def from_contract(
        cls,
        response: ServiceOperationResponse,
        *,
        transport_diagnostics: JsonObject | None = None,
    ) -> "ServiceDuplexOperationResponse":
        return cls(
            status=response.status,
            error=response.error,
            response_payload=dump_service_duplex_payload(response.response_payload),
            receipt=response.receipt,
            stream_lifecycle=response.stream_lifecycle,
            transport_diagnostics=transport_diagnostics,
        )

    def to_contract(self) -> ServiceOperationResponse:
        return ServiceOperationResponse(
            status=self.status,
            error=self.error,
            response_payload=self.response_payload,
            receipt=self.receipt,
            stream_lifecycle=self.stream_lifecycle,
        )


class ServiceDuplexHandshakeRequest(BaseModel):
    """JSON-safe handshake request envelope for the standalone Service host."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["service_host_handshake"] = "service_host_handshake"
    supported_protocol_versions: tuple[str, ...] = ()

    @classmethod
    def from_contract(
        cls,
        request: ServiceHostHandshakeRequest,
    ) -> "ServiceDuplexHandshakeRequest":
        return cls(
            supported_protocol_versions=request.supported_protocol_versions,
        )

    def to_contract(self) -> ServiceHostHandshakeRequest:
        return ServiceHostHandshakeRequest(
            supported_protocol_versions=self.supported_protocol_versions,
        )


class ServiceDuplexHostReadiness(BaseModel):
    """JSON-safe readiness snapshot for one Service host handshake response."""

    model_config = ConfigDict(extra="forbid")

    is_ready: bool
    status: ServiceHostBootstrapStatus
    reason: str | None = None
    detail_payload: JsonValue = None

    @classmethod
    def from_contract(
        cls,
        readiness: ServiceHostReadiness,
    ) -> "ServiceDuplexHostReadiness":
        return cls(
            is_ready=readiness.is_ready,
            status=readiness.status,
            reason=readiness.reason,
            detail_payload=dump_service_duplex_payload(readiness.detail_payload),
        )

    def to_contract(self) -> ServiceHostReadiness:
        return ServiceHostReadiness(
            is_ready=self.is_ready,
            status=self.status,
            reason=self.reason,
            detail_payload=self.detail_payload,
        )


class ServiceDuplexHostCapabilityAdvertisement(BaseModel):
    """JSON-safe host capability advertisement for handshake publication."""

    model_config = ConfigDict(extra="forbid")

    capability_id: str
    state: ServiceHostCapabilityState = ServiceHostCapabilityState.available
    detail_payload: JsonValue = None

    @classmethod
    def from_contract(
        cls,
        capability: ServiceHostCapabilityAdvertisement,
    ) -> "ServiceDuplexHostCapabilityAdvertisement":
        return cls(
            capability_id=capability.capability_id,
            state=capability.state,
            detail_payload=dump_service_duplex_payload(capability.detail_payload),
        )

    def to_contract(self) -> ServiceHostCapabilityAdvertisement:
        return ServiceHostCapabilityAdvertisement(
            capability_id=self.capability_id,
            state=self.state,
            detail_payload=self.detail_payload,
        )


class ServiceDuplexHandshakeResponse(BaseModel):
    """JSON-safe handshake response envelope for the standalone Service host."""

    model_config = ConfigDict(extra="forbid")

    endpoint: DuplexIpcEndpoint
    protocol_version: str
    host_id: str
    host_version: str | None = None
    readiness: ServiceDuplexHostReadiness
    capabilities: tuple[ServiceDuplexHostCapabilityAdvertisement, ...] = ()

    @classmethod
    def from_contract(
        cls,
        response: ServiceHostHandshakeResponse,
    ) -> "ServiceDuplexHandshakeResponse":
        return cls(
            endpoint=response.endpoint,
            protocol_version=response.protocol_version,
            host_id=response.host_id,
            host_version=response.host_version,
            readiness=ServiceDuplexHostReadiness.from_contract(response.readiness),
            capabilities=tuple(
                ServiceDuplexHostCapabilityAdvertisement.from_contract(item)
                for item in response.capabilities
            ),
        )

    def to_contract(self) -> ServiceHostHandshakeResponse:
        return ServiceHostHandshakeResponse(
            endpoint=self.endpoint,
            protocol_version=self.protocol_version,
            host_id=self.host_id,
            host_version=self.host_version,
            readiness=self.readiness.to_contract(),
            capabilities=tuple(item.to_contract() for item in self.capabilities),
        )


class ServiceDuplexStreamSession(BaseModel):
    """JSON-safe stream session envelope for the standalone Service host."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    request: ServiceDuplexOperationRequest
    publisher_id: str | None = None
    subscriber_id: str | None = None

    @classmethod
    def from_contract(
        cls,
        session: ServiceStreamSession,
    ) -> "ServiceDuplexStreamSession":
        return cls(
            session_id=session.session_id,
            request=ServiceDuplexOperationRequest.from_contract(session.request),
            publisher_id=session.publisher_id,
            subscriber_id=session.subscriber_id,
        )

    def to_contract(self) -> ServiceStreamSession:
        return ServiceStreamSession(
            session_id=self.session_id,
            request=self.request.to_contract(),
            publisher_id=self.publisher_id,
            subscriber_id=self.subscriber_id,
        )


class ServiceDuplexStreamControlRequest(BaseModel):
    """JSON-safe control request envelope for one Service stream session."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    kind: ServiceStreamControlKind
    reason: str | None = None
    detail_payload: JsonValue = None

    @classmethod
    def from_contract(
        cls,
        request: ServiceStreamControlRequest,
    ) -> "ServiceDuplexStreamControlRequest":
        return cls(
            session_id=request.session_id,
            kind=request.kind,
            reason=request.reason,
            detail_payload=dump_service_duplex_payload(request.detail_payload),
        )

    def to_contract(self) -> ServiceStreamControlRequest:
        return ServiceStreamControlRequest(
            session_id=self.session_id,
            kind=self.kind,
            reason=self.reason,
            detail_payload=self.detail_payload,
        )


class ServiceDuplexStreamControlResponse(BaseModel):
    """JSON-safe control response envelope for one Service stream session."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    kind: ServiceStreamControlKind
    status: RequestStatus
    error: str | None = None
    detail_payload: JsonValue = None

    @classmethod
    def from_contract(
        cls,
        response: ServiceStreamControlResponse,
    ) -> "ServiceDuplexStreamControlResponse":
        return cls(
            session_id=response.session_id,
            kind=response.kind,
            status=response.status,
            error=response.error,
            detail_payload=dump_service_duplex_payload(response.detail_payload),
        )

    def to_contract(self) -> ServiceStreamControlResponse:
        return ServiceStreamControlResponse(
            session_id=self.session_id,
            kind=self.kind,
            status=self.status,
            error=self.error,
            detail_payload=self.detail_payload,
        )


class ServiceDuplexStreamEventEnvelope(BaseModel):
    """JSON-safe semantic stream envelope carried over Service transport."""

    model_config = ConfigDict(extra="forbid")

    session: ServiceDuplexStreamSession
    sequence: int
    kind: ServiceStreamEventKind
    item_key: str
    payload: JsonValue = None

    @classmethod
    def from_contract(
        cls,
        envelope: ServiceStreamEventEnvelope,
    ) -> "ServiceDuplexStreamEventEnvelope":
        return cls(
            session=ServiceDuplexStreamSession.from_contract(envelope.session),
            sequence=envelope.sequence,
            kind=envelope.kind,
            item_key=envelope.item_key,
            payload=dump_service_duplex_payload(envelope.payload),
        )

    def to_contract(self) -> ServiceStreamEventEnvelope:
        return ServiceStreamEventEnvelope(
            session=self.session.to_contract(),
            sequence=self.sequence,
            kind=self.kind,
            item_key=self.item_key,
            payload=self.payload,
        )


class ServiceDuplexStreamEventKind(str, Enum):
    """Notification kinds emitted by the standalone Service host."""

    RESPONSE = "response"
    CLOSE = "close"


class ServiceDuplexStreamEvent(BaseModel):
    """JSON-safe stream event envelope over the duplex transport."""

    model_config = ConfigDict(extra="forbid")

    kind: ServiceDuplexStreamEventKind
    response: ServiceDuplexOperationResponse | None = None

    @model_validator(mode="after")
    def _validate_shape(self) -> "ServiceDuplexStreamEvent":
        if self.kind is ServiceDuplexStreamEventKind.RESPONSE and self.response is None:
            raise ValueError("response stream events require a response payload")
        if (
            self.kind is ServiceDuplexStreamEventKind.CLOSE
            and self.response is not None
        ):
            raise ValueError("close stream events must not carry a response payload")
        return self

    @classmethod
    def response_event(
        cls,
        response: ServiceOperationResponse,
    ) -> "ServiceDuplexStreamEvent":
        return cls(
            kind=ServiceDuplexStreamEventKind.RESPONSE,
            response=ServiceDuplexOperationResponse.from_contract(response),
        )

    @classmethod
    def close_event(cls) -> "ServiceDuplexStreamEvent":
        return cls(kind=ServiceDuplexStreamEventKind.CLOSE)


class ServiceDuplexLaneCommitReceiptNotification(BaseModel):
    """Host-private lane receipt notification for one hosted Service process."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["lane_commit_receipt"] = "lane_commit_receipt"
    receipt: LaneCommitReceiptNotification

    @classmethod
    def from_contract(
        cls,
        receipt: LaneCommitReceiptNotification,
    ) -> "ServiceDuplexLaneCommitReceiptNotification":
        return cls(receipt=receipt)

    def to_contract(self) -> LaneCommitReceiptNotification:
        return self.receipt


__all__ = [
    "JsonValue",
    "ServiceDuplexApiIngressRequest",
    "ServiceDuplexHostControlRequest",
    "ServiceDuplexHostControlResponse",
    "ServiceDuplexOperationContext",
    "ServiceDuplexOperationRequest",
    "ServiceDuplexOperationResponse",
    "ServiceDuplexLaneCommitReceiptNotification",
    "ServiceDuplexStreamControlRequest",
    "ServiceDuplexStreamControlResponse",
    "ServiceDuplexStreamEventEnvelope",
    "ServiceDuplexStreamEvent",
    "ServiceDuplexStreamEventKind",
    "ServiceDuplexStreamSession",
    "dump_service_duplex_payload",
    "service_duplex_operation_response_payload_from_contract",
    "service_duplex_payload_from_model",
    "service_duplex_trusted_json_payload",
]
