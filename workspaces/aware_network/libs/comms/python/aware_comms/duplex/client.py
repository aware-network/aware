"""Client-side duplex implementation for aware-comms."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import cast, override
from urllib.parse import urlparse, urlunparse
from uuid import UUID

from websockets import protocol as ws_protocol, ConnectionClosed
from websockets.asyncio import client as ws_client

from aware_comms.duplex.base import DuplexSide
from aware_comms.duplex.duplex import Duplex

logger = logging.getLogger(__name__)


class DuplexClient(Duplex[ws_client.ClientConnection, object]):
    """Async websocket client that utilises the aware-comms duplex primitives."""

    side: DuplexSide = DuplexSide.CLIENT

    async def establish_ws_connection(
        self,
        connection_id: UUID,
        *,
        external_url: str,
        auth_token: str | None = None,
    ) -> None:
        if connection_id in self.ws_connections:
            logger.debug("Connection %s already established", connection_id)
            return

        remote_url = (
            f"{_normalize_external_url(external_url)}/{self.get_net_endpoint()}"
        )
        headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else None

        url_with_params = f"{remote_url}?connection_id={connection_id}"
        logger.info("Connecting to %s", url_with_params)
        websocket = await ws_client.connect(
            uri=url_with_params,
            additional_headers=headers,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10,
            max_size=None,
        )
        self.ws_connections[connection_id] = websocket
        task = asyncio.create_task(self._handle_messages_loop(connection_id, websocket))
        task.add_done_callback(lambda fut: fut.exception())

    async def ensure_connection(
        self,
        connection_id: UUID,
        *,
        external_url: str,
        auth_token: str | None = None,
    ) -> None:
        if connection_id not in self.ws_connections:
            await self.establish_ws_connection(
                connection_id,
                external_url=external_url,
                auth_token=auth_token,
            )

    async def _handle_messages_loop(
        self, connection_id: UUID, websocket: ws_client.ClientConnection
    ) -> None:
        try:
            while True:
                if websocket.state == ws_protocol.State.CLOSED:
                    break
                try:
                    message = await websocket.recv()
                except ConnectionClosed as exc:
                    logger.info(
                        "Websocket closed for %s: %s / %s",
                        connection_id,
                        exc.code,
                        exc.reason,
                    )
                    break
                except asyncio.CancelledError:
                    logger.info("Message loop cancelled for %s", connection_id)
                    break

                try:
                    parsed = cast(object, json.loads(message))
                except json.JSONDecodeError:
                    logger.error("Invalid JSON payload from %s", connection_id)
                    continue

                if not isinstance(parsed, dict):
                    logger.error("Invalid JSON object payload from %s", connection_id)
                    continue
                parsed_items = cast(dict[object, object], parsed).items()
                data: dict[str, object] = {
                    str(key): value for key, value in parsed_items
                }

                await self.handle_data(connection_id, data)

        finally:
            await self.disconnect(connection_id)

    @override
    async def _send_data(self, data: str, connection_id: UUID) -> bool:
        websocket = self.ws_connections.get(connection_id)
        if not websocket:
            return False
        await websocket.send(data)
        return True

    @override
    async def disconnect(self, connection_id: UUID) -> None:
        websocket = self.ws_connections.pop(connection_id, None)
        if websocket:
            await websocket.close()


def _normalize_external_url(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise ValueError("aware_comms client requires an external endpoint")
    if "://" not in raw:
        raw = f"ws://{raw}"
    parsed = urlparse(raw)
    scheme = parsed.scheme.lower()
    if scheme == "http":
        parsed = parsed._replace(scheme="ws")
    elif scheme == "https":
        parsed = parsed._replace(scheme="wss")
    elif scheme not in {"ws", "wss"}:
        message = (
            f"Unsupported aware_comms external endpoint scheme {parsed.scheme!r}; "
            "expected ws, wss, http, or https."
        )
        raise ValueError(message)
    return urlunparse(parsed).rstrip("/")
