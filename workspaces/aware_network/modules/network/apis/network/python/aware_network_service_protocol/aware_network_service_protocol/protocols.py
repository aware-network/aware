# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_network_service_dto.comms.models.network_service import (
    NetworkDiscoverExperienceTerritoryRequest,
    NetworkDiscoverExperienceTerritoryResponse,
    NetworkDiscoverTerritoryRequest,
    NetworkDiscoverTerritoryResponse,
    NetworkListEnvironmentsRequest,
    NetworkListEnvironmentsResponse,
    NetworkListHostedServicesRequest,
    NetworkListHostedServicesResponse,
    NetworkListPeersRequest,
    NetworkListPeersResponse,
    NetworkReconcileNodePublicationRequest,
    NetworkReconcileNodePublicationResponse,
    NetworkResolveHostedServiceRoutesRequest,
    NetworkResolveHostedServiceRoutesResponse,
    NetworkUpsertPeerRequest,
    NetworkUpsertPeerResponse,
)

API_PACKAGE_NAME: Final[str] = "network-service-api"
API_FQN_PREFIX: Final[str] = "aware_network_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_network_service_api"


@dataclass(frozen=True, slots=True)
class ServiceProtocolFulfillmentBinding:
    name: str
    graph_target: str
    graph_capability_function_name: str
    graph_function_python_ref: str
    method_name: str
    request_type_ref: str
    response_type_ref: str


class ServiceProtocolExecutionBackend(Protocol):
    async def invoke_fulfillment(
        self,
        *,
        fulfillment_name: str,
        request: BaseModel,
    ) -> object | None: ...


class ServiceProtocolExecution(Protocol):
    pass


ServiceProtocolExecutionFactory: TypeAlias = Callable[[ServiceProtocolExecutionBackend], ServiceProtocolExecution]

ServiceProtocolInvoker: TypeAlias = Callable[
    [object, BaseModel, ServiceProtocolExecution | None], Awaitable[object | None]
]

ServiceProtocolStreamInvoker: TypeAlias = Callable[
    [object, BaseModel, ServiceProtocolExecution | None], AsyncIterator[object]
]


def _coerce_model_payload(value: object, *, model_cls: type[BaseModel]) -> object:
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json")
    else:
        payload = value
    required_fields = [name for name, field in model_cls.model_fields.items() if field.is_required()]
    if len(required_fields) == 1:
        field_name = required_fields[0]
        if isinstance(payload, dict) and field_name in payload:
            return payload
        return {field_name: payload}
    return payload


@dataclass(frozen=True, slots=True)
class ServiceProtocolEndpointBinding:
    endpoint_ref: str
    api_name: str
    capability_name: str
    endpoint_name: str
    request_type_ref: str
    response_type_ref: str | None
    stream_event_type_refs: tuple[str, ...]
    execution_protocol_ref: str | None
    build_execution: ServiceProtocolExecutionFactory | None
    stream_invoke: ServiceProtocolStreamInvoker | None
    fulfillment_bindings: tuple[ServiceProtocolFulfillmentBinding, ...]
    invoke: ServiceProtocolInvoker


async def invoke_network__discovery__discover_experience_territory(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NetworkDiscoverExperienceTerritoryResponse:
    typed_handler = cast(AwareNetworkServiceProtocol, handler)
    typed_request = NetworkDiscoverExperienceTerritoryRequest.model_validate(request)
    return await typed_handler.network.discovery.discover_experience_territory(typed_request)


NETWORK__DISCOVERY__DISCOVER_EXPERIENCE_TERRITORY_ENDPOINT_REF: Final[str] = (
    "network.discovery.discover_experience_territory"
)
NETWORK__DISCOVERY__DISCOVER_EXPERIENCE_TERRITORY_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=NETWORK__DISCOVERY__DISCOVER_EXPERIENCE_TERRITORY_ENDPOINT_REF,
        api_name="network",
        capability_name="discovery",
        endpoint_name="discover_experience_territory",
        request_type_ref="aware_network_service_dto.comms.models.NetworkDiscoverExperienceTerritoryRequest",
        response_type_ref="aware_network_service_dto.comms.models.NetworkDiscoverExperienceTerritoryResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_network__discovery__discover_experience_territory,
    )
)


