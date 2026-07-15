from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from aware_api_ontology.stable_ids import stable_api_package_id
from aware_network_sdk import NetworkSdkCache, NetworkSdkClient
from aware_network_service_api import AwareNetworkServiceApiClient
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_route,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
)
from aware_utils.logging import logger

NETWORK_SERVICE_API_PACKAGE_NAME = "network-service-api"
NODE_CONTROL_PLANE_SERVICE_PACKAGE_NAME = "aware-node-control-plane"


@dataclass(frozen=True, slots=True)
class NodeNetworkSdkRouteBinding:
    route: ServiceApiDependencyRouteDescriptor
    client: NetworkSdkClient


def select_network_service_api_route(
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
) -> ServiceApiDependencyRouteDescriptor | None:
    matches = tuple(route for route in routes if _route_is_network_service_api(route))
    if not matches:
        return None

    control_plane_matches = tuple(
        route
        for route in matches
        if route.consumer_service_package_name.strip().casefold()
        == NODE_CONTROL_PLANE_SERVICE_PACKAGE_NAME
    )
    if len(control_plane_matches) == 1:
        return control_plane_matches[0]
    if len(control_plane_matches) > 1:
        raise RuntimeError(
            "Resolved multiple Node control-plane Network Service API routes."
        )
    if len(matches) == 1:
        return matches[0]

    labels = ", ".join(
        f"{route.consumer_service_package_name}->{route.provider_service_package_name}"
        for route in matches
    )
    raise RuntimeError(
        "Resolved multiple Network Service API routes and none is the Node "
        f"control-plane route: {labels}."
    )


def build_network_sdk_client_for_service_api_routes(
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
    *,
    actor_id: UUID | None = None,
) -> NodeNetworkSdkRouteBinding | None:
    route = select_network_service_api_route(routes)
    if route is None:
        return None
    api_invoker = build_service_api_client_for_route(route, actor_id=actor_id)
    api_client = AwareNetworkServiceApiClient(api_invoker)
    return NodeNetworkSdkRouteBinding(
        route=route,
        client=NetworkSdkClient(
            api_client=api_client,
            cache=NetworkSdkCache(),
        ),
    )


def configure_network_sdk_client_from_service_api_routes(
    *,
    node_app: object,
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
) -> NodeNetworkSdkRouteBinding | None:
    router = getattr(node_app, "_network_router", None)
    setter = getattr(router, "set_network_sdk_client", None)
    if not callable(setter):
        return None

    binding = build_network_sdk_client_for_service_api_routes(routes)
    setter(binding.client if binding is not None else None)
    if binding is None:
        logger.info(
            "Node Network SDK route cleared; no Network Service API route bound."
        )
        return None

    logger.info(
        "Node Network SDK route bound "
        "(route_kind=%s provider_service_package=%s host_id=%s)",
        binding.route.route_kind.value,
        binding.route.provider_service_package_name,
        binding.route.host_id,
    )
    return binding


def _route_is_network_service_api(route: ServiceApiDependencyRouteDescriptor) -> bool:
    api_package_name = (route.api_package_name or "").strip().casefold()
    if api_package_name == NETWORK_SERVICE_API_PACKAGE_NAME:
        return True
    return route.api_package_id == stable_api_package_id(
        name=NETWORK_SERVICE_API_PACKAGE_NAME
    )


__all__ = [
    "NETWORK_SERVICE_API_PACKAGE_NAME",
    "NODE_CONTROL_PLANE_SERVICE_PACKAGE_NAME",
    "NodeNetworkSdkRouteBinding",
    "build_network_sdk_client_for_service_api_routes",
    "configure_network_sdk_client_from_service_api_routes",
    "select_network_service_api_route",
]
