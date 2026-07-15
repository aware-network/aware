# @code-under-test: ../aware_network/communications/interface_session_binding_manager.py

import asyncio
from uuid import UUID, uuid4

import pytest

from aware_network.communications.interface_session_binding_manager import (
    InterfaceSessionBindingManager,
)
from aware_network.network.node.manager import network_node_manager


@pytest.fixture(autouse=True)
def _reset_binding_manager(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    manager = InterfaceSessionBindingManager.instance()
    manager._bindings.clear()
    manager._bindings_by_session_token.clear()
    network_node_manager._local_info_cache = None
    monkeypatch.setenv("AWARE_NETWORK_NODE_INFO_ROOT", str(tmp_path))


@pytest.mark.asyncio
async def test_register_connection_creates_binding() -> None:
    manager = InterfaceSessionBindingManager.instance()

    connection_id = uuid4()
    payload = {
        "interface_id": str(uuid4()),
        "interface_session_id": str(uuid4()),
        "identity_id": str(uuid4()),
        "session_label": "Studio Desktop",
    }

    context = await manager.register_connection(connection_id=connection_id, payload=payload)

    assert context.connection_id == connection_id
    assert context.interface_id == UUID(payload["interface_id"])
    assert context.interface_session_id == UUID(payload["interface_session_id"])
    assert context.identity_id == UUID(payload["identity_id"])
    assert context.interface_session_network_binding_id is not None
    assert connection_id in manager._bindings


@pytest.mark.asyncio
async def test_heartbeat_and_disconnect_update_context() -> None:
    manager = InterfaceSessionBindingManager.instance()

    connection_id = uuid4()
    payload = {
        "interface_id": str(uuid4()),
        "interface_session_id": str(uuid4()),
        "identity_id": str(uuid4()),
    }
    context = await manager.register_connection(connection_id=connection_id, payload=payload)

    previous = context.last_seen_at
    await asyncio.sleep(0)
    await manager.record_heartbeat(connection_id=connection_id)
    assert context.last_seen_at >= previous

    await manager.disconnect(connection_id=connection_id)
    assert connection_id not in manager._bindings
