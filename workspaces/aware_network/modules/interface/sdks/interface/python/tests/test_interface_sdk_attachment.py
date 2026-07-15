from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_network_service_dto.comms.models.network_node import InterfaceSessionRegisterResponse
from aware_interface_sdk.attachment import create_interface_attachment


@pytest.mark.asyncio
async def test_interface_sdk_attachment_creates_interface_transport_profile(
    tmp_path,
) -> None:
    actor_id = uuid4()
    client = SimpleNamespace(
        config=SimpleNamespace(
            endpoint="ws://example",
            actor_id=actor_id,
            context=None,
        ),
        get_context=lambda: None,
    )

    attachment = await create_interface_attachment(
        client=client,
        state_home=tmp_path,
        namespace="sdk-attachment-test",
        endpoint="ws://example",
        host_label="sdk-host",
        capabilities=("interface.api",),
        persist_interface_id=True,
    )

    assert attachment.interface_id is not None
    assert attachment.transport_session.profile.interface_id == attachment.interface_id
    assert attachment.transport_session.profile.session_label == "sdk-host"
    assert attachment.transport_session.profile.capabilities == ("interface.api",)


@pytest.mark.asyncio
async def test_interface_sdk_transport_registration_carries_current_actor_id(
    tmp_path,
) -> None:
    actor_id = uuid4()
    observed: dict[str, object] = {}

    class _Client:
        config = SimpleNamespace(
            endpoint="ws://example",
            actor_id=actor_id,
            context=None,
        )

        async def ensure_interface_session_registered(
            self,
            *,
            profile,
        ) -> InterfaceSessionRegisterResponse:
            observed["profile"] = profile
            return InterfaceSessionRegisterResponse(
                actor_id=profile.actor_id,
                node_id=uuid4(),
                status="succeeded",
                error=None,
                interface_id=profile.interface_id,
                interface_session_id=profile.interface_session_id,
                interface_identity_network_node_id=uuid4(),
                interface_session_network_binding_id=uuid4(),
                last_seen_at="2026-05-29T00:00:00Z",
                protocol_version=profile.protocol_version,
            )

    attachment = await create_interface_attachment(
        client=_Client(),
        state_home=tmp_path,
        namespace="sdk-attachment-test",
        endpoint="ws://example",
        host_label="sdk-host",
        capabilities=("interface.api",),
        persist_interface_id=True,
    )

    binding = await attachment.transport_session.ensure_registered()
    profile = observed["profile"]

    assert profile.actor_id == actor_id
    assert binding.actor_id == actor_id


@pytest.mark.asyncio
async def test_interface_sdk_attachment_reuses_persisted_interface_id(
    tmp_path,
) -> None:
    actor_id = uuid4()
    client = SimpleNamespace(
        config=SimpleNamespace(
            endpoint="ws://example",
            actor_id=actor_id,
            context=None,
        ),
        get_context=lambda: None,
    )

    first = await create_interface_attachment(
        client=client,
        state_home=tmp_path,
        namespace="sdk-attachment-test",
        endpoint="ws://example",
        host_label="sdk-host",
        capabilities=(),
        persist_interface_id=True,
    )
    second = await create_interface_attachment(
        client=client,
        state_home=tmp_path,
        namespace="sdk-attachment-test",
        endpoint="ws://example",
        host_label="sdk-host",
        capabilities=(),
        persist_interface_id=True,
    )

    assert second.interface_id == first.interface_id
