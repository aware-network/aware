from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol, TypeAlias, cast
from uuid import UUID

from aware_comms import DuplexIpcEndpoint
from aware_code.types import JsonValue
from aware_code.types import JsonObject
from aware_service_service_dto.comms.models.service import (
    ActivateServiceHostLifecyclesHostControlRequest,
    ActivateServiceHostLifecyclesHostControlResponse,
    ConfigureServiceApiDependencyRoutesHostControlRequest,
    ConfigureServiceApiDependencyRoutesHostControlResponse,
    RequestStatus,
    ServiceApiDispatchEnvelope,
    ServiceApiDispatchFulfillmentBinding,
    ServiceApiDispatchRequest,
    ServiceApiDispatchReceipt,
    ServiceHostControlRequest,
    ServiceHostControlResponse,
    ServiceOperationContext,
    ServiceOperationRequest,
    ServiceOperationResponse,
    StreamLifecycle,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentOperationContext,
)
from aware_environment_service_dto.environment.environment_service_operation import (
    EnvironmentServiceOperation,
)
from aware_environment_service_dto.environment.environment_service_operation import (
    EnvironmentServiceOperationRequest,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
)
from pydantic import SerializeAsAny, model_validator

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology.graph.projection.object_projection_graph import (
        ObjectProjectionGraph,
    )


SERVICE_HOST_PROTOCOL_VERSION = "1"
SERVICE_HOST_CAPABILITY_API_DISPATCH = "api_dispatch"
SERVICE_HOST_API_DISPATCH_SERVICE_NAMES_KEY = "service_names"
SERVICE_HOST_API_DISPATCH_SERVICE_IDS_BY_NAME_KEY = "service_ids_by_name"
SERVICE_HOST_API_DISPATCH_SERVICE_PACKAGE_IDS_BY_NAME_KEY = (
    "service_package_ids_by_name"
)
SERVICE_HOST_API_DISPATCH_SERVICE_ENDPOINT_REFS_KEY = "service_endpoint_refs"
SERVICE_HOST_API_DISPATCH_SERVICE_STREAM_ENDPOINT_REFS_KEY = (
    "service_stream_endpoint_refs"
)
_REMOTE_SERVICE_API_MODEL_EXPORTS = (
    RequestStatus,
    ServiceApiDispatchEnvelope,
    ServiceApiDispatchFulfillmentBinding,
    ServiceApiDispatchRequest,
    ServiceApiDispatchReceipt,
    ServiceHostControlRequest,
    ServiceHostControlResponse,
    ActivateServiceHostLifecyclesHostControlRequest,
    ActivateServiceHostLifecyclesHostControlResponse,
    ConfigureServiceApiDependencyRoutesHostControlRequest,
    ConfigureServiceApiDependencyRoutesHostControlResponse,
    ServiceOperationContext,
    ServiceOperationRequest,
    ServiceOperationResponse,
    StreamLifecycle,
)

_SERVICE_HOST_CONTROL_REQUEST_MODEL_BY_OPERATION: dict[
    str, type[ServiceHostControlRequest]
] = {
    "activate_service_host_lifecycles": (
        ActivateServiceHostLifecyclesHostControlRequest
    ),
    "configure_service_api_dependency_routes": (
        ConfigureServiceApiDependencyRoutesHostControlRequest
    ),
}
_SERVICE_HOST_CONTROL_RESPONSE_MODEL_BY_OPERATION: dict[
    str, type[ServiceHostControlResponse]
] = {
    "activate_service_host_lifecycles": (
        ActivateServiceHostLifecyclesHostControlResponse
    ),
    "configure_service_api_dependency_routes": (
        ConfigureServiceApiDependencyRoutesHostControlResponse
    ),
}


class ServiceGraphCatalog(Protocol):
    """Ontology-owned graph catalog needed by service API target resolution."""

    @property
    def ocg(self) -> "ObjectConfigGraph": ...

    @property
    def class_configs_by_id(self) -> Mapping[UUID, "ClassConfig"]: ...

    @property
    def attribute_configs_by_id(self) -> Mapping[UUID, "AttributeConfig"]: ...

    @property
    def opg_by_id(self) -> Mapping[UUID, "ObjectProjectionGraph"]: ...

    @property
    def opg_by_hash(self) -> Mapping[str, "ObjectProjectionGraph"]: ...


class ServiceGraphContext(Protocol):
    """Meta SDK graph context that exposes its ontology-owned catalog."""

    @property
    def index(self) -> ServiceGraphCatalog: ...


ServiceGraphContextLike: TypeAlias = ServiceGraphContext | ServiceGraphCatalog


