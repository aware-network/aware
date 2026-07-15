from __future__ import annotations

from abc import abstractmethod, ABC
import inspect
from typing import Any, ClassVar, Optional, Self
from pydantic import model_validator
from uuid import UUID, uuid4

from aware_utils.logging import logger

from aware_comms.duplex.base import DuplexBase, WS_T, WRTC_T
from aware_comms.duplex.websocket.models import WsMessageFrame, WsMessageFrameType

from aware_network.communications.duplex.messenger import NetworkDuplexMessenger
from aware_network.communications.duplex.models import WsMessageAck, WsMessageError

from aware_network.communications.duplex.router_interface import NetworkFrameHandler


def _frame_handler_accepts_connection_id(handler: NetworkFrameHandler) -> bool:
    try:
        parameters = inspect.signature(handler).parameters.values()
    except (TypeError, ValueError):
        return False
    return any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD or parameter.name == "connection_id" for parameter in parameters
    )


async def _invoke_frame_handler(
    handler: NetworkFrameHandler,
    data: str,
    message_type: WsMessageFrameType,
    *,
    connection_id: UUID,
) -> Optional[str]:
    if _frame_handler_accepts_connection_id(handler):
        return await handler(data, message_type, connection_id=connection_id)
    return await handler(data, message_type)


