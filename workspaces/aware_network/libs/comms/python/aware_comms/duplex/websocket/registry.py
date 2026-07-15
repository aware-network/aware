"""Registry describing websocket connections between AWARE applications."""

from __future__ import annotations

from dataclasses import dataclass

import logging

from aware_comms.duplex.websocket.models import WsConnectionConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WsConnection:
    """Describes an allowed websocket connection between two app types."""

    client: str
    server: str
    config: WsConnectionConfig

    def __post_init__(self) -> None:
        if type(self.client) is not str or type(self.server) is not str:
            raise TypeError("WsConnection route keys must be plain strings")


class WsConnectionRegistry:
    """Maintains the set of allowed websocket connections."""

    connections: list[WsConnection]
    _connection_map: dict[tuple[str, str], WsConnection]

    def __init__(self, connections: list[WsConnection] | None = None) -> None:
        self.connections = connections or []
        self._build_connection_map()

    def _build_connection_map(self) -> None:
        self._connection_map = {}
        for conn in self.connections:
            self._connection_map[(conn.client, conn.server)] = conn

    def register_connection(self, connection: WsConnection) -> None:
        self.connections = [
            conn
            for conn in self.connections
            if (conn.client, conn.server) != (connection.client, connection.server)
        ]
        self.connections.append(connection)
        self._build_connection_map()

    def get_connection(self, client_type: str, server_type: str) -> WsConnection | None:
        logger.info("Getting connection for %s -> %s", client_type, server_type)
        return self._connection_map.get((client_type, server_type))

    def get_relationship_types(
        self, source_app: str, target_app: str
    ) -> tuple[str, str]:
        conn = self._connection_map.get((source_app, target_app))
        if not conn:
            conn = self._connection_map.get((target_app, source_app))
        if conn:
            return (conn.client, conn.server)
        raise ValueError(f"No connection found between {source_app} and {target_app}")

    def get_valid_connections(self, app_type: str, *, as_client: bool) -> list[str]:
        app_info: list[str] = []
        for (client, server), _conn in self._connection_map.items():
            if as_client and server == app_type:
                app_info.append(client)
            elif not as_client and client == app_type:
                app_info.append(server)
        return app_info


ws_registry = WsConnectionRegistry()
