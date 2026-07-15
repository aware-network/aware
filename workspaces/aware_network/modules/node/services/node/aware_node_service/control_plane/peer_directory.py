from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse
from uuid import UUID, uuid4

from aware_code.types import JsonArray, JsonObject
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentConfigRequest,
    FetchCapabilitiesRequest,
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
)
from aware_network_service_dto.comms.models.network import (
    NetworkAppType,
    NetworkOperation,
    NetworkOperationHop,
    NetworkOperationMessageType,
    NetworkOperationType,
    NetworkRequest,
    NetworkRequestStatus,
)
from aware_network_service_dto.comms.models.network_node import (
    BootEnvironmentDescriptor,
    DiscoverHostedServicesRequest,
    DiscoverHostedServicesResponse,
    GetBootEnvironmentDescriptorRequest,
    GetBootEnvironmentDescriptorResponse,
    HostedServiceAdvertisement,
    NetworkNodeOperation,
)
from aware_network.communications.app import NetworkApp
from aware_network.network.node.manager import network_node_manager
from aware_network_ontology.stable_ids import stable_network_node_peer_id
from aware_network_sdk import NetworkSdkClient
from aware_network_service_dto.comms.models.network_service import (
    NetworkResolvedHostedServiceRoute,
)

from aware_utils.logging import logger

from aware_node_service.control_plane.environment_host_support import (
    EnvironmentRouteHandler,
)
from aware_node_service.control_plane.environment_api_network import (
    build_environment_service_api_client,
    invoke_environment_service_api_request,
)
from aware_node_service.control_plane.hosted_environment_service import (
    NetworkNodeHostedEnvironmentService,
)


@dataclass(frozen=True)
class NetworkNodePeerEndpoint:
    node_id: UUID
    base_url: str


@dataclass(frozen=True)
class RemoteHostedServiceRoute:
    peer: NetworkNodePeerEndpoint
    advertisement: HostedServiceAdvertisement


@dataclass(frozen=True)
class _BootNetworkNodeTargets:
    environment_id: UUID
    process_id: UUID
    thread_id: UUID
    projection_graph_id: UUID
    projection_hash: str
    list_peers_function_id: UUID


class _NetworkNodePeerDiscoveryUnavailable(RuntimeError):
    """Raised when the boot environment has no local peer directory surface."""


def _normalize_service_name(service_name: str) -> str:
    return service_name.strip().casefold()


def _normalize_endpoint_ref(endpoint_ref: str) -> str:
    return endpoint_ref.strip().casefold()


def _resolve_matching_remote_hosted_service_advertisement_for_service_name(
    *,
    peer_node_id: UUID,
    advertisements: tuple[HostedServiceAdvertisement, ...],
    service_name: str,
) -> HostedServiceAdvertisement | None:
    normalized_service_name = _normalize_service_name(service_name)
    if not normalized_service_name:
        return None

    matches = tuple(
        advertisement
        for advertisement in advertisements
        if _normalize_service_name(advertisement.service_name)
        == normalized_service_name
    )
    if not matches:
        return None
    if len(matches) != 1:
        raise RuntimeError(
            "Remote Node peer "
            f"{peer_node_id} advertised duplicate hosted service_name "
            f"{service_name!r}"
        )

    match = matches[0]
    if match.service_id is None:
        raise RuntimeError(
            "Remote Node peer "
            f"{peer_node_id} advertised hosted service {service_name!r} "
            "without committed service_id"
        )
    return match


