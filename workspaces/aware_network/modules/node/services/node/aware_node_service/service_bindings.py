from __future__ import annotations

from aware_node.host_control_plane import NodeHostControlPlaneService

from .api_service_protocol import build_aware_node_service_protocol_handler


def build_service_bindings(
    *,
    control_plane: NodeHostControlPlaneService,
) -> dict[str, object]:
    return {
        "aware_node": build_aware_node_service_protocol_handler(
            control_plane=control_plane,
        ),
    }


__all__ = ["build_service_bindings"]