class ServiceGraphContextProvider(Protocol):
    """Provider for ontology-owned graph context/catalog resolution."""

    async def resolve_graph_context(self) -> ServiceGraphContextLike:
        """Return ontology-owned graph context/catalog for target resolution."""
        ...


class BootstrapServiceContractAccessContextHostControlRequest(
    ServiceHostControlRequest
):
    """Host-control request for Service-owned contract access context bootstrap."""

    operation: str = "bootstrap_service_contract_access_context"
    service_id: UUID
    consumer_finance_entity_id: UUID | None = None
    service_operation_config_id: UUID | None = None
    service_subscription_id: UUID | None = None
    service_contract_id: UUID | None = None
    service_contract_config_id: UUID | None = None
    smart_contract_id: UUID | None = None


class BootstrapServiceContractAccessContextHostControlResponse(
    ServiceHostControlResponse
):
    """Host-control response carrying the Service contract access bootstrap read model."""

    operation: str = "bootstrap_service_contract_access_context"
    ready: bool = False
    blocker: str | None = None
    blockers: tuple[str, ...] = ()
    next_action: str | None = None
    bootstrap: JsonObject | None = None


class EnsureServiceContractAccessContextHostControlRequest(ServiceHostControlRequest):
    """Host-control request to admit local Service contract access truth."""

    operation: str = "ensure_service_contract_access_context"
    service_id: UUID
    consumer_finance_entity_id: UUID | None = None
    service_operation_config_id: UUID | None = None
    service_subscription_id: UUID | None = None
    service_contract_id: UUID | None = None
    service_contract_config_id: UUID | None = None
    smart_contract_id: UUID | None = None
    service_contract_config_name: str = "local_dev"
    commercial_profile_id: UUID | None = None
    producer_finance_entity_id: UUID | None = None
    service_plan_id: UUID | None = None


class EnsureServiceContractAccessContextHostControlResponse(ServiceHostControlResponse):
    """Host-control response for local Service contract access admission."""

    operation: str = "ensure_service_contract_access_context"
    ready: bool = False
    ensured: bool = False
    blocker: str | None = None
    blockers: tuple[str, ...] = ()
    next_action: str | None = None
    bootstrap: JsonObject | None = None
    admission: JsonObject | None = None


_SERVICE_HOST_CONTROL_REQUEST_MODEL_BY_OPERATION[
    "bootstrap_service_contract_access_context"
] = BootstrapServiceContractAccessContextHostControlRequest
_SERVICE_HOST_CONTROL_RESPONSE_MODEL_BY_OPERATION[
    "bootstrap_service_contract_access_context"
] = BootstrapServiceContractAccessContextHostControlResponse
_SERVICE_HOST_CONTROL_REQUEST_MODEL_BY_OPERATION[
    "ensure_service_contract_access_context"
] = EnsureServiceContractAccessContextHostControlRequest
_SERVICE_HOST_CONTROL_RESPONSE_MODEL_BY_OPERATION[
    "ensure_service_contract_access_context"
] = EnsureServiceContractAccessContextHostControlResponse


def parse_service_host_control_request(
    value: object,
) -> ServiceHostControlRequest:
    """Parse host-control payloads while preserving operation-specific DTOs."""

    if isinstance(value, ServiceHostControlRequest):
        return value
    model = ServiceHostControlRequest
    if isinstance(value, Mapping):
        operation = value.get("operation")
        if isinstance(operation, str):
            model = _SERVICE_HOST_CONTROL_REQUEST_MODEL_BY_OPERATION.get(
                operation,
                model,
            )
    return model.model_validate(value)


def parse_service_host_control_response(
    value: object,
) -> ServiceHostControlResponse:
    """Parse host-control responses while preserving operation-specific DTOs."""

    if isinstance(value, ServiceHostControlResponse):
        return value
    model = ServiceHostControlResponse
    if isinstance(value, Mapping):
        operation = value.get("operation")
        if isinstance(operation, str):
            model = _SERVICE_HOST_CONTROL_RESPONSE_MODEL_BY_OPERATION.get(
                operation,
                model,
            )
    return model.model_validate(value)


class ServiceHostBootstrapStatus(str, Enum):
    """Canonical readiness states published by the standalone Service host."""

    starting = "starting"
    awaiting_dependency_routes = "awaiting_dependency_routes"
    ready = "ready"
    failed = "failed"


class ServiceHostCapabilityState(str, Enum):
    """Availability states for one host-level capability advertisement."""

    available = "available"
    unavailable = "unavailable"


@dataclass(frozen=True, slots=True)
class ServiceHostApiIngressRequest:
    """Host-private API ingress request carried over local Service duplex IPC."""

    actor_id: UUID | None
    endpoint_ref: str
    discriminant: str
    request_payload: JsonObject
    invocation_context: JsonObject | None = None
    network_request_id: UUID | None = None
    stream_requested: bool = False
    target_branch_id: UUID | None = None
    target_projection_hash: str | None = None