def _resolve_matching_remote_hosted_service_advertisement_for_endpoint_ref(
    *,
    peer_node_id: UUID,
    advertisements: tuple[HostedServiceAdvertisement, ...],
    endpoint_ref: str,
) -> HostedServiceAdvertisement | None:
    normalized_endpoint_ref = _normalize_endpoint_ref(endpoint_ref)
    if not normalized_endpoint_ref:
        return None

    matches = tuple(
        advertisement
        for advertisement in advertisements
        if normalized_endpoint_ref
        in {
            _normalize_endpoint_ref(advertised_endpoint_ref)
            for advertised_endpoint_ref in advertisement.endpoint_refs
            if _normalize_endpoint_ref(advertised_endpoint_ref)
        }
    )
    if not matches:
        return None
    if len(matches) != 1:
        raise RuntimeError(
            "Remote Node peer "
            f"{peer_node_id} advertised duplicate hosted endpoint_ref "
            f"{endpoint_ref!r}"
        )

    match = matches[0]
    if match.service_id is None:
        raise RuntimeError(
            "Remote Node peer "
            f"{peer_node_id} advertised hosted endpoint_ref {endpoint_ref!r} "
            "without committed service_id"
        )
    return match


def _normalize_node_endpoint(endpoint: str) -> str:
    normalized = endpoint.strip()
    if not normalized:
        return normalized

    if normalized.startswith("http://"):
        normalized = "ws://" + normalized[len("http://") :]
    elif normalized.startswith("https://"):
        normalized = "wss://" + normalized[len("https://") :]

    trimmed = normalized.rstrip("/")
    for suffix in ("/interface/network_node", "/network_node/network_node"):
        if trimmed.endswith(suffix):
            trimmed = trimmed[: -len(suffix)]
            break
    trimmed = trimmed.rstrip("/")

    parsed = urlparse(trimmed)
    if parsed.scheme and parsed.netloc:
        trimmed = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
    return trimmed.rstrip("/")


def _hosted_service_advertisement_from_network_route(
    route: NetworkResolvedHostedServiceRoute,
) -> HostedServiceAdvertisement:
    hosted_service = route.hosted_service
    return HostedServiceAdvertisement(
        service_package_id=hosted_service.service_package_id,
        service_id=hosted_service.service_id,
        service_name=hosted_service.service_name,
        service_package_names=list(hosted_service.service_package_names),
        endpoint_refs=list(hosted_service.endpoint_refs),
        host_id=hosted_service.host_id,
        host_version=hosted_service.host_version,
        protocol_version=hosted_service.protocol_version,
        supports_stream_events=hosted_service.supports_stream_events,
    )


def _remote_hosted_service_route_from_network_route(
    route: NetworkResolvedHostedServiceRoute,
) -> RemoteHostedServiceRoute:
    return RemoteHostedServiceRoute(
        peer=NetworkNodePeerEndpoint(
            node_id=route.provider_node_id,
            base_url=_normalize_node_endpoint(route.provider_node_base_url),
        ),
        advertisement=_hosted_service_advertisement_from_network_route(route),
    )


async def discover_remote_hosted_service_advertisements_from_peer(
    *,
    network_app: NetworkApp,
    peer: NetworkNodePeerEndpoint,
    route_connection_id: UUID | None = None,
    actor_id: UUID | None = None,
    timeout_s: float = 5.0,
) -> tuple[HostedServiceAdvertisement, ...]:
    local_node_id = network_node_manager.hosted_node_id
    connection_id = route_connection_id or stable_network_node_peer_id(
        source_peer_node_id=local_node_id,
        target_peer_node_id=peer.node_id,
    )
    duplex = network_app.get_duplex_client(NetworkAppType.network_node)
    await duplex.ensure_connection(
        connection_id=connection_id,
        external_url=peer.base_url,
    )
    request_op = NetworkOperation(
        id=uuid4(),
        message_type=NetworkOperationMessageType.request,
        type=NetworkOperationType.network_node,
        network_request=NetworkRequest(
            id=uuid4(),
            status=NetworkRequestStatus.pending,
            requester_id=actor_id,
            requester=None,
        ),
        network_node_operation=NetworkNodeOperation(
            request=DiscoverHostedServicesRequest(
                actor_id=actor_id,
                operation="discover_hosted_services",
            )
        ),
        network_operation_hop_list=[
            NetworkOperationHop(
                source_app_type=NetworkAppType.network_node,
                source_node_id=local_node_id,
                target_app_type=NetworkAppType.network_node,
                target_node_id=peer.node_id,
            )
        ],
    )
    raw = await duplex.send_request(
        connection_id=connection_id,
        data_serialized=request_op.model_dump_json(),
        timeout_s=timeout_s,
    )
    if raw is None:
        return ()
    response = (
        NetworkOperation.model_validate_json(raw)
        if isinstance(raw, str)
        else NetworkOperation.model_validate(raw)
    )
    if (
        response.network_response is None
        or response.network_response.status is not NetworkRequestStatus.succeeded
        or response.network_node_operation is None
        or not isinstance(
            response.network_node_operation.response,
            DiscoverHostedServicesResponse,
        )
    ):
        return ()
    return tuple(response.network_node_operation.response.hosted_services)


