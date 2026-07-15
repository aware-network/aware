from __future__ import annotations

from uuid import UUID

import pytest
from websockets.asyncio import client as ws_client

from aware_comms.duplex import client as client_mod
from aware_comms.duplex.client import DuplexClient


@pytest.mark.asyncio
async def test_network_duplex_client_honors_explicit_external_url_without_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    connection_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    class _FakeWebSocket:
        async def send(self, data: str) -> None:
            captured["sent"] = data

        async def close(self) -> None:
            captured["closed"] = True

    async def _connect(**kwargs: object) -> _FakeWebSocket:
        captured.update(kwargs)
        return _FakeWebSocket()

    async def _handle_messages_loop(
        _self: DuplexClient,
        connection_id: UUID,
        websocket: object,
    ) -> None:
        captured["loop_connection_id"] = connection_id
        captured["loop_websocket"] = websocket

    monkeypatch.setattr(ws_client, "connect", _connect)
    monkeypatch.setattr(
        client_mod.DuplexClient,
        "_handle_messages_loop",
        _handle_messages_loop,
    )

    client = DuplexClient(
        client_type="network_node",
        server_type="network_node",
    )

    await client.ensure_connection(
        connection_id,
        external_url="http://127.0.0.1:8951/",
    )

    assert captured["uri"] == (
        "ws://127.0.0.1:8951/network_node/network_node"
        f"?connection_id={connection_id}"
    )
    assert connection_id in client.ws_connections
