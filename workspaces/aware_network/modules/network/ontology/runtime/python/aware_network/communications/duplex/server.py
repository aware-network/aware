import logging
from typing import Optional, Union
from starlette.websockets import WebSocketDisconnect, WebSocketState
from overrides import override
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketException, status
from pydantic import BaseModel, Field

from aware_comms.duplex.websocket.registry import ws_registry
from aware_comms.duplex.base import DuplexSide
from aware_comms.duplex.webrtc.server import WebRTCServer
from aware_comms.duplex.webrtc.models import WsRTCOfferRequest, WsRTCResponse
from aware_comms.duplex.websocket.models import WsMessageFrame, WsMessageFrameType

# Network Duplex
from aware_network.communications.duplex.duplex import NetworkDuplex
from aware_network.communications.interface_session_binding_manager import (
    InterfaceSessionBindingManager,
)
from aware_network.communications.identity_session_manager import IdentitySessionManager


logger = logging.getLogger(__name__)


class NetworkDuplexServer(NetworkDuplex[WebSocket, WebRTCServer]):
    """
    Duplex instance for server side connections (WebSocket and WebRTC)
    """

    side: DuplexSide = DuplexSide.SERVER
    ws_active_request_counts: dict[UUID, int] = Field(default_factory=dict)

    ########################### WEBSOCKET HANDLING - CONNECTION ###########################
    async def connect(
        self,
        connection_id: UUID,
        websocket: WebSocket,
        auth_token: Optional[str] = None,
    ):
        """Accept and store a new WebSocket connection"""
        # Validate connection requirements
        logger.info(
            "duplex.ws.connect client=%s server=%s connection_id=%s",
            self.client_type,
            self.server_type,
            connection_id,
        )
        connection = ws_registry.get_connection(self.client_type, self.server_type)
        if not connection:
            raise ValueError(f"No connection found between {self.client_type} and {self.server_type}")

        existing = self.ws_connections.get(connection_id)
        if existing is not None:
            active_request_count = self.ws_active_request_counts.get(connection_id, 0)
            if active_request_count > 0:
                logger.warning(
                    "duplex.ws.duplicate_rejected_active_requests "
                    "client=%s server=%s connection_id=%s active_requests=%s",
                    self.client_type,
                    self.server_type,
                    connection_id,
                    active_request_count,
                )
                try:
                    await websocket.accept()
                    await websocket.close(
                        code=getattr(
                            status,
                            "WS_1013_TRY_AGAIN_LATER",
                            status.WS_1012_SERVICE_RESTART,
                        )
                    )
                except Exception:
                    logger.debug(
                        "Failed to close duplicate websocket for %s",
                        connection_id,
                        exc_info=True,
                    )
                return

            logger.warning(
                "duplex.ws.replaced client=%s server=%s connection_id=%s",
                self.client_type,
                self.server_type,
                connection_id,
            )
            try:
                if getattr(existing, "application_state", WebSocketState.CONNECTED) != WebSocketState.DISCONNECTED:
                    close_code = getattr(status, "WS_1012_SERVICE_RESTART", status.WS_1001_GOING_AWAY)
                    await existing.close(code=close_code)
            except Exception:
                logger.debug(
                    "Failed to close existing websocket for %s",
                    connection_id,
                    exc_info=True,
                )
            finally:
                if self.ws_connections.get(connection_id) is existing:
                    self.ws_connections.pop(connection_id, None)

        # Accept the WebSocket connection
        await websocket.accept()

        # Store WebSocket connection
        self.ws_connections[connection_id] = websocket

    def _mark_ws_request_active(self, connection_id: UUID) -> None:
        self.ws_active_request_counts[connection_id] = self.ws_active_request_counts.get(connection_id, 0) + 1

    def _mark_ws_request_finished(self, connection_id: UUID) -> None:
        remaining = self.ws_active_request_counts.get(connection_id, 0) - 1
        if remaining > 0:
            self.ws_active_request_counts[connection_id] = remaining
            return
        self.ws_active_request_counts.pop(connection_id, None)

    @staticmethod
    def _is_ws_request_frame(data: object) -> bool:
        try:
            return WsMessageFrame.model_validate(data).type is WsMessageFrameType.REQUEST
        except Exception:
            return False

    @override
    async def disconnect(self, connection_id: UUID):
        """Remove all connections for a given ID"""
        logger.info(
            "duplex.ws.disconnect client=%s server=%s connection_id=%s",
            self.client_type,
            self.server_type,
            connection_id,
        )
        websocket = self.ws_connections.get(connection_id)
        if websocket is not None:
            await self._disconnect_websocket(connection_id, websocket)
            return

        try:
            await InterfaceSessionBindingManager.instance().disconnect(connection_id=connection_id)
            await IdentitySessionManager.instance().disconnect(connection_id=connection_id)
        except Exception:
            logger.exception(
                "Failed to record interface session disconnect for connection %s",
                connection_id,
            )

        wrtc = self.wrtc_connections.pop(connection_id, None)
        if wrtc is not None:
            try:
                await wrtc.close()
            except Exception:
                logger.debug(
                    "Failed to close WebRTC connection for %s",
                    connection_id,
                    exc_info=True,
                )

    async def _disconnect_websocket(self, connection_id: UUID, websocket: WebSocket) -> None:
        """Disconnect a specific websocket instance for a connection id.

        This guards against stale message loops closing a newer socket after a reconnect.
        """
        is_current = self.ws_connections.get(connection_id) is websocket
        if is_current:
            try:
                await InterfaceSessionBindingManager.instance().disconnect(connection_id=connection_id)
                await IdentitySessionManager.instance().disconnect(connection_id=connection_id)
            except Exception:
                logger.exception(
                    "Failed to record interface session disconnect for connection %s",
                    connection_id,
                )

        try:
            if getattr(websocket, "application_state", WebSocketState.CONNECTED) != WebSocketState.DISCONNECTED:
                await websocket.close()
        except Exception:
            logger.debug("Failed to close websocket for %s", connection_id, exc_info=True)

        if is_current:
            self.ws_connections.pop(connection_id, None)
            wrtc = self.wrtc_connections.pop(connection_id, None)
            if wrtc is not None:
                try:
                    await wrtc.close()
                except Exception:
                    logger.debug(
                        "Failed to close WebRTC connection for %s",
                        connection_id,
                        exc_info=True,
                    )

    async def get_connection_id_from_token(self, token: str) -> Optional[UUID]:
        """Get the active connection ID from the token
        Used only by duplex instances used on token ws_routers.
        """
        # TODO: Implement token validation and connection ID extraction
        # Should validate the token and return the associated connection UUID
        logger.warning(
            "duplex.ws.auth_token_unimplemented client=%s server=%s",
            self.client_type,
            self.server_type,
        )
        return None

    def register(self) -> APIRouter:
        """Register the ws_routers for this duplex instance and returns a FastAPI router"""
        # Get connection config from registry
        logger.info(f"Registering connection for {self.client_type} -> {self.server_type}")
        connection = ws_registry.get_connection(self.client_type, self.server_type)
        if connection is None:
            raise ValueError(f"No connection found between {self.client_type} and {self.server_type}")

        # Create the FastAPI router
        router = APIRouter()
        config = connection.config

        if config.requires_auth:
            logger.info(f"Registering authenticated endpoint for {self.client_type} -> {self.server_type}")

            async def token_dependency(websocket: WebSocket):
                logger.debug("duplex.ws.auth_token_dependency")
                # Get token from Authorization header
                auth_header = websocket.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    logger.info("duplex.ws.auth_missing_header")
                    raise WebSocketException(
                        code=status.WS_1008_POLICY_VIOLATION,
                        reason="Missing or invalid Authorization header",
                    )

                token = auth_header.replace("Bearer ", "")
                connection_id = await self.get_connection_id_from_token(token)
                if not connection_id:
                    logger.info("duplex.ws.auth_invalid_token")
                    raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
                return connection_id

            @router.websocket(f"/{self.get_net_endpoint()}")
            async def websocket_endpoint_token(
                websocket: WebSocket,
                connection_id: UUID = Depends(token_dependency),
            ):
                logger.debug("duplex.ws.endpoint connection_id=%s", connection_id)
                await self.start_websocket(websocket, connection_id)

        else:
            logger.info(f"Registering endpoint for {self.client_type} -> {self.server_type} without auth")

            @router.websocket(f"/{self.get_net_endpoint()}")
            async def websocket_endpoint_no_auth(websocket: WebSocket):
                logger.info(f"Connecting {self.client_type} to {self.server_type} without auth")
                cid_str = websocket.query_params.get("connection_id")
                if not cid_str:
                    raise WebSocketException(
                        code=status.WS_1008_POLICY_VIOLATION,
                        reason="Missing connection_id query param",
                    )
                try:
                    connection_id = UUID(cid_str)
                except Exception:
                    raise WebSocketException(
                        code=status.WS_1008_POLICY_VIOLATION,
                        reason="Invalid connection_id",
                    )
                await self.start_websocket(websocket, connection_id)

        return router

    async def start_websocket(self, websocket: WebSocket, connection_id: UUID) -> None:
        """Common WebSocket handling logic"""
        try:
            await self.connect(connection_id, websocket)
            await self._handle_messages_loop(connection_id, websocket)

        except WebSocketDisconnect as disconnect:
            logger.info(
                "duplex.ws.disconnect connection_id=%s code=%s reason=%s",
                connection_id,
                getattr(disconnect, "code", None),
                getattr(disconnect, "reason", None),
            )
            logger.info(
                "duplex.ws.state connection_id=%s state=%s",
                connection_id,
                websocket.client_state,
            )
        except Exception as e:
            logger.exception(
                "duplex.ws.loop_error connection_id=%s error=%s",
                connection_id,
                str(e),
            )

        finally:
            logger.debug(f"server duplex handle_messages_loop finally - disconnecting {connection_id}")
            await self._disconnect_websocket(connection_id, websocket)

    ########################### WEBSOCKET HANDLING - MESSAGING ###########################
    async def _handle_messages_loop(self, connection_id: UUID, websocket: WebSocket) -> None:
        """Handle incoming websocket messages in a loop"""
        logger.debug("duplex.ws.loop_start connection_id=%s", connection_id)
        try:
            while True:
                try:
                    if self.ws_connections.get(connection_id) is not websocket:
                        logger.info(
                            "duplex.ws.stale_loop_exit connection_id=%s reason=replaced",
                            connection_id,
                        )
                        break

                    client_state = websocket.client_state
                    application_state = getattr(websocket, "application_state", None)
                    if client_state != WebSocketState.CONNECTED or application_state not in (
                        None,
                        WebSocketState.CONNECTED,
                    ):
                        logger.info(
                            "duplex.ws.loop_exit connection_id=%s reason=disconnected client=%s application=%s",
                            connection_id,
                            client_state,
                            application_state,
                        )
                        break

                    data = await websocket.receive_json()
                    if self.ws_connections.get(connection_id) is not websocket:
                        logger.info(
                            "duplex.ws.stale_loop_exit connection_id=%s reason=replaced_after_recv",
                            connection_id,
                        )
                        break

                    is_request = self._is_ws_request_frame(data)
                    if is_request:
                        self._mark_ws_request_active(connection_id)
                    try:
                        await self.handle_data(connection_id=connection_id, data=data)
                    finally:
                        if is_request:
                            self._mark_ws_request_finished(connection_id)

                except WebSocketDisconnect as e:
                    logger.info(
                        "duplex.ws.disconnect connection_id=%s code=%s reason=%s",
                        connection_id,
                        getattr(e, "code", None),
                        getattr(e, "reason", None),
                    )
                    break  # Exit the loop on disconnection
                except RuntimeError as e:
                    message = str(e)
                    if "WebSocket is not connected" in message or "accept" in message:
                        logger.info(
                            "duplex.ws.loop_exit connection_id=%s reason=runtime_disconnected error=%s",
                            connection_id,
                            message,
                        )
                        break
                    logger.error(
                        "duplex.ws.loop_error connection_id=%s error=%s",
                        connection_id,
                        message,
                        exc_info=True,
                    )
                    break
                except Exception as e:
                    logger.error(
                        "duplex.ws.loop_error connection_id=%s error=%s",
                        connection_id,
                        str(e),
                        exc_info=True,
                    )
        except Exception as e:
            logger.error(
                "duplex.ws.loop_error connection_id=%s error=%s",
                connection_id,
                str(e),
                exc_info=True,
            )
            raise

    @override
    async def _send_data(self, data: str, connection_id: UUID) -> bool:
        """Send data over WebSocket to Client"""
        if connection_id in self.ws_connections:
            await self.ws_connections[connection_id].send_text(data)
            return True
        return False

    ########################### WEBRTC HANDLING - MESSAGING ############################
    async def handle_wrtc_connection_messages(
        self, request: Union[WsRTCOfferRequest, WsRTCResponse], connection_id: UUID
    ) -> Optional[BaseModel]:
        """
        Overrides base class to handle WebRTC specific messages for connection at server side
        NOTE: For now only wrtc offer is supported.
        """
        if not isinstance(request, WsRTCOfferRequest):
            raise WebSocketException(
                code=status.WS_1003_UNSUPPORTED_DATA,
                reason="Unsupported WebRTC endpoint",
            )

        # Raise error if already connected.
        if connection_id in self.wrtc_connections:
            raise WebSocketException(
                code=status.WS_1011_INTERNAL_ERROR,
                reason="WebRTC handler already connected",
            )

        async def _send_ice_wrapper(candidate):
            """Wrapper to ensure send_ice_candidates_func matches the expected signature"""
            return await self.send_ice_candidate(connection_id, candidate)

        # Start WebRTC server connection on offer request.
        wrtc_server = WebRTCServer(send_ice_candidates_func=_send_ice_wrapper)
        self.wrtc_connections[connection_id] = wrtc_server

        return WsRTCResponse(
            answer_session_description=await wrtc_server.handle_webrtc_offer(request.offer_session_description),
        )