async def read_remote_boot_environment_descriptor_from_peer(
    *,
    network_app: NetworkApp,
    peer: NetworkNodePeerEndpoint,
    route_connection_id: UUID | None = None,
    actor_id: UUID | None = None,
    timeout_s: float = 5.0,
) -> BootEnvironmentDescriptor | None:
    local_node_id = network_node_manager.hosted_node_id
    connection_id = route_connection_id or stable_network_node_peer_id(
        source_peer_node_id=local_node_id,
        target_peer_node_id=peer.node_id,
    )
    duplex = network_app.get_duplex_client(NetworkAppType.network_node)
    await duplex.ensure_connection(
        connection_id=connection_id,
        external_url=peer.base_url,
    )
    request_op = NetworkOperation(
        id=uuid4(),
        message_type=NetworkOperationMessageType.request,
        type=NetworkOperationType.network_node,
        network_request=NetworkRequest(
            id=uuid4(),
            status=NetworkRequestStatus.pending,
            requester_id=actor_id,
            requester=None,
        ),
        network_node_operation=NetworkNodeOperation(
            request=GetBootEnvironmentDescriptorRequest(
                actor_id=actor_id,
                operation="get_boot_environment_descriptor",
            )
        ),
        network_operation_hop_list=[
            NetworkOperationHop(
                source_app_type=NetworkAppType.network_node,
                source_node_id=local_node_id,
                target_app_type=NetworkAppType.network_node,
                target_node_id=peer.node_id,
            )
        ],
    )
    raw = await duplex.send_request(
        connection_id=connection_id,
        data_serialized=request_op.model_dump_json(),
        timeout_s=timeout_s,
    )
    if raw is None:
        return None
    response = (
        NetworkOperation.model_validate_json(raw)
        if isinstance(raw, str)
        else NetworkOperation.model_validate(raw)
    )
    if (
        response.network_response is None
        or response.network_response.status is not NetworkRequestStatus.succeeded
        or response.network_node_operation is None
        or not isinstance(
            response.network_node_operation.response,
            GetBootEnvironmentDescriptorResponse,
        )
    ):
        return None
    boot_response = response.network_node_operation.response
    if (boot_response.status or "").lower() not in {"succeeded", "ready", "running"}:
        return None
    descriptor = boot_response.descriptor
    return descriptor if isinstance(descriptor, BootEnvironmentDescriptor) else None


