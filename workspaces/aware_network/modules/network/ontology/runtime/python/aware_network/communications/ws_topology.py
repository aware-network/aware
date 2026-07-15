from __future__ import annotations

import os

from aware_comms.duplex.websocket.models import WsConnectionConfig
from aware_comms.duplex.websocket.registry import (
    WsConnection,
    WsConnectionRegistry,
    ws_registry,
)
from aware_network_service_dto.network.network_enums import NetworkAppType


def network_app_route_key(app_type: NetworkAppType | str) -> str:
    if isinstance(app_type, NetworkAppType):
        return app_type.value
    if isinstance(app_type, str):
        return app_type
    raise TypeError(f"Unsupported network app route key: {type(app_type).__name__}")


def register_network_ws_topology(registry: WsConnectionRegistry = ws_registry) -> None:
    registry.register_connection(
        WsConnection(
            client=NetworkAppType.interface.value,
            server=NetworkAppType.network_node.value,
            config=WsConnectionConfig(
                requires_auth=False,
                enable_ws=True,
                enable_webrtc=True,
                internal=False,
            ),
        )
    )
    registry.register_connection(
        WsConnection(
            client=NetworkAppType.network_node.value,
            server=NetworkAppType.environment.value,
            config=WsConnectionConfig(
                requires_auth=False,
                enable_ws=True,
                enable_webrtc=True,
                internal=True,
            ),
        )
    )
    registry.register_connection(
        WsConnection(
            client=NetworkAppType.network_node.value,
            server=NetworkAppType.network_node.value,
            config=WsConnectionConfig(
                # v0: bearer-token WS auth is not yet implemented (see get_connection_id_from_token).
                # Until then, node-to-node sessions use explicit connection_id + identity challenge/login.
                requires_auth=(os.environ.get("AWARE_NODE_NODE_WS_REQUIRES_AUTH") or "").strip().lower()
                in {"1", "true", "yes"},
                enable_ws=True,
                enable_webrtc=True,
                internal=True,
            ),
        )
    )


__all__ = ["network_app_route_key", "register_network_ws_topology"]
