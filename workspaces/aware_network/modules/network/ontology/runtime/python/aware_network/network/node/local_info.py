from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from aware_network_ontology.stable_ids import stable_network_node_id


class LocalNetworkNodeInfo(BaseModel):
    """Serializable local node info for discovery via filesystem (.aware).

    This complements DB persistence by providing a durable, process-independent
    source of truth for local node identity and endpoints during bootstrap.
    """

    id: UUID = Field(default_factory=uuid4)
    label: Optional[str] = None

    # Base HTTP URL where this node is serving (e.g., http://localhost:8000)
    http_base_url: str = Field(default="http://localhost:8000")

    # WebSocket endpoints relative to base URL
    ws_interface_to_node_path: str = Field(default="/interface/network_node")
    ws_node_to_node_path: str = Field(default="/network_node/network_node")

    # Optional metadata
    public_key: Optional[str] = None
    requires_auth_interface_to_node: bool = Field(default=False)

    def get_interface_ws_url(self, connection_id: UUID) -> str:
        base = self.http_base_url.replace("http://", "ws://").replace("https://", "wss://")
        return f"{base}{self.ws_interface_to_node_path}?connection_id={connection_id}"

    def get_node_to_node_ws_url(self) -> str:
        base = self.http_base_url.replace("http://", "ws://").replace("https://", "wss://")
        return f"{base}{self.ws_node_to_node_path}"


def normalize_local_network_node_info_identity(
    info: LocalNetworkNodeInfo,
) -> LocalNetworkNodeInfo:
    public_key = (info.public_key or "").strip() or f"dev:node:{info.id}"
    expected_id = stable_network_node_id(public_key=public_key)
    if info.id == expected_id and info.public_key == public_key:
        return info
    return info.model_copy(update={"id": expected_id, "public_key": public_key})