async def invoke_network__discovery__discover_territory(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NetworkDiscoverTerritoryResponse:
    typed_handler = cast(AwareNetworkServiceProtocol, handler)
    typed_request = NetworkDiscoverTerritoryRequest.model_validate(request)
    return await typed_handler.network.discovery.discover_territory(typed_request)


NETWORK__DISCOVERY__DISCOVER_TERRITORY_ENDPOINT_REF: Final[str] = "network.discovery.discover_territory"
NETWORK__DISCOVERY__DISCOVER_TERRITORY_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=NETWORK__DISCOVERY__DISCOVER_TERRITORY_ENDPOINT_REF,
        api_name="network",
        capability_name="discovery",
        endpoint_name="discover_territory",
        request_type_ref="aware_network_service_dto.comms.models.NetworkDiscoverTerritoryRequest",
        response_type_ref="aware_network_service_dto.comms.models.NetworkDiscoverTerritoryResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_network__discovery__discover_territory,
    )
)


async def invoke_network__environment__list(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NetworkListEnvironmentsResponse:
    typed_handler = cast(AwareNetworkServiceProtocol, handler)
    typed_request = NetworkListEnvironmentsRequest.model_validate(request)
    return await typed_handler.network.environment.list(typed_request)


NETWORK__ENVIRONMENT__LIST_ENDPOINT_REF: Final[str] = "network.environment.list"
NETWORK__ENVIRONMENT__LIST_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=NETWORK__ENVIRONMENT__LIST_ENDPOINT_REF,
    api_name="network",
    capability_name="environment",
    endpoint_name="list",
    request_type_ref="aware_network_service_dto.comms.models.NetworkListEnvironmentsRequest",
    response_type_ref="aware_network_service_dto.comms.models.NetworkListEnvironmentsResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_network__environment__list,
)


async def invoke_network__hosted_service__list(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NetworkListHostedServicesResponse:
    typed_handler = cast(AwareNetworkServiceProtocol, handler)
    typed_request = NetworkListHostedServicesRequest.model_validate(request)
    return await typed_handler.network.hosted_service.list(typed_request)


NETWORK__HOSTED_SERVICE__LIST_ENDPOINT_REF: Final[str] = "network.hosted_service.list"
NETWORK__HOSTED_SERVICE__LIST_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=NETWORK__HOSTED_SERVICE__LIST_ENDPOINT_REF,
    api_name="network",
    capability_name="hosted_service",
    endpoint_name="list",
    request_type_ref="aware_network_service_dto.comms.models.NetworkListHostedServicesRequest",
    response_type_ref="aware_network_service_dto.comms.models.NetworkListHostedServicesResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_network__hosted_service__list,
)


async def invoke_network__peer__list(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NetworkListPeersResponse:
    typed_handler = cast(AwareNetworkServiceProtocol, handler)
    typed_request = NetworkListPeersRequest.model_validate(request)
    return await typed_handler.network.peer.list(typed_request)


NETWORK__PEER__LIST_ENDPOINT_REF: Final[str] = "network.peer.list"
NETWORK__PEER__LIST_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=NETWORK__PEER__LIST_ENDPOINT_REF,
    api_name="network",
    capability_name="peer",
    endpoint_name="list",
    request_type_ref="aware_network_service_dto.comms.models.NetworkListPeersRequest",
    response_type_ref="aware_network_service_dto.comms.models.NetworkListPeersResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_network__peer__list,
)