def coerce_request_status(
    value: object,
    *,
    default: RequestStatus = RequestStatus.failed,
) -> RequestStatus:
    if isinstance(value, RequestStatus):
        return value
    raw = getattr(value, "value", value)
    if isinstance(raw, str):
        try:
            return RequestStatus(raw.strip().lower())
        except ValueError:
            return default
    return default


class ServiceStreamControlKind(str, Enum):
    """Semantic control kinds for Service-owned stream sessions."""

    OPEN_SESSION = "open_session"
    ACCEPT_SESSION = "accept_session"
    REJECT_SESSION = "reject_session"
    CANCEL_SESSION = "cancel_session"
    CLOSE_SESSION = "close_session"
    STREAM_ERROR = "stream_error"
    FLOW_UPDATE = "flow_update"


class ServiceStreamEventKind(str, Enum):
    """Semantic event categories above one Service stream session."""

    SNAPSHOT = "snapshot"
    DELTA = "delta"
    NOTICE = "notice"
    COMPLETE = "complete"
    EVENT_ERROR = "event_error"


@dataclass(frozen=True, slots=True)
class ServiceHostHandshakeRequest:
    """Client-supported protocol information for one host handshake probe."""

    supported_protocol_versions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceHostReadiness:
    """Typed readiness snapshot published by the standalone Service host."""

    is_ready: bool
    status: ServiceHostBootstrapStatus
    reason: str | None = None
    detail_payload: object | None = None


@dataclass(frozen=True, slots=True)
class ServiceHostCapabilityAdvertisement:
    """One host-level capability advertisement published during handshake."""

    capability_id: str
    state: ServiceHostCapabilityState = ServiceHostCapabilityState.available
    detail_payload: object | None = None


