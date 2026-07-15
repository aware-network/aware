from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from aware_comms.duplex.collection import DuplexCollection
from aware_comms.http.server import HttpServer
from aware_network.network.node.local_info import LocalNetworkNodeInfo
from aware_network.communications.ws_topology import register_network_ws_topology
from aware_network_service_dto.network.network_enums import NetworkAppType

from aware_node_service.control_plane.bootstrap_service import (
    NetworkNodeBootstrapService,
)
from aware_node_service.control_plane.hosted_environment_service import (
    NetworkNodeHostedEnvironmentService,
)
from aware_node_service.control_plane.topology_bootstrap_service import (
    NetworkNodeTopologyBootstrapService,
)
from aware_node_service.duplex.client import NetworkNodeDuplexClient
from aware_node_service.duplex.router import NetworkNodeRouter
from aware_node_service.duplex.server import NetworkNodeDuplexServer
from aware_node_service.http_api.server import network_node_http_server

if TYPE_CHECKING:
    from aware_node_service.app import NetworkNodeApp


@dataclass(frozen=True)
class NodeTransportAssembly:
    http_server: HttpServer
    duplex_collection: DuplexCollection
    network_router: NetworkNodeRouter
    hosted_environment_service: NetworkNodeHostedEnvironmentService
    topology_bootstrap_service: NetworkNodeTopologyBootstrapService
    bootstrap_service: NetworkNodeBootstrapService


def assemble_node_transport(
    *,
    node_app: "NetworkNodeApp",
    network_node: LocalNetworkNodeInfo,
) -> NodeTransportAssembly:
    duplex_collection = _build_duplex_collection(network_node=network_node)
    node_app.http_server = network_node_http_server
    node_app.duplex_collection = duplex_collection
    network_router = NetworkNodeRouter(node_app)
    hosted_environment_service = NetworkNodeHostedEnvironmentService(
        route_to_environment_service=network_router.route_to_environment_service
    )
    topology_bootstrap_service = NetworkNodeTopologyBootstrapService(
        route_to_environment_service=network_router.route_to_environment_service
    )
    bootstrap_service = NetworkNodeBootstrapService(
        route_to_environment_service=network_router.route_to_environment_service,
        hosted_environment_service=hosted_environment_service,
        topology_bootstrap_service=topology_bootstrap_service,
    )
    network_router.set_hosted_environment_service(hosted_environment_service)
    network_router.set_bootstrap_service(bootstrap_service)
    return NodeTransportAssembly(
        http_server=network_node_http_server,
        duplex_collection=duplex_collection,
        network_router=network_router,
        hosted_environment_service=hosted_environment_service,
        topology_bootstrap_service=topology_bootstrap_service,
        bootstrap_service=bootstrap_service,
    )


def _build_duplex_collection(*, network_node: LocalNetworkNodeInfo) -> DuplexCollection:
    register_network_ws_topology()
    duplex_collection = DuplexCollection()
    duplex_collection.register_duplex(
        NetworkNodeDuplexServer(
            client_type=NetworkAppType.interface.value,
            server_type=NetworkAppType.network_node.value,
        )
    )
    duplex_collection.register_duplex(
        NetworkNodeDuplexServer(
            client_type=NetworkAppType.network_node.value,
            server_type=NetworkAppType.network_node.value,
        )
    )
    duplex_collection.register_duplex(
        NetworkNodeDuplexClient(
            client_type=NetworkAppType.network_node.value,
            server_type=NetworkAppType.environment.value,
        )
    )
    duplex_collection.register_duplex(
        NetworkNodeDuplexClient(
            client_type=NetworkAppType.network_node.value,
            server_type=NetworkAppType.network_node.value,
        )
    )

    for duplex in duplex_collection.duplex_list.values():
        if isinstance(duplex, NetworkNodeDuplexClient) or isinstance(
            duplex, NetworkNodeDuplexServer
        ):
            duplex.set_network_node(network_node)
    return duplex_collection


__all__ = ["NodeTransportAssembly", "assemble_node_transport"]