async def invoke_network__peer__upsert(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NetworkUpsertPeerResponse:
    typed_handler = cast(AwareNetworkServiceProtocol, handler)
    typed_request = NetworkUpsertPeerRequest.model_validate(request)
    return await typed_handler.network.peer.upsert(typed_request)


NETWORK__PEER__UPSERT_ENDPOINT_REF: Final[str] = "network.peer.upsert"
NETWORK__PEER__UPSERT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=NETWORK__PEER__UPSERT_ENDPOINT_REF,
    api_name="network",
    capability_name="peer",
    endpoint_name="upsert",
    request_type_ref="aware_network_service_dto.comms.models.NetworkUpsertPeerRequest",
    response_type_ref="aware_network_service_dto.comms.models.NetworkUpsertPeerResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_network__peer__upsert,
)


async def invoke_network__publication__reconcile_node_publication(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NetworkReconcileNodePublicationResponse:
    typed_handler = cast(AwareNetworkServiceProtocol, handler)
    typed_request = NetworkReconcileNodePublicationRequest.model_validate(request)
    return await typed_handler.network.publication.reconcile_node_publication(typed_request)


NETWORK__PUBLICATION__RECONCILE_NODE_PUBLICATION_ENDPOINT_REF: Final[str] = (
    "network.publication.reconcile_node_publication"
)
NETWORK__PUBLICATION__RECONCILE_NODE_PUBLICATION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=NETWORK__PUBLICATION__RECONCILE_NODE_PUBLICATION_ENDPOINT_REF,
        api_name="network",
        capability_name="publication",
        endpoint_name="reconcile_node_publication",
        request_type_ref="aware_network_service_dto.comms.models.NetworkReconcileNodePublicationRequest",
        response_type_ref="aware_network_service_dto.comms.models.NetworkReconcileNodePublicationResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_network__publication__reconcile_node_publication,
    )
)


async def invoke_network__route__resolve_hosted_service_routes(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NetworkResolveHostedServiceRoutesResponse:
    typed_handler = cast(AwareNetworkServiceProtocol, handler)
    typed_request = NetworkResolveHostedServiceRoutesRequest.model_validate(request)
    return await typed_handler.network.route.resolve_hosted_service_routes(typed_request)


NETWORK__ROUTE__RESOLVE_HOSTED_SERVICE_ROUTES_ENDPOINT_REF: Final[str] = "network.route.resolve_hosted_service_routes"
NETWORK__ROUTE__RESOLVE_HOSTED_SERVICE_ROUTES_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=NETWORK__ROUTE__RESOLVE_HOSTED_SERVICE_ROUTES_ENDPOINT_REF,
        api_name="network",
        capability_name="route",
        endpoint_name="resolve_hosted_service_routes",
        request_type_ref="aware_network_service_dto.comms.models.NetworkResolveHostedServiceRoutesRequest",
        response_type_ref="aware_network_service_dto.comms.models.NetworkResolveHostedServiceRoutesResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_network__route__resolve_hosted_service_routes,
    )
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    NETWORK__DISCOVERY__DISCOVER_EXPERIENCE_TERRITORY_ENDPOINT_REF: NETWORK__DISCOVERY__DISCOVER_EXPERIENCE_TERRITORY_PROTOCOL_BINDING,
    NETWORK__DISCOVERY__DISCOVER_TERRITORY_ENDPOINT_REF: NETWORK__DISCOVERY__DISCOVER_TERRITORY_PROTOCOL_BINDING,
    NETWORK__ENVIRONMENT__LIST_ENDPOINT_REF: NETWORK__ENVIRONMENT__LIST_PROTOCOL_BINDING,
    NETWORK__HOSTED_SERVICE__LIST_ENDPOINT_REF: NETWORK__HOSTED_SERVICE__LIST_PROTOCOL_BINDING,
    NETWORK__PEER__LIST_ENDPOINT_REF: NETWORK__PEER__LIST_PROTOCOL_BINDING,
    NETWORK__PEER__UPSERT_ENDPOINT_REF: NETWORK__PEER__UPSERT_PROTOCOL_BINDING,
    NETWORK__PUBLICATION__RECONCILE_NODE_PUBLICATION_ENDPOINT_REF: NETWORK__PUBLICATION__RECONCILE_NODE_PUBLICATION_PROTOCOL_BINDING,
    NETWORK__ROUTE__RESOLVE_HOSTED_SERVICE_ROUTES_ENDPOINT_REF: NETWORK__ROUTE__RESOLVE_HOSTED_SERVICE_ROUTES_PROTOCOL_BINDING,
}


