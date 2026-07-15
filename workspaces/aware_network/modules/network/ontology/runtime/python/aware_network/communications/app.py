"""
Aware Network Node App
"""

from typing import cast
from uuid import UUID

# App
from aware_network.communications.app_config import get_network_app_config as get_app_config
from aware_comms.app.registry import app_registry
from aware_comms.app.app import App

# Duplex
from aware_comms.duplex.base import DuplexSide

# Network Communications
from aware_network.communications.duplex.client import NetworkDuplexClient
from aware_network.communications.duplex.server import NetworkDuplexServer
from aware_network.communications.ws_topology import (
    network_app_route_key,
    register_network_ws_topology,
)

# Network protocol models (DTO)
from aware_network_service_dto.comms.models.network import NetworkOperation
from aware_network_service_dto.network.network_enums import NetworkAppType


from aware_utils.logging import logger


class NetworkApp(App):
    """Network App Service, hosted in the Aware Network module"""

    app_type: str
    title: str = "Aware Network"
    description: str = "Aware Network - Enter the future of Technology."

    async def start(self, host="0.0.0.0"):
        """Start Agent App"""
        register_network_ws_topology()
        # Register self in the global registry
        app_registry.register_app(self)
        app_port = get_app_config(self.app_type).PORT
        # Start the app
        await self.run_prod(host=host, port=app_port)

    def get_duplex_client(self, server_app_type: NetworkAppType | str) -> NetworkDuplexClient:
        """Get a duplex client instance for WebSocket connections to a specific server app type

        NOTE: Overrides to provide the NetworkNodeDuplexClient type.
        """
        client = super().get_duplex_client(network_app_route_key(server_app_type))
        return cast(NetworkDuplexClient, client)

    def get_duplex_server(self, client_app_type: NetworkAppType | str) -> NetworkDuplexServer:
        """Get a duplex server instance for WebSocket connections from a specific client app type

        NOTE: Overrides to provide the NetworkNodeDuplexServer type.
        """
        server = super().get_duplex_server(network_app_route_key(client_app_type))
        return cast(NetworkDuplexServer, server)

    def get_duplex(
        self, app_type: NetworkAppType | str, side: DuplexSide | None = None
    ) -> NetworkDuplexClient | NetworkDuplexServer | None:
        """Get a duplex instance for a specific app type"""
        if side is None:
            # Try client first; if unavailable, try server
            try:
                client = self.get_duplex_client(app_type)
                if client:
                    return client
            except ValueError:
                pass
            try:
                server = self.get_duplex_server(app_type)
                if server:
                    return server
            except ValueError:
                pass
            return None
        if side == DuplexSide.CLIENT:
            return self.get_duplex_client(app_type)
        elif side == DuplexSide.SERVER:
            return self.get_duplex_server(app_type)
        raise ValueError(f"Invalid duplex side: {side}")

    def get_duplex_for_connection(self, connection_id: UUID) -> NetworkDuplexServer | NetworkDuplexClient | None:
        """Get a duplex instance for a specific connection ID"""
        duplex = self.duplex_collection.get_ws_connection(connection_id)
        if duplex:
            return cast(NetworkDuplexServer | NetworkDuplexClient, duplex)

        return None

    async def send_network_operation(
        self,
        network_operation: NetworkOperation,
        target_connection_id: UUID,
    ) -> dict:
        """
        Send a NetworkOperation to another node or service using the network router

        Args:
            network_operation: The NetworkOperation to send
            target_connection_id: The target connection ID

        Returns:
            Response from target
        """
        try:
            # Get appropriate duplex for sending
            duplex = self.get_duplex_for_connection(target_connection_id)
            if not duplex:
                raise RuntimeError(f"No duplex found for connection {target_connection_id}")

            # Send NetworkOperation
            response = await duplex.send_request(
                connection_id=target_connection_id,
                data_serialized=network_operation.model_dump_json(),
            )

            return response

        except Exception as e:
            logger.error(f"Error sending NetworkOperation: {e}")
            raise
