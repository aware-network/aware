"""
Aware Network Node App
"""

import asyncio
import os

from aware_utils.logging import logger

# Network
from aware_network.communications.app import NetworkApp
from aware_network.network.node.local_info import LocalNetworkNodeInfo

# Network Node HTTP Server
from aware_node_service.http_api.server import network_node_http_server

# Network Node Duplex
from aware_comms.duplex.collection import DuplexCollection
from aware_comms.http.server import HttpServer

from aware_node_service.duplex.router import NetworkNodeRouter
from aware_node_service.acl_mode import lock_node_actor_role_acl_mode
from aware_node_service.control_plane.bootstrap_service import (
    NetworkNodeBootstrapService,
)
from aware_node_service.control_plane.hosted_environment_service import (
    NetworkNodeHostedEnvironmentService,
)
from aware_node_service.control_plane.topology_bootstrap_service import (
    NetworkNodeTopologyBootstrapService,
)
from aware_node_service.host import (
    NodeHostServicesAssembly,
    activate_node_hosted_service_lifecycles,
    configure_node_persistence_backend,
    configure_node_runtime_inputs,
    configure_node_secrets,
    configure_node_storage,
    serve_node_runtime,
    bind_node_service_api_dependency_routes,
    register_node_http_routes,
    start_node_host_services,
    stop_node_host_services,
)
from aware_node_service.transport import (
    NodeTransportAssembly,
    assemble_node_transport,
)

from aware_network_service_dto.network.network_enums import NetworkAppType


class NetworkNodeApp(NetworkApp):
    """Network Node App Service, hosted in the Aware Network Node module"""

    app_type: str = NetworkAppType.network_node.value
    title: str = "Aware Network Node"
    description: str = "Aware Network Node - Enter the future of Technology."

    # Required NetApp fields (Pydantic defaults)
    http_server: HttpServer = network_node_http_server
    duplex_collection: DuplexCollection = DuplexCollection()

    # Non-model attribute for internal use
    _transport_runtime: NodeTransportAssembly
    _host_services_runtime: NodeHostServicesAssembly | None = None
    _network_router: NetworkNodeRouter
    _node_bootstrap_service: NetworkNodeBootstrapService
    _node_hosted_environment_service: NetworkNodeHostedEnvironmentService
    _node_topology_bootstrap_service: NetworkNodeTopologyBootstrapService
    _fanout_service: object | None = None

    def __init__(self, **data):
        super().__init__(**data)

    def create_app(self):
        app = super().create_app()
        register_node_http_routes(app)
        return app

    async def start(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Start the Network Node App"""
        self._configure_host_shell()
        try:
            self._host_services_runtime = await start_node_host_services(node_app=self)
            await bind_node_service_api_dependency_routes(
                node_app=self,
                runtime=self._host_services_runtime,
                configure_hosted_environments=False,
                allow_prepared_local_providers=True,
                include_node_control_plane_consumer=False,
                require_complete=False,
            )
            await activate_node_hosted_service_lifecycles(
                runtime=self._host_services_runtime
            )
            await self._bootstrap_control_plane()
            await bind_node_service_api_dependency_routes(
                node_app=self,
                runtime=self._host_services_runtime,
            )
            self._fanout_service = self._host_services_runtime.fanout_service
            await serve_node_runtime(node_app=self, host=host, port=port)
        finally:
            if self._host_services_runtime is not None:
                await stop_node_host_services(runtime=self._host_services_runtime)

    def _configure_host_shell(self) -> None:
        acl_mode = lock_node_actor_role_acl_mode()
        logger.info(
            "ActorRole ACL locked for node runtime boundary (mode=%s)", acl_mode
        )
        configure_node_secrets()
        configure_node_runtime_inputs()
        configure_node_storage()
        configure_node_persistence_backend()
        self._transport_runtime = assemble_node_transport(
            node_app=self,
            network_node=self._get_network_node(),
        )
        self.http_server = self._transport_runtime.http_server
        self.duplex_collection = self._transport_runtime.duplex_collection
        self._network_router = self._transport_runtime.network_router
        self._node_bootstrap_service = self._transport_runtime.bootstrap_service
        self._node_hosted_environment_service = (
            self._transport_runtime.hosted_environment_service
        )
        self._node_topology_bootstrap_service = (
            self._transport_runtime.topology_bootstrap_service
        )

    async def _bootstrap_control_plane(self) -> None:
        # Kernel boot contract: ensure the kernel environment exists and is
        # ready before serving traffic.
        await self._node_bootstrap_service.bootstrap_kernel_environment()

    def _get_network_node(self) -> LocalNetworkNodeInfo:
        # Resolve from filesystem (.aware) using NetworkNodeManager info
        from aware_network.network.node.manager import network_node_manager

        return network_node_manager.ensure_local_info()


def create_network_node_app() -> NetworkNodeApp:
    return NetworkNodeApp()


def _resolve_node_host(host: str | None = None) -> str:
    if host is not None:
        return host
    return os.environ.get("AWARE_NODE_HOST", "0.0.0.0")


def _resolve_node_port(port: int | None = None) -> int:
    if port is not None:
        return port
    return int(os.environ.get("AWARE_NODE_PORT", "8000"))


async def start_node_service(
    *, host: str | None = None, port: int | None = None
) -> None:
    resolved_host = _resolve_node_host(host)
    resolved_port = _resolve_node_port(port)
    logger.info("Starting AWARE Node service on %s:%s", resolved_host, resolved_port)
    app = create_network_node_app()
    await app.start(host=resolved_host, port=resolved_port)


def run() -> None:
    asyncio.run(start_node_service())


if __name__ == "__main__":
    run()