class NetworkDiscoveryCapabilityServiceProtocol(Protocol):

    async def discover_experience_territory(
        self, request: NetworkDiscoverExperienceTerritoryRequest
    ) -> NetworkDiscoverExperienceTerritoryResponse: ...

    async def discover_territory(
        self, request: NetworkDiscoverTerritoryRequest
    ) -> NetworkDiscoverTerritoryResponse: ...


class NetworkEnvironmentCapabilityServiceProtocol(Protocol):

    async def list(self, request: NetworkListEnvironmentsRequest) -> NetworkListEnvironmentsResponse: ...


class NetworkHostedServiceCapabilityServiceProtocol(Protocol):

    async def list(self, request: NetworkListHostedServicesRequest) -> NetworkListHostedServicesResponse: ...


class NetworkPeerCapabilityServiceProtocol(Protocol):

    async def list(self, request: NetworkListPeersRequest) -> NetworkListPeersResponse: ...

    async def upsert(self, request: NetworkUpsertPeerRequest) -> NetworkUpsertPeerResponse: ...


class NetworkPublicationCapabilityServiceProtocol(Protocol):

    async def reconcile_node_publication(
        self, request: NetworkReconcileNodePublicationRequest
    ) -> NetworkReconcileNodePublicationResponse: ...


class NetworkRouteCapabilityServiceProtocol(Protocol):

    async def resolve_hosted_service_routes(
        self, request: NetworkResolveHostedServiceRoutesRequest
    ) -> NetworkResolveHostedServiceRoutesResponse: ...


class NetworkApiServiceProtocol(Protocol):
    discovery: NetworkDiscoveryCapabilityServiceProtocol
    environment: NetworkEnvironmentCapabilityServiceProtocol
    hosted_service: NetworkHostedServiceCapabilityServiceProtocol
    peer: NetworkPeerCapabilityServiceProtocol
    publication: NetworkPublicationCapabilityServiceProtocol
    route: NetworkRouteCapabilityServiceProtocol