class NetworkDuplex(DuplexBase[WS_T, WRTC_T], ABC):
    """
    Network duplex communication layer using common messenger and handlers.
    """

    # Messenger for handling requests and responses
    _messenger: Optional[NetworkDuplexMessenger] = None  # late init

    # Event Handlers - organized by message type
    _handlers: ClassVar[dict[WsMessageFrameType, set[NetworkFrameHandler]]] = {}

    @property
    def messenger(self) -> NetworkDuplexMessenger:
        """Get the messenger"""
        if self._messenger is None:
            raise ValueError("Messenger not initialized")
        return self._messenger

    @model_validator(mode="after")
    def setup_messenger(self) -> Self:
        """Post-initialization hook"""
        if self._messenger is None:
            self._messenger = NetworkDuplexMessenger(send_data_fn=self._send_data)
        return self

    @classmethod
    def register_handler(cls, message_type: WsMessageFrameType, handler: NetworkFrameHandler) -> None:
        """
        Register a handler for a specific message type

        Args:
            message_type: The message frame type to handle
            handler: The handler function
        """
        # Initialize message type if not present
        if message_type not in cls._handlers:
            cls._handlers[message_type] = set()

        # Idempotent: if this exact handler is already registered, do nothing
        if handler in cls._handlers[message_type]:
            logger.warning(f"Handler already registered for {message_type.value}; skipping")
            return

        # Enforce single request handler per message type
        if message_type is WsMessageFrameType.REQUEST and len(cls._handlers[message_type]) > 0:
            raise ValueError(f"Request handler for {message_type} already registered")

        cls._handlers[message_type].add(handler)
        logger.debug(f"Registered handler for {message_type.value}")

    @classmethod
    def unregister_handler(cls, message_type: WsMessageFrameType, handler: NetworkFrameHandler) -> None:
        """
        Unregister a handler for a specific message type

        Args:
            message_type: The message frame type to handle
            handler: The handler function to remove
        """
        if message_type in cls._handlers and handler in cls._handlers[message_type]:
            cls._handlers[message_type].remove(handler)
            logger.debug(f"Unregistered handler for {message_type.value}")

    async def handle_data(self, connection_id: UUID, data: dict) -> None:
        """Handle incoming data from a websocket connection."""
        try:
            # Parse the message into frame and content
            frame = WsMessageFrame.model_validate(data)

            # Send acknowledgment for requests only
            logger.debug(
                "duplex.frame.recv connection_id=%s frame_type=%s ws_request_id=%s frame_id=%s",
                connection_id,
                frame.type.value,
                frame.request_id,
                frame.id,
            )
            if frame.type == WsMessageFrameType.REQUEST:
                logger.debug(
                    "duplex.frame.ack_send connection_id=%s ws_request_id=%s",
                    connection_id,
                    frame.request_id or frame.id,
                )
                await self._send_ack(connection_id=connection_id, frame=frame)

            # Handle special cases for responses and acks
            if frame.type in [
                WsMessageFrameType.RESPONSE,
                WsMessageFrameType.ACK,
                WsMessageFrameType.ERROR,
            ]:
                logger.debug(
                    "duplex.frame.deliver connection_id=%s frame_type=%s ws_request_id=%s",
                    connection_id,
                    frame.type.value,
                    frame.request_id,
                )
                await self.messenger.recv(frame, data)
                return None

            # Find handlers for this message type
            handlers = set()
            if frame.type in self._handlers:
                handlers = self._handlers[frame.type]

            # Execute the request handler
            if frame.type == WsMessageFrameType.REQUEST:
                if handlers:
                    try:
                        # Retrieve the enforced single handler
                        handler = next(iter(handlers))
                        logger.debug(
                            "duplex.frame.dispatch connection_id=%s frame_type=%s ws_request_id=%s",
                            connection_id,
                            frame.type.value,
                            frame.request_id,
                        )
                        response = await _invoke_frame_handler(
                            handler,
                            frame.data,
                            frame.type,
                            connection_id=connection_id,
                        )
                        if response is not None:
                            logger.debug(
                                "duplex.frame.response_send connection_id=%s ws_request_id=%s",
                                connection_id,
                                frame.request_id or frame.id,
                            )
                            await self._send_response(
                                connection_id=connection_id,
                                frame=frame,
                                data_serialized=response,
                            )
                    except Exception as e:
                        logger.exception(
                            "duplex.frame.handler_error connection_id=%s ws_request_id=%s error=%s",
                            connection_id,
                            frame.request_id,
                            str(e),
                        )
                        if frame.type == WsMessageFrameType.REQUEST:
                            await self._send_error_message(
                                connection_id=connection_id,
                                frame=frame,
                                error=WsMessageError(type="unexpected", message=str(e)),
                            )
                else:
                    error_message = f"No handlers for {frame.type.value}"
                    logger.error(
                        "duplex.frame.no_handler connection_id=%s frame_type=%s ws_request_id=%s",
                        connection_id,
                        frame.type.value,
                        frame.request_id,
                    )
                    await self._send_error_message(
                        connection_id=connection_id,
                        frame=frame,
                        error=WsMessageError(type="invalid_message", message=error_message),
                    )
                    return None

            # Execute all notification handlers
            elif frame.type == WsMessageFrameType.NOTIFICATION and handlers:
                logger.debug(
                    "duplex.frame.notify_dispatch connection_id=%s handler_count=%s",
                    connection_id,
                    len(handlers),
                )
                for handler in handlers:
                    try:
                        await _invoke_frame_handler(
                            handler,
                            frame.data,
                            frame.type,
                            connection_id=connection_id,
                        )
                    except Exception as e:
                        logger.error(
                            "duplex.frame.notify_handler_error connection_id=%s error=%s",
                            connection_id,
                            str(e),
                            exc_info=True,
                        )
                return None

        except Exception as e:
            logger.error(
                "duplex.frame.parse_error connection_id=%s error=%s",
                connection_id,
                str(e),
                exc_info=True,
            )
            return None

    async def _send_ack(self, connection_id: UUID, frame: WsMessageFrame) -> bool:
        """Send an ack message to the client"""
        ack = WsMessageAck()
        ack_frame = self._build_message(
            message_type=WsMessageFrameType.ACK,
            data_serialized=ack.model_dump_json(),
            request_id=frame.request_id,
        )
        return await self.messenger.send_feedback(
            connection_id=connection_id,
            feedback_data=ack_frame.model_dump_json(),
        )

    async def _send_error_message(
        self,
        connection_id: UUID,
        frame: WsMessageFrame,
        error: WsMessageError,
    ) -> bool:
        """Send error message"""
        error_frame = self._build_message(
            message_type=WsMessageFrameType.ERROR,
            data_serialized=error.model_dump_json(),
            request_id=frame.request_id,
        )
        return await self.messenger.send_feedback(
            connection_id=connection_id,
            feedback_data=error_frame.model_dump_json(),
        )

    async def send_notification(
        self,
        connection_id: UUID,
        data_serialized: str,
    ) -> bool:
        """
        Generic method to send any notification

        Args:
            connection_id: The connection to send to
            data_serialized: The serialized data of the notification

        Returns:
            True if sent successfully
        """
        # Create frame with serialized content
        notification_frame = self._build_message(
            message_type=WsMessageFrameType.NOTIFICATION,
            data_serialized=data_serialized,
        )

        # Send the frame
        return await self.messenger.send_feedback(
            connection_id=connection_id,
            feedback_data=notification_frame.model_dump_json(),
        )

    async def send_request(
        self,
        connection_id: UUID,
        data_serialized: str,
        timeout_s: float | None = None,
    ) -> Any:
        request_id = uuid4()
        request_frame = self._build_message(
            message_type=WsMessageFrameType.REQUEST,
            data_serialized=data_serialized,
            request_id=request_id,
        )
        response = await self.messenger.send_request(
            request_id=request_id,
            request_data=request_frame.model_dump_json(),
            connection_id=connection_id,
            timeout_s=timeout_s,
        )
        return response

    async def _send_response(
        self,
        connection_id: UUID,
        frame: WsMessageFrame,
        data_serialized: str,
    ) -> bool:
        response_frame = self._build_message(
            message_type=WsMessageFrameType.RESPONSE,
            data_serialized=data_serialized,
            request_id=frame.request_id,
        )
        return await self.messenger.send_feedback(
            connection_id=connection_id,
            feedback_data=response_frame.model_dump_json(),
        )

    @abstractmethod
    def _build_message(
        self,
        message_type: WsMessageFrameType,
        data_serialized: str,
        request_id: Optional[UUID] = None,
    ) -> WsMessageFrame:
        pass
