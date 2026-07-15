import asyncio
import json
import os
import ssl
from overrides import override
from typing import Optional, Union
from uuid import UUID

# TODO: Remove fastapi dependency, use common WebSocketException
from fastapi import WebSocketException, status
from websockets import protocol as ws_protocol, ConnectionClosed
from websockets.asyncio import client as ws_client

from aware_network.communications.app_config import get_network_app_config as get_app_config

from aware_comms.duplex.websocket.registry import ws_registry
from aware_comms.duplex.base import DuplexSide
from aware_comms.duplex.webrtc.client import WebRTCClient
from aware_comms.duplex.webrtc.models import WsRTCOfferRequest, WsRTCResponse

# Network Duplex
from aware_network.communications.duplex.duplex import NetworkDuplex

from aware_utils.logging import logger


def _read_keepalive_seconds(*, env_var: str, default: float | None) -> float | None:
    raw = os.environ.get(env_var)
    if raw is None:
        return default
    raw = raw.strip().lower()
    if raw in {"", "none", "null"}:
        return None
    try:
        value = float(raw)
    except Exception:
        return default
    if value <= 0:
        return None
    return value


class NetworkDuplexClient(NetworkDuplex[ws_client.ClientConnection, WebRTCClient]):
    """
    Client implementation of DuplexManager for initiating connections to remote endpoints
    """

    side: DuplexSide = DuplexSide.CLIENT
    ssl_context: Optional[ssl.SSLContext] = None

    ########################### WEBSOCKET HANDLING - CONNECTION ##########################
    async def establish_ws_connection(
        self,
        connection_id: UUID,
        auth_token: Optional[str] = None,
        external_url: Optional[str] = None,
    ) -> None:
        """Establish a WebSocket connection using the connection configuration"""
        if connection_id in self.ws_connections:
            logger.warning(f"[{connection_id}] Connection already exists")
            return

        try:
            connection = ws_registry.get_connection(self.client_type, self.server_type)
            if not connection:
                raise ValueError(f"No connection found between {self.client_type} and {self.server_type}")

            logger.debug(
                "duplex.ws.config client=%s server=%s connection_id=%s",
                self.client_type,
                self.server_type,
                connection_id,
            )

            # Determine the URL to connect to
            if external_url:
                # Accept both http(s) and ws(s) endpoints.
                if external_url.startswith("http://"):
                    external_url = f"ws://{external_url[len('http://'):]}"
                elif external_url.startswith("https://"):
                    external_url = f"wss://{external_url[len('https://'):]}"
                # Explicit override for dynamic endpoints (e.g. multi-environment routing).
                remote_url = f"{external_url.rstrip('/')}/{self.get_net_endpoint()}"
                logger.info(
                    "duplex.ws.connecting connection_id=%s remote_url=%s",
                    connection_id,
                    remote_url,
                )
            elif connection.config.internal:
                # Use internal URL (Docker network)
                url = get_app_config(connection.server).full_url
                url = url.replace("http://", "ws://")
                url = url.replace("https://", "wss://")
                remote_url = f"{url}/{self.get_net_endpoint()}"
                logger.info(
                    "duplex.ws.connecting connection_id=%s remote_url=%s",
                    connection_id,
                    remote_url,
                )
            else:
                raise ValueError("External URL is required for non-internal connections")

            headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else None

            if connection.config.requires_auth and not auth_token:
                raise WebSocketException(code=1008, reason="Authentication token required")

            url_with_params = f"{remote_url}?connection_id={connection_id}"
            logger.info(
                "duplex.ws.connect connection_id=%s url=%s requires_auth=%s",
                connection_id,
                url_with_params,
                connection.config.requires_auth,
            )

            # Important: node->environment `ensure_ready` can legitimately take tens of seconds while DB/schema
            # is bootstrapped. Default websockets ping timeouts are too aggressive for that path and can
            # close the duplex before the response is emitted.
            ping_interval = _read_keepalive_seconds(
                env_var="AWARE_DUPLEX_WS_PING_INTERVAL_S",
                default=20,
            )
            ping_timeout = _read_keepalive_seconds(
                env_var="AWARE_DUPLEX_WS_PING_TIMEOUT_S",
                default=120,
            )

            # Use modern websockets client with proper configuration
            websocket = await ws_client.connect(
                uri=url_with_params,
                additional_headers=headers,
                ping_interval=ping_interval,
                ping_timeout=ping_timeout,
                close_timeout=10,
                max_size=None,
                logger=logger,
                ssl=self.ssl_context,
            )

            logger.info("duplex.ws.connected connection_id=%s", connection_id)
            self.ws_connections[connection_id] = websocket

            # Start message handling loop as a task
            task = asyncio.create_task(self._handle_messages_loop(connection_id, websocket))
            task.add_done_callback(self._handle_task_completion(connection_id))

        except Exception as e:
            logger.error(
                "duplex.ws.connect_failed connection_id=%s error=%s",
                connection_id,
                str(e),
            )
            raise WebSocketException(code=1011, reason=f"Connection failed: {str(e)}")

    async def ensure_connection(
        self,
        connection_id: UUID,
        auth_token: Optional[str] = None,
        external_url: Optional[str] = None,
    ) -> None:
        """
        Ensures a connection exists, establishing it if necessary
        """
        if connection_id not in self.ws_connections:
            await self.establish_ws_connection(connection_id, auth_token, external_url)

    @override
    async def disconnect(self, connection_id: UUID):
        """Remove all connections for a given ID"""
        if connection_id in self.ws_connections:
            await self.ws_connections[connection_id].close()
            del self.ws_connections[connection_id]

    ########################### WEBSOCKET HANDLING - MESSAGING ###########################
    async def _handle_messages_loop(self, connection_id: UUID, websocket: ws_client.ClientConnection):
        """Handle incoming websocket messages in a loop"""

        logger.info("duplex.ws.loop_start connection_id=%s", connection_id)
        try:
            while True:
                if websocket.state == ws_protocol.State.CLOSED:
                    logger.warning(
                        "duplex.ws.loop_exit connection_id=%s reason=socket_closed state=%s",
                        connection_id,
                        websocket.state.name,
                    )
                    break

                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    await self.handle_data(connection_id, data)

                    # Add state check after message processing
                    if websocket.state != ws_protocol.State.OPEN:
                        logger.warning(
                            "duplex.ws.loop_exit connection_id=%s reason=state_changed state=%s",
                            connection_id,
                            websocket.state.name,
                        )
                        break
                except asyncio.CancelledError:
                    logger.warning(
                        "duplex.ws.loop_exit connection_id=%s reason=cancelled",
                        connection_id,
                    )
                    break
                except ConnectionClosed as e:
                    logger.warning(
                        "duplex.ws.disconnect connection_id=%s code=%s reason=%s",
                        connection_id,
                        getattr(e, "code", None),
                        getattr(e, "reason", None),
                    )
                    break
                except json.JSONDecodeError as e:
                    logger.error(
                        "duplex.ws.json_decode_error connection_id=%s error=%s",
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

        except Exception as e:
            logger.error(
                "duplex.ws.loop_error connection_id=%s error=%s",
                connection_id,
                str(e),
                exc_info=True,
            )
            raise WebSocketException(
                code=status.WS_1011_INTERNAL_ERROR,
                reason=f"Fatal error in message loop: {str(e)}",
            )
        else:
            logger.info(
                "duplex.ws.loop_exit connection_id=%s reason=ended state=%s",
                connection_id,
                websocket.state.name,
            )
        finally:
            logger.debug(
                "duplex.ws.cleanup connection_id=%s state=%s",
                connection_id,
                websocket.state.name,
            )
            await self.disconnect(connection_id)

    @override
    async def _send_data(self, data: str, connection_id: UUID) -> bool:
        """Send data over WebSocket to Server"""
        # Ensure connection
        await self.ensure_connection(connection_id)

        # Send data
        if connection_id in self.ws_connections:
            connection = self.ws_connections[connection_id]
            await connection.send(data)
            return True
        return False

    ########################### WEBRTC HANDLING - CONNECTION ###########################
    async def establish_webrtc_connection(self, connection_id: UUID) -> None:
        """Establish a WebRTC connection"""

        async def send_ice_candidate_wrapper(candidate):
            """Wrapper to ensure we use the websocket from connect"""
            return await self.send_ice_candidate(connection_id, candidate)

        self.wrtc_connections[connection_id] = WebRTCClient(send_ice_candidates_func=send_ice_candidate_wrapper)
        await self.wrtc_connections[connection_id].create_offer()

    ########################### WEBRTC HANDLING - MESSAGING ###########################
    async def handle_wrtc_connection_messages(
        self, request: Union[WsRTCOfferRequest, WsRTCResponse], connection_id: UUID
    ):
        """Overrides base class to handle WebRTC specific messages for connection at server side

        NOTE: For now only wrtc offer is supported.
        """
        wrtc_client = self.wrtc_connections.get(connection_id)
        if not wrtc_client:
            raise WebSocketException(code=status.WS_1011_INTERNAL_ERROR, reason="WebRTC handler not found")

        if not isinstance(request, WsRTCResponse):
            raise WebSocketException(
                code=status.WS_1003_UNSUPPORTED_DATA,
                reason="Unsupported WebRTC endpoint",
            )

        await wrtc_client.handle_webrtc_response(request.answer_session_description)
        return None

    def _handle_task_completion(self, connection_id: UUID):
        def callback(task: asyncio.Task):
            try:
                result = task.result()
                logger.debug(
                    "duplex.ws.loop_task_completed connection_id=%s result=%s",
                    connection_id,
                    result,
                )
            except asyncio.CancelledError:
                logger.warning(
                    "duplex.ws.loop_task_cancelled connection_id=%s",
                    connection_id,
                )
            except Exception as e:
                logger.error(
                    "duplex.ws.loop_task_error connection_id=%s error=%s",
                    connection_id,
                    str(e),
                    exc_info=True,
                )

        return callback