def build_remote_environment_route_to_peer(
    *,
    network_app: NetworkApp,
    peer: NetworkNodePeerEndpoint,
    route_connection_id: UUID | None = None,
    default_timeout_s: float = 5.0,
):
    async def _route_to_remote_environment(
        network_op: NetworkOperation,
        *,
        timeout_s: float | None = None,
    ) -> NetworkOperation | None:
        if not network_op.network_operation_hop_list:
            raise RuntimeError("Remote Environment route requires an operation hop")
        current_hop = network_op.network_operation_hop_list[0]
        if current_hop.target_app_type != NetworkAppType.environment:
            raise RuntimeError(
                "Remote Environment route only accepts Environment-targeted "
                "NetworkOperations"
            )

        local_node_id = network_node_manager.hosted_node_id
        connection_id = route_connection_id or stable_network_node_peer_id(
            source_peer_node_id=local_node_id,
            target_peer_node_id=peer.node_id,
        )
        duplex = network_app.get_duplex_client(NetworkAppType.network_node)
        await duplex.ensure_connection(
            connection_id=connection_id,
            external_url=peer.base_url,
        )
        forward_op = network_op.model_copy(
            update={
                "network_operation_hop_list": [
                    NetworkOperationHop(
                        source_app_type=NetworkAppType.network_node,
                        source_node_id=local_node_id,
                        target_app_type=NetworkAppType.environment,
                        target_node_id=peer.node_id,
                        target_environment_id=current_hop.target_environment_id,
                    )
                ]
            }
        )

        if network_op.message_type == NetworkOperationMessageType.notification:
            await duplex.send_notification(
                connection_id=connection_id,
                data_serialized=forward_op.model_dump_json(),
            )
            return None

        if network_op.message_type != NetworkOperationMessageType.request:
            raise RuntimeError(
                "Remote Environment route only supports request or notification "
                f"messages, got {network_op.message_type}"
            )

        raw = await duplex.send_request(
            connection_id=connection_id,
            data_serialized=forward_op.model_dump_json(),
            timeout_s=timeout_s if timeout_s is not None else default_timeout_s,
        )
        if raw is None:
            return None
        return (
            NetworkOperation.model_validate_json(raw)
            if isinstance(raw, str)
            else NetworkOperation.model_validate(raw)
        )

    return _route_to_remote_environment


async def _send_environment_request(
    *,
    route_to_environment_service: EnvironmentRouteHandler,
    environment_id: UUID,
    request: object,
    timeout_s: float,
) -> object:
    client = build_environment_service_api_client(
        route_to_environment_service=route_to_environment_service,
        environment_id=environment_id,
        node_id=network_node_manager.hosted_node_id,
        actor_id=getattr(request, "actor_id", None),
        default_timeout_s=timeout_s,
    )
    return await invoke_environment_service_api_request(client, request)


async def _read_network_node_capability_targets(
    *,
    route_to_environment_service: EnvironmentRouteHandler,
    hosted_environment_service: NetworkNodeHostedEnvironmentService,
) -> _BootNetworkNodeTargets:
    node_id = network_node_manager.hosted_node_id
    boot = hosted_environment_service.read_boot_environment_descriptor(node_id=node_id)
    if boot.descriptor is None:
        error = (
            boot.response_error or boot.network_error or "Boot environment unavailable"
        )
        raise RuntimeError(error)
    descriptor = boot.descriptor
    if descriptor.process_id is None or descriptor.thread_id is None:
        raise RuntimeError(
            "Boot environment descriptor is missing process_id/thread_id "
            "for NetworkNode peer discovery"
        )

    describe_payload = await _send_environment_request(
        route_to_environment_service=route_to_environment_service,
        environment_id=descriptor.boot_environment_id,
        timeout_s=15.0,
        request=DescribeEnvironmentConfigRequest(
            actor_id=None,
            environment_id=descriptor.boot_environment_id,
            process_id=descriptor.process_id,
            thread_id=descriptor.thread_id,
            branch_id=descriptor.branch_id,
            projection_hash=None,
        ),
    )
    if getattr(describe_payload, "operation", None) != "describe_environment_config":
        raise RuntimeError(
            "describe_environment_config returned unexpected payload "
            "while resolving NetworkNode peers"
        )

    network_node_opg = next(
        (
            opg
            for opg in describe_payload.opgs
            if (opg.name or "").strip() == "NetworkNode"
        ),
        None,
    )
    if network_node_opg is None:
        raise _NetworkNodePeerDiscoveryUnavailable(
            "Boot environment does not expose the network_node projection"
        )

    capabilities_payload = await _send_environment_request(
        route_to_environment_service=route_to_environment_service,
        environment_id=descriptor.boot_environment_id,
        timeout_s=15.0,
        request=FetchCapabilitiesRequest(
            actor_id=None,
            environment_id=descriptor.boot_environment_id,
            process_id=descriptor.process_id,
            thread_id=descriptor.thread_id,
            branch_id=None,
            projection_hash=None,
        ),
    )
    if getattr(capabilities_payload, "operation", None) != "fetch_capabilities":
        raise RuntimeError(
            "fetch_capabilities returned unexpected payload while resolving "
            "NetworkNode peers"
        )

    list_peers_fn_id: UUID | None = None
    for obj in capabilities_payload.objects:
        if obj.name != "NetworkNode":
            continue
        list_peers_fn_id = next(
            (fn.id for fn in obj.functions if fn.name == "list_peers"),
            None,
        )
        break
    if list_peers_fn_id is None:
        raise _NetworkNodePeerDiscoveryUnavailable(
            "NetworkNode.list_peers is missing from boot environment capabilities"
        )

    return _BootNetworkNodeTargets(
        environment_id=descriptor.boot_environment_id,
        process_id=descriptor.process_id,
        thread_id=descriptor.thread_id,
        projection_graph_id=network_node_opg.id,
        projection_hash=network_node_opg.projection_hash,
        list_peers_function_id=list_peers_fn_id,
    )


