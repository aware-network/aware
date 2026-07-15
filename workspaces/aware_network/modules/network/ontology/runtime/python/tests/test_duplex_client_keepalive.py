# @code-under-test: ../aware_network/communications/duplex/client.py

from __future__ import annotations

from uuid import uuid4

import pytest

from aware_comms.duplex.websocket.models import WsMessageFrame, WsMessageFrameType
from aware_network_service_dto.comms.models.network import NetworkAppType
from aware_network.communications.duplex.client import NetworkDuplexClient


class _DummyWsConfig:
    requires_auth = False
    internal = False


class _DummyWsConnection:
    config = _DummyWsConfig()


class _TestDuplexClient(NetworkDuplexClient):
    def _build_message(
        self,
        message_type: WsMessageFrameType,
        data_serialized: str,
        request_id=None,
    ) -> WsMessageFrame:
        return WsMessageFrame(
            id=uuid4(),
            type=message_type,
            data=data_serialized,
            request_id=request_id,
        )


@pytest.mark.asyncio
async def test_duplex_client_uses_relaxed_keepalive_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def fake_connect(*, ping_interval, ping_timeout, **_kwargs):  # type: ignore[no-untyped-def]
        captured["ping_interval"] = ping_interval
        captured["ping_timeout"] = ping_timeout
        return object()

    async def noop_handle_loop(self, connection_id, websocket):  # type: ignore[no-untyped-def]
        _ = self, connection_id, websocket
        return None

    from aware_network.communications.duplex import client as client_module

    monkeypatch.setattr(
        client_module.ws_registry,
        "get_connection",
        lambda *_args, **_kwargs: _DummyWsConnection(),
    )
    monkeypatch.setattr(client_module.ws_client, "connect", fake_connect)
    monkeypatch.setattr(NetworkDuplexClient, "_handle_messages_loop", noop_handle_loop)

    client = _TestDuplexClient(
        client_type=NetworkAppType.network_node.value, server_type=NetworkAppType.environment.value
    )
    await client.establish_ws_connection(connection_id=uuid4(), external_url="ws://127.0.0.1:9999")

    assert captured["ping_interval"] == 20
    assert captured["ping_timeout"] == 120


@pytest.mark.asyncio
async def test_duplex_client_keepalive_env_vars_allow_disabling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def fake_connect(*, ping_interval, ping_timeout, **_kwargs):  # type: ignore[no-untyped-def]
        captured["ping_interval"] = ping_interval
        captured["ping_timeout"] = ping_timeout
        return object()

    async def noop_handle_loop(self, connection_id, websocket):  # type: ignore[no-untyped-def]
        _ = self, connection_id, websocket
        return None

    from aware_network.communications.duplex import client as client_module

    monkeypatch.setenv("AWARE_DUPLEX_WS_PING_INTERVAL_S", "0")
    monkeypatch.setenv("AWARE_DUPLEX_WS_PING_TIMEOUT_S", "none")

    monkeypatch.setattr(
        client_module.ws_registry,
        "get_connection",
        lambda *_args, **_kwargs: _DummyWsConnection(),
    )
    monkeypatch.setattr(client_module.ws_client, "connect", fake_connect)
    monkeypatch.setattr(NetworkDuplexClient, "_handle_messages_loop", noop_handle_loop)

    client = _TestDuplexClient(
        client_type=NetworkAppType.network_node.value, server_type=NetworkAppType.environment.value
    )
    await client.establish_ws_connection(connection_id=uuid4(), external_url="ws://127.0.0.1:9999")

    assert captured["ping_interval"] is None
    assert captured["ping_timeout"] is None
