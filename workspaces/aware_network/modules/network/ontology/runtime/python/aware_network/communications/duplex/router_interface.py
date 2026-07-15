from abc import abstractmethod, ABC
from typing import Awaitable, Callable, Iterable, Optional
from uuid import UUID

from aware_network_service_dto.comms.models.network import NetworkAppType

from aware_comms.duplex.websocket.models import WsMessageFrame, WsMessageFrameType


# Define handler types more generically. Newer handlers may accept an optional
# keyword-only connection_id from the websocket duplex server.
NetworkFrameHandler = Callable[..., Awaitable[Optional[str]]]


class NetworkRouterInterface(ABC):
    """
    Network interface for sending and receiving messages
    """

    @abstractmethod
    async def is_local_identity(self, identity_id: UUID) -> bool:
        """Check if we are the host node for this identity."""
        raise NotImplementedError

    @abstractmethod
    def register_handler(
        self,
        app_type: NetworkAppType,
        message_type: WsMessageFrameType,
        handler: NetworkFrameHandler,
    ) -> None:
        """Register a handler for a message type"""
        raise NotImplementedError

    @abstractmethod
    def unregister_handler(
        self,
        app_type: NetworkAppType,
        message_type: WsMessageFrameType,
        handler: NetworkFrameHandler,
    ) -> None:
        """Unregister a handler for a message type"""
        raise NotImplementedError

    @abstractmethod
    async def send_notifications(
        self,
        identity_ids: Iterable[UUID],
        data_serialized: str,
        notify_local_interfaces: bool = True,
        notify_remote_nodes: bool = True,
        exclude_identity_ids: Iterable[UUID] | None = None,
    ) -> bool:
        """Send a notification to the recipients"""
        raise NotImplementedError

    @abstractmethod
    async def send_request(
        self,
        identity_id: UUID,
        data_serialized: str,
    ) -> WsMessageFrame:
        """Send a request"""
        raise NotImplementedError