async def discover_network_node_peer_endpoints(
    *,
    route_to_environment_service: EnvironmentRouteHandler,
    hosted_environment_service: NetworkNodeHostedEnvironmentService,
    network_sdk_client: NetworkSdkClient | None = None,
) -> tuple[NetworkNodePeerEndpoint, ...]:
    node_id = network_node_manager.hosted_node_id
    if network_sdk_client is not None:
        sdk_peers = await network_sdk_client.list_peers(
            node_id=node_id,
            include_incoming=False,
            include_outgoing=True,
            accepted_only=True,
            limit_results=500,
        )
        endpoints: list[NetworkNodePeerEndpoint] = []
        seen: set[UUID] = set()
        for peer in sdk_peers:
            peer_node_id = peer.peer_node_id
            peer_base_url = _normalize_node_endpoint(peer.peer_base_url)
            if peer_node_id in seen or not peer_base_url:
                continue
            seen.add(peer_node_id)
            endpoints.append(
                NetworkNodePeerEndpoint(
                    node_id=peer_node_id,
                    base_url=peer_base_url,
                )
            )
        return tuple(endpoints)

    try:
        targets = await _read_network_node_capability_targets(
            route_to_environment_service=route_to_environment_service,
            hosted_environment_service=hosted_environment_service,
        )
    except _NetworkNodePeerDiscoveryUnavailable as exc:
        logger.info(
            "NetworkNode peer discovery unavailable; proceeding with no local peers "
            "(reason=%s)",
            exc,
        )
        return ()

    invoke_payload = await _send_environment_request(
        route_to_environment_service=route_to_environment_service,
        environment_id=targets.environment_id,
        timeout_s=15.0,
        request=InvokeFunctionRequest(
            actor_id=None,
            environment_id=targets.environment_id,
            process_id=targets.process_id,
            thread_id=targets.thread_id,
            branch_id=node_id,
            projection_hash=targets.projection_hash,
            call_target=InvokeFunctionCallTarget.instance,
            object_id=node_id,
            object_projection_graph_id=targets.projection_graph_id,
            function_id=targets.list_peers_function_id,
            args=JsonArray(),
            kwargs=JsonObject(
                {
                    "include_incoming": False,
                    "include_outgoing": True,
                    "limit_results": 500,
                }
            ),
            commit=False,
            publish=False,
        ),
    )
    if getattr(invoke_payload, "operation", None) != "invoke_function":
        raise RuntimeError(
            "invoke_function(NetworkNode.list_peers) returned unexpected payload"
        )
    if (invoke_payload.status or "").lower() != "succeeded":
        raise RuntimeError(invoke_payload.error or "NetworkNode.list_peers failed")

    payload = invoke_payload.payload
    if isinstance(payload, dict) and "value" in payload:
        payload = payload.get("value")
    if not isinstance(payload, dict):
        return ()
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        return ()

    peers: list[NetworkNodePeerEndpoint] = []
    seen: set[UUID] = set()
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "").strip().lower() != "accepted":
            continue
        peer_node_id_raw = str(item.get("peer_node_id") or "").strip()
        peer_base_url_raw = str(item.get("peer_http_base_url") or "").strip()
        if not peer_node_id_raw or not peer_base_url_raw:
            continue
        peer_base_url = _normalize_node_endpoint(peer_base_url_raw)
        if not peer_base_url:
            continue
        peer_node_id = UUID(peer_node_id_raw)
        if peer_node_id in seen:
            continue
        seen.add(peer_node_id)
        peers.append(
            NetworkNodePeerEndpoint(node_id=peer_node_id, base_url=peer_base_url)
        )
    return tuple(peers)


