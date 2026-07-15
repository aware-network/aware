from typing import Optional
from uuid import UUID, uuid4


from aware_comms.duplex.websocket.models import WsMessageFrame, WsMessageFrameType

from aware_network.communications.duplex.duplex import NetworkDuplex


class EnvironmentDuplex(NetworkDuplex):
    """
    Environment duplex communication layer.

    Implements message building as Environment App.
    """

    # Environment app id (connection id or service id)
    environment_app_id: Optional[UUID] = None

    def set_environment_app_id(self, app_id: UUID) -> None:
        """Set the environment app identifier used as source_app_id"""
        self.environment_app_id = app_id

    def _build_message(
        self,
        message_type: WsMessageFrameType,
        data_serialized: str,
        request_id: Optional[UUID] = None,
    ) -> WsMessageFrame:
        """Build a message frame as ENVIRONMENT app"""
        if self.environment_app_id is None:
            raise RuntimeError("Environment app id is not set")

        if message_type == WsMessageFrameType.REQUEST and request_id is None:
            request_id = uuid4()

        return WsMessageFrame(
            # Message info
            type=message_type,
            data=data_serialized,
            request_id=request_id,
        )