class AwareNetworkServiceProtocol(Protocol):
    network: NetworkApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:15e146cf7f6ca6f27c74b4a83c34def49732b1d8c7adc950ad1736c243d73c0c",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 36,'
    '  "sections": ['
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:cd8d708176fc929a8ede9d10b0d985542bbadd8d92dcceb9716b7439bca125e5",'
    '      "section_key": "api.service_protocol.module_prelude",'
    '      "section_kind": "service_protocol_module_prelude",'
    '      "section_order": 0'
    "    },"
    "    {"
    '      "line_count": 59,'
    '      "rendered_text_digest": "sha256:4b2f83676760964f04df5a2dfd6a8153e0c286051f2d85dd83b8e2e933b411d7",'
    '      "section_key": "api.service_protocol.runtime_support",'
    '      "section_kind": "service_protocol_runtime_support",'
    '      "section_order": 1'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:network.discovery.discover_experience_territory",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:network.discovery.discover_territory",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:network.environment.list",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:network.hosted_service.list",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:network.peer.list",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:network.peer.upsert",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:network.publication.reconcile_node_publication",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:network.route.resolve_hosted_service_routes",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:f2c70a6908461968e230e2540aa93b8e1f9b27eeadba386055baa3fe09a0996c",'
    '      "section_key": "api.service_protocol.endpoint_invoker:network.discovery.discover_experience_territory",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:e053464cc0b25a305df1cbae852b190e77186833c916d32f12606cdc3d6b9ef6",'
    '      "section_key": "api.service_protocol.endpoint_binding:network.discovery.discover_experience_territory",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:5e7036771113ada4a5b9fc47ce3af6b07e02f8f6c16116064ae620e3528472c0",'
    '      "section_key": "api.service_protocol.endpoint_invoker:network.discovery.discover_territory",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:93420042a18bbd09ea549f2626c71326edaf672e85a8ee7dcfaf3a168f47f512",'
    '      "section_key": "api.service_protocol.endpoint_binding:network.discovery.discover_territory",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:1c4fb19025ddd5291a8edd706a093ff0bb68b95578ff3daa5cfc018e2d64b238",'
    '      "section_key": "api.service_protocol.endpoint_invoker:network.environment.list",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:922f9bc196ff911a21b356ab2da5c28d62a6b3549a3e5a12cfe0c4d957eba8e4",'
    '      "section_key": "api.service_protocol.endpoint_binding:network.environment.list",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:bc4c18191ab13e59e2e3101e5a83d8f4fc71382a9d6c364c8c5edd3052329342",'
    '      "section_key": "api.service_protocol.endpoint_invoker:network.hosted_service.list",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:e47abad5642143b94c3d534c8e5a37d880a761ff473f7743c95fc38f47c9dda5",'
    '      "section_key": "api.service_protocol.endpoint_binding:network.hosted_service.list",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:b5126741f800729d383d78873a86f11a401046d110f6a21324d313f7fc1fbc41",'
    '      "section_key": "api.service_protocol.endpoint_invoker:network.peer.list",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:c6077aaf874f460b4469994944c418d213079e7566c95040755d194385b95043",'
    '      "section_key": "api.service_protocol.endpoint_binding:network.peer.list",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:4247d0c3e8710d7b77658361f006f7cf4455766ba7a3b9215bd16b34632df26f",'
    '      "section_key": "api.service_protocol.endpoint_invoker:network.peer.upsert",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:28a26d02c2882df2a1ea15f8e46c5621e0c2dc8b4fb57cb2fd817f860b8bebcc",'
    '      "section_key": "api.service_protocol.endpoint_binding:network.peer.upsert",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ca7da97d78919bcf365fa7b0f1db7ca6cf008d69965deb40cec927503f950630",'
    '      "section_key": "api.service_protocol.endpoint_invoker:network.publication.reconcile_node_publication",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:b56f41f201a76033c88058cc127e173bfcc210ffd69cf979d999650036721e52",'
    '      "section_key": "api.service_protocol.endpoint_binding:network.publication.reconcile_node_publication",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e5a4a04491d739a08ff05430ab42ee3d19e94362399a69de5db9dd2e0e2a2133",'
    '      "section_key": "api.service_protocol.endpoint_invoker:network.route.resolve_hosted_service_routes",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:655dfe0e6b91e5644cf2614c82c5f49c45fccef6a64c006bc1a65a8c08c10583",'
    '      "section_key": "api.service_protocol.endpoint_binding:network.route.resolve_hosted_service_routes",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 11,'
    '      "rendered_text_digest": "sha256:b0c1739bea5d29cb4d196f231866428616649f4b532ad97b716f1128a05c91c5",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:5393d6a39befef63c6847fee4ace5c77a2a49431080281940badd3a528aa263c",'
    '      "section_key": "api.service_protocol.capability_protocol:network.discovery",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:6f5a8a6f418acf09a1726293b12aaa4c855fe9555aed9ba1c5b83fc1b13ffcac",'
    '      "section_key": "api.service_protocol.capability_protocol:network.environment",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:bc22eb4965c7571a3996a82eb1564191da089a3f0e6d4549ae7e62abe6c33f2c",'
    '      "section_key": "api.service_protocol.capability_protocol:network.hosted_service",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:42e4a15c252d7a08639a09d98f019899d25913cae73c0ba2b9b4e33d2528f96f",'
    '      "section_key": "api.service_protocol.capability_protocol:network.peer",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 30'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:e7bcc3ed93a267856a848ffa8cf1540226a5464bb4ed8dccbcf62966f5fb00bd",'
    '      "section_key": "api.service_protocol.capability_protocol:network.publication",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 31'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:5da20636235eb2362d0e62e0cdf248417f4c897d8f12997b6c67a3b2d6bb0201",'
    '      "section_key": "api.service_protocol.capability_protocol:network.route",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 32'
    "    },"
    "    {"
    '      "line_count": 8,'
    '      "rendered_text_digest": "sha256:9a3719b64b79ad9acbbb30caa99601048dd20ab17c65fccfad3d047341318d54",'
    '      "section_key": "api.service_protocol.api_protocol:network",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 33'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:4f4243c0d0b213e5c851f60c226cc1fdf5c3828beb73d2ff2ff38eac53287ba3",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 34'
    "    },"
    "    {"
    '      "line_count": 46,'
    '      "rendered_text_digest": "sha256:f95dd976c0673da7a840fbd55585bded2e6259a9c28690bf265401d80d155525",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 35'
    "    }"
    "  ],"
    '  "target_relpath": "protocols.py",'
    '  "text_digest_algorithm": "sha256"'
    "}"
)