async def discover_remote_hosted_service_routes(
    *,
    network_app: NetworkApp,
    route_to_environment_service: EnvironmentRouteHandler,
    hosted_environment_service: NetworkNodeHostedEnvironmentService,
    service_name: str,
    network_sdk_client: NetworkSdkClient | None = None,
    actor_id: UUID | None = None,
    timeout_s: float = 5.0,
) -> tuple[RemoteHostedServiceRoute, ...]:
    normalized_service_name = service_name.strip()
    if not normalized_service_name:
        return ()

    local_node_id = network_node_manager.hosted_node_id
    if network_sdk_client is not None:
        sdk_routes = await network_sdk_client.resolve_hosted_service_routes(
            consumer_node_id=local_node_id,
            service_name=normalized_service_name,
            actor_id=actor_id,
            accepted_peers_only=True,
        )
        return tuple(
            _remote_hosted_service_route_from_network_route(route)
            for route in sdk_routes
        )

    duplex = network_app.get_duplex_client(NetworkAppType.network_node)
    routes: list[RemoteHostedServiceRoute] = []

    peers = await discover_network_node_peer_endpoints(
        route_to_environment_service=route_to_environment_service,
        hosted_environment_service=hosted_environment_service,
        network_sdk_client=network_sdk_client,
    )
    for peer in peers:
        connection_id = stable_network_node_peer_id(
            source_peer_node_id=local_node_id,
            target_peer_node_id=peer.node_id,
        )
        await duplex.ensure_connection(
            connection_id=connection_id,
            external_url=peer.base_url,
        )
        request_op = NetworkOperation(
            id=uuid4(),
            message_type=NetworkOperationMessageType.request,
            type=NetworkOperationType.network_node,
            network_request=NetworkRequest(
                id=uuid4(),
                status=NetworkRequestStatus.pending,
                requester_id=actor_id,
                requester=None,
            ),
            network_node_operation=NetworkNodeOperation(
                request=DiscoverHostedServicesRequest(
                    actor_id=actor_id,
                    operation="discover_hosted_services",
                )
            ),
            network_operation_hop_list=[
                NetworkOperationHop(
                    source_app_type=NetworkAppType.network_node,
                    source_node_id=local_node_id,
                    target_app_type=NetworkAppType.network_node,
                    target_node_id=peer.node_id,
                )
            ],
        )
        raw = await duplex.send_request(
            connection_id=connection_id,
            data_serialized=request_op.model_dump_json(),
            timeout_s=timeout_s,
        )
        if raw is None:
            continue
        response = (
            NetworkOperation.model_validate_json(raw)
            if isinstance(raw, str)
            else NetworkOperation.model_validate(raw)
        )
        if (
            response.network_response is None
            or response.network_response.status is not NetworkRequestStatus.succeeded
            or response.network_node_operation is None
            or not isinstance(
                response.network_node_operation.response,
                DiscoverHostedServicesResponse,
            )
        ):
            continue
        advertisement = (
            _resolve_matching_remote_hosted_service_advertisement_for_service_name(
                peer_node_id=peer.node_id,
                advertisements=tuple(
                    response.network_node_operation.response.hosted_services
                ),
                service_name=normalized_service_name,
            )
        )
        if advertisement is not None:
            routes.append(
                RemoteHostedServiceRoute(peer=peer, advertisement=advertisement)
            )

    return tuple(routes)