@dataclass(frozen=True, slots=True)
class ServiceHostHandshakeResponse:
    """Typed standalone Service host handshake response."""

    endpoint: DuplexIpcEndpoint
    protocol_version: str
    host_id: str
    host_version: str | None
    readiness: ServiceHostReadiness
    capabilities: tuple[ServiceHostCapabilityAdvertisement, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceStreamSession:
    """Service-owned semantic session for one live stream relation."""

    session_id: UUID
    request: ServiceOperationRequest
    publisher_id: str | None = None
    subscriber_id: str | None = None


@dataclass(frozen=True, slots=True)
class ServiceStreamControlRequest:
    """Semantic control request over one Service stream session."""

    session_id: UUID
    kind: ServiceStreamControlKind
    reason: str | None = None
    detail_payload: object | None = None


@dataclass(frozen=True, slots=True)
class ServiceStreamControlResponse:
    """Semantic outcome for one Service stream control request."""

    session_id: UUID
    kind: ServiceStreamControlKind
    status: RequestStatus
    error: str | None = None
    detail_payload: object | None = None


@dataclass(frozen=True, slots=True)
class ServiceStreamEventEnvelope:
    """Service-owned semantic stream event envelope.

    Payload DTO truth remains API-owned. Service owns only sequencing,
    item identity, session correlation, and semantic event category.
    """

    session: ServiceStreamSession
    sequence: int
    kind: ServiceStreamEventKind
    item_key: str
    payload: object | None = None


@dataclass(frozen=True, slots=True)
class ServiceLaneSubscriptionBinding:
    """Resolved lane subscription bound to one hosted service instance."""

    service_branch_id: UUID
    service_config_api_projection_id: UUID
    api_graph_projection_id: UUID
    object_instance_graph_branch_id: UUID
    branch_id: UUID
    projection_hash: str


class ServiceOperationResult(ServiceOperationResponse):
    """Legacy compatibility result used by Environment-hosted service plugins."""

    response_service_operation: SerializeAsAny[EnvironmentServiceOperation] | None = (
        None
    )

    @model_validator(mode="after")
    def _sync_response_payload(self) -> "ServiceOperationResult":
        payload = self.response_payload
        response_service_operation = self.response_service_operation
        if payload is None and response_service_operation is not None:
            self.response_payload = cast(
                JsonValue,
                response_service_operation.model_dump(mode="json"),
            )
            return self
        if payload is not None and response_service_operation is None:
            if isinstance(payload, EnvironmentServiceOperation):
                self.response_service_operation = payload
                return self
            if isinstance(payload, dict):
                self.response_service_operation = (
                    EnvironmentServiceOperation.model_validate(payload)
                )
                return self
            return self
        if payload is not None and response_service_operation is not None:
            if payload == response_service_operation.model_dump(mode="json"):
                return self
            raise TypeError(
                "ServiceOperationResult received mismatched response_payload and "
                "response_service_operation values."
            )
        return self


@dataclass(frozen=True, slots=True)
class ServiceOperationInvocation:
    """Legacy Environment-shaped invocation payload preserved for compatibility."""

    env_req: EnvironmentServiceOperationRequest
    stream_target_id: UUID | None = None
    stream_correlation_id: UUID | None = None
    network_request_id: UUID | None = None

    @property
    def context(self) -> EnvironmentOperationContext:
        return EnvironmentOperationContext(
            actor_id=self.env_req.actor_id,
            environment_id=self.env_req.environment_id,
            process_id=self.env_req.process_id,
            thread_id=self.env_req.thread_id,
            branch_id=self.env_req.branch_id,
            projection_hash=self.env_req.projection_hash,
        )

    @property
    def service_context(self) -> ServiceOperationContext:
        return ServiceOperationContext(
            actor_id=self.env_req.actor_id,
            branch_id=cast(UUID, self.env_req.branch_id),
            projection_hash=cast(str, self.env_req.projection_hash),
        )

    @property
    def request(self) -> ServiceOperationRequest:
        return ServiceOperationRequest(
            context=self.service_context,
            service=self.env_req.service_operation.service,
            operation=self.env_req.service_operation.model_dump(mode="json"),
            stream_target_id=self.stream_target_id,
            stream_correlation_id=self.stream_correlation_id,
            network_request_id=self.network_request_id,
        )


class ServiceHostTransport(Protocol):
    async def send_service_response(
        self,
        *,
        request: ServiceOperationRequest,
        response: ServiceOperationResponse,
    ) -> None: ...

    async def close_service_stream(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> None: ...

    async def get_graph_gateway(self) -> ServiceGraphGateway:
        """Return the host-selected graph invocation backend."""
        ...

    async def get_meta_temporal_graph_route(self) -> "MetaTemporalGraphRoute":
        """Return the host-selected Meta temporal overlay invocation route."""
        ...


class ServiceOperationTransport(ServiceHostTransport, Protocol):
    """Environment-compatibility extension over the canonical host transport.

    New Environment-bound imports should prefer
    `aware_service_runtime.adapters.environment.EnvironmentServiceTransport`
    so this protocol stops reading like a generic shared host contract.
    """

    async def send_service_operation_stream(
        self,
        *,
        node_id: UUID,
        network_operation_id: UUID,
        env_req: EnvironmentServiceOperationRequest,
        service_operation: EnvironmentServiceOperation,
    ) -> None: ...

    async def close_stream(
        self,
        *,
        node_id: UUID,
        network_operation_id: UUID,
        env_req: EnvironmentServiceOperationRequest,
    ) -> None: ...


class ServiceGraphGateway(Protocol):
    """Canonical graph invocation route consumed by service handlers."""

    async def invoke_function(
        self,
        *,
        request: MetaGraphInvokeFunctionRequest,
        graph_context: "ServiceGraphContextLike | None" = None,
    ) -> MetaGraphInvokeFunctionResponse:
        """Invoke one canonical function request against the hosted runtime."""
        ...


class MetaTemporalGraphRoute(Protocol):
    """Explicit Meta SDK route for non-committing temporal graph invocations."""

    async def invoke_temporal_function(self, **kwargs: object) -> object:
        """Invoke one temporal overlay function through the Meta boundary."""
        ...


class ServiceStreamPublisher(Protocol):
    """Publisher-side port for opening and controlling stream sessions."""

    async def open_stream_session(
        self,
        *,
        session: ServiceStreamSession,
    ) -> ServiceStreamControlResponse: ...

    async def send_stream_control(
        self,
        *,
        request: ServiceStreamControlRequest,
    ) -> ServiceStreamControlResponse: ...


class ServiceStreamSubscriber(Protocol):
    """Subscriber-side port for handling stream control requests."""

    async def handle_stream_control(
        self,
        *,
        request: ServiceStreamControlRequest,
    ) -> ServiceStreamControlResponse: ...


class ServiceOperationHandler(Protocol):
    """Canonical host-neutral service-operation protocol."""

    service: str

    async def handle_request(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> ServiceOperationResponse: ...

    async def handle_notification(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> None: ...


class ServiceOperationInvocationHandler(Protocol):
    """Legacy Environment-hosted service-operation plugin protocol."""

    service: str

    async def handle_request(
        self,
        *,
        invocation: ServiceOperationInvocation,
    ) -> ServiceOperationResult: ...

    async def handle_notification(
        self,
        *,
        invocation: ServiceOperationInvocation,
    ) -> None: ...


ServiceOperationPluginHandler = (
    ServiceOperationHandler | ServiceOperationInvocationHandler
)
