from typing import Optional
from uuid import UUID, uuid4

from aware_comms.duplex.websocket.models import WsMessageFrame, WsMessageFrameType

from aware_network.communications.duplex.duplex import NetworkDuplex

from aware_network.network.node.local_info import LocalNetworkNodeInfo


class NetworkNodeDuplex(NetworkDuplex):
    """
    Network node duplex communication layer.

    Implements NetworkInterface to interact with duplex as Network Node App.
    """

    # Network node instance
    network_node: Optional[LocalNetworkNodeInfo] = None

    def set_network_node(self, network_node: LocalNetworkNodeInfo) -> None:
        """Set the network node instance"""
        self.network_node = network_node

    def _build_message(
        self,
        message_type: WsMessageFrameType,
        data_serialized: str,
        request_id: Optional[UUID] = None,
    ) -> WsMessageFrame:
        """Build a message frame"""
        if self.network_node is None:
            raise RuntimeError("Network node is not set")

        if message_type == WsMessageFrameType.REQUEST and request_id is None:
            # Enforce request construction as default for Request messages
            request_id = uuid4()

        return WsMessageFrame(
            # Message info
            type=message_type,
            data=data_serialized,
            request_id=request_id,
        )