async def discover_remote_hosted_service_routes_for_endpoint_ref(
    *,
    network_app: NetworkApp,
    route_to_environment_service: EnvironmentRouteHandler,
    hosted_environment_service: NetworkNodeHostedEnvironmentService,
    endpoint_ref: str,
    network_sdk_client: NetworkSdkClient | None = None,
    actor_id: UUID | None = None,
    timeout_s: float = 5.0,
) -> tuple[RemoteHostedServiceRoute, ...]:
    normalized_endpoint_ref = endpoint_ref.strip()
    if not normalized_endpoint_ref:
        return ()

    local_node_id = network_node_manager.hosted_node_id
    if network_sdk_client is not None:
        sdk_routes = await network_sdk_client.resolve_hosted_service_routes(
            consumer_node_id=local_node_id,
            endpoint_ref=normalized_endpoint_ref,
            actor_id=actor_id,
            accepted_peers_only=True,
        )
        return tuple(
            _remote_hosted_service_route_from_network_route(route)
            for route in sdk_routes
        )

    duplex = network_app.get_duplex_client(NetworkAppType.network_node)
    routes: list[RemoteHostedServiceRoute] = []

    peers = await discover_network_node_peer_endpoints(
        route_to_environment_service=route_to_environment_service,
        hosted_environment_service=hosted_environment_service,
        network_sdk_client=network_sdk_client,
    )
    for peer in peers:
        connection_id = stable_network_node_peer_id(
            source_peer_node_id=local_node_id,
            target_peer_node_id=peer.node_id,
        )
        await duplex.ensure_connection(
            connection_id=connection_id,
            external_url=peer.base_url,
        )
        request_op = NetworkOperation(
            id=uuid4(),
            message_type=NetworkOperationMessageType.request,
            type=NetworkOperationType.network_node,
            network_request=NetworkRequest(
                id=uuid4(),
                status=NetworkRequestStatus.pending,
                requester_id=actor_id,
                requester=None,
            ),
            network_node_operation=NetworkNodeOperation(
                request=DiscoverHostedServicesRequest(
                    actor_id=actor_id,
                    operation="discover_hosted_services",
                )
            ),
            network_operation_hop_list=[
                NetworkOperationHop(
                    source_app_type=NetworkAppType.network_node,
                    source_node_id=local_node_id,
                    target_app_type=NetworkAppType.network_node,
                    target_node_id=peer.node_id,
                )
            ],
        )
        raw = await duplex.send_request(
            connection_id=connection_id,
            data_serialized=request_op.model_dump_json(),
            timeout_s=timeout_s,
        )
        if raw is None:
            continue
        response = (
            NetworkOperation.model_validate_json(raw)
            if isinstance(raw, str)
            else NetworkOperation.model_validate(raw)
        )
        if (
            response.network_response is None
            or response.network_response.status is not NetworkRequestStatus.succeeded
            or response.network_node_operation is None
            or not isinstance(
                response.network_node_operation.response,
                DiscoverHostedServicesResponse,
            )
        ):
            continue
        advertisement = (
            _resolve_matching_remote_hosted_service_advertisement_for_endpoint_ref(
                peer_node_id=peer.node_id,
                advertisements=tuple(
                    response.network_node_operation.response.hosted_services
                ),
                endpoint_ref=normalized_endpoint_ref,
            )
        )
        if advertisement is not None:
            routes.append(
                RemoteHostedServiceRoute(peer=peer, advertisement=advertisement)
            )

    return tuple(routes)


__all__ = [
    "NetworkNodePeerEndpoint",
    "RemoteHostedServiceRoute",
    "build_remote_environment_route_to_peer",
    "discover_network_node_peer_endpoints",
    "discover_remote_hosted_service_advertisements_from_peer",
    "discover_remote_hosted_service_routes",
    "discover_remote_hosted_service_routes_for_endpoint_ref",
    "read_remote_boot_environment_descriptor_from_peer",
]
