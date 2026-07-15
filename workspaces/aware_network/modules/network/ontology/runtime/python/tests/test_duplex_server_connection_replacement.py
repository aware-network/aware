# @code-under-test: ../aware_network/communications/duplex/server.py

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import status
from starlette.websockets import WebSocketState

from aware_network_service_dto.comms.models.network import NetworkAppType
from aware_comms.duplex.websocket.models import WsMessageFrame, WsMessageFrameType
from aware_network.communications.duplex import server as server_module
from aware_network.communications.duplex.server import NetworkDuplexServer


class _DummyWsConfig:
    requires_auth = False
    internal = False


class _DummyWsConnection:
    config = _DummyWsConfig()


class _FakeWebSocket:
    client_state = WebSocketState.CONNECTED
    application_state = WebSocketState.CONNECTED

    def __init__(self) -> None:
        self.accepted = False
        self.close_code: int | None = None
        self.close_count = 0

    async def accept(self) -> None:
        self.accepted = True

    async def close(self, code: int = status.WS_1000_NORMAL_CLOSURE) -> None:
        self.close_code = code
        self.close_count += 1
        self.application_state = WebSocketState.DISCONNECTED


class _TestDuplexServer(NetworkDuplexServer):
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


@pytest.fixture
def duplex_server(monkeypatch: pytest.MonkeyPatch) -> _TestDuplexServer:
    monkeypatch.setattr(
        server_module.ws_registry,
        "get_connection",
        lambda *_args, **_kwargs: _DummyWsConnection(),
    )
    return _TestDuplexServer(
        client_type=NetworkAppType.network_node.value,
        server_type=NetworkAppType.environment.value,
    )


@pytest.mark.asyncio
async def test_duplex_server_rejects_duplicate_ws_while_request_active(
    duplex_server: _TestDuplexServer,
) -> None:
    connection_id = uuid4()
    existing = _FakeWebSocket()
    duplicate = _FakeWebSocket()
    duplex_server.ws_connections[connection_id] = existing
    duplex_server.ws_active_request_counts[connection_id] = 1

    await duplex_server.connect(connection_id=connection_id, websocket=duplicate)

    assert duplex_server.ws_connections[connection_id] is existing
    assert existing.close_count == 0
    assert duplicate.accepted is True
    assert duplicate.close_count == 1
    assert duplicate.close_code == getattr(
        status,
        "WS_1013_TRY_AGAIN_LATER",
        status.WS_1012_SERVICE_RESTART,
    )


@pytest.mark.asyncio
async def test_duplex_server_replaces_idle_ws_connection(
    duplex_server: _TestDuplexServer,
) -> None:
    connection_id = uuid4()
    existing = _FakeWebSocket()
    replacement = _FakeWebSocket()
    duplex_server.ws_connections[connection_id] = existing

    await duplex_server.connect(connection_id=connection_id, websocket=replacement)

    assert duplex_server.ws_connections[connection_id] is replacement
    assert replacement.accepted is True
    assert existing.close_count == 1
    assert existing.close_code == getattr(
        status,
        "WS_1012_SERVICE_RESTART",
        status.WS_1001_GOING_AWAY,
    )
    assert duplex_server.ws_active_request_counts == {}


def test_duplex_server_tracks_ws_request_activity(
    duplex_server: _TestDuplexServer,
) -> None:
    connection_id = uuid4()

    duplex_server._mark_ws_request_active(connection_id)
    duplex_server._mark_ws_request_active(connection_id)
    duplex_server._mark_ws_request_finished(connection_id)

    assert duplex_server.ws_active_request_counts[connection_id] == 1

    duplex_server._mark_ws_request_finished(connection_id)

    assert connection_id not in duplex_server.ws_active_request_counts