__all__ = [
    "API_FQN_PREFIX",
    "API_PACKAGE_NAME",
    "ENDPOINT_BINDINGS",
    "PUBLIC_PACKAGE_IMPORT_ROOT",
    "SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON",
    "ServiceProtocolExecutionBackend",
    "ServiceProtocolExecutionFactory",
    "ServiceProtocolEndpointBinding",
    "ServiceProtocolFulfillmentBinding",
    "ServiceProtocolInvoker",
    "ServiceProtocolStreamInvoker",
    "AwareNetworkServiceProtocol",
    "NetworkApiServiceProtocol",
    "NetworkDiscoveryCapabilityServiceProtocol",
    "NetworkEnvironmentCapabilityServiceProtocol",
    "NetworkHostedServiceCapabilityServiceProtocol",
    "NetworkPeerCapabilityServiceProtocol",
    "NetworkPublicationCapabilityServiceProtocol",
    "NetworkRouteCapabilityServiceProtocol",
    "NETWORK__DISCOVERY__DISCOVER_EXPERIENCE_TERRITORY_ENDPOINT_REF",
    "NETWORK__DISCOVERY__DISCOVER_EXPERIENCE_TERRITORY_PROTOCOL_BINDING",
    "invoke_network__discovery__discover_experience_territory",
    "NETWORK__DISCOVERY__DISCOVER_TERRITORY_ENDPOINT_REF",
    "NETWORK__DISCOVERY__DISCOVER_TERRITORY_PROTOCOL_BINDING",
    "invoke_network__discovery__discover_territory",
    "NETWORK__ENVIRONMENT__LIST_ENDPOINT_REF",
    "NETWORK__ENVIRONMENT__LIST_PROTOCOL_BINDING",
    "invoke_network__environment__list",
    "NETWORK__HOSTED_SERVICE__LIST_ENDPOINT_REF",
    "NETWORK__HOSTED_SERVICE__LIST_PROTOCOL_BINDING",
    "invoke_network__hosted_service__list",
    "NETWORK__PEER__LIST_ENDPOINT_REF",
    "NETWORK__PEER__LIST_PROTOCOL_BINDING",
    "invoke_network__peer__list",
    "NETWORK__PEER__UPSERT_ENDPOINT_REF",
    "NETWORK__PEER__UPSERT_PROTOCOL_BINDING",
    "invoke_network__peer__upsert",
    "NETWORK__PUBLICATION__RECONCILE_NODE_PUBLICATION_ENDPOINT_REF",
    "NETWORK__PUBLICATION__RECONCILE_NODE_PUBLICATION_PROTOCOL_BINDING",
    "invoke_network__publication__reconcile_node_publication",
    "NETWORK__ROUTE__RESOLVE_HOSTED_SERVICE_ROUTES_ENDPOINT_REF",
    "NETWORK__ROUTE__RESOLVE_HOSTED_SERVICE_ROUTES_PROTOCOL_BINDING",
    "invoke_network__route__resolve_hosted_service_routes",
]
