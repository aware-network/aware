from __future__ import annotations

from typing import cast

import pytest

from aware_comms import (
    WsMessageFrame,
    WsMessageFrameType,
    ws_registry,
    WsConnection,
    WsConnectionConfig,
    WsConnectionRegistry,
)


def test_ws_message_frame_roundtrip() -> None:
    frame = WsMessageFrame(
        type=WsMessageFrameType.REQUEST,
        data='{"ping": "pong"}',
    )
    serialized = frame.model_dump()
    restored = WsMessageFrame.model_validate(serialized)
    assert restored.type is WsMessageFrameType.REQUEST
    assert restored.data == '{"ping": "pong"}'
    assert restored.request_id == frame.request_id


def test_ws_message_frame_defaults_empty_data() -> None:
    frame = WsMessageFrame(type=WsMessageFrameType.RESPONSE)

    assert frame.data == ""
    assert frame.payload is None


def test_ws_connection_registry_registration() -> None:
    custom = WsConnection(
        client="interface",
        server="environment",
        config=WsConnectionConfig(
            requires_auth=False,
            enable_ws=True,
            internal=False,
        ),
    )
    ws_registry.register_connection(custom)
    fetched = ws_registry.get_connection(
        "interface",
        "environment",
    )
    assert fetched is not None
    assert fetched.config.internal is False


def test_ws_connection_registry_has_no_builtin_product_topology() -> None:
    registry = WsConnectionRegistry()

    assert registry.connections == []
    assert registry.get_connection("interface", "network_node") is None


def test_ws_connection_requires_plain_string_route_keys() -> None:
    class _FakeEnum:
        value: str = "interface"

    with pytest.raises(TypeError, match="plain strings"):
        _ = WsConnection(
            client=cast(str, cast(object, _FakeEnum())),
            server="network_node",
            config=WsConnectionConfig(requires_auth=False, enable_ws=True),
        )
