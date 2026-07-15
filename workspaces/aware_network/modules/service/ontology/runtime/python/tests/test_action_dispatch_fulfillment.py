from __future__ import annotations

from uuid import uuid4

import pytest

from aware_service_runtime.action_dispatch_fulfillment import (
    ServiceHostActionTerminalFulfillmentInvoker,
)


class _Client:
    def __init__(self) -> None:
        self.request = None
        self.timeout_s = None

    async def send_api_ingress_request(self, *, request, timeout_s=None):
        self.request = request
        self.timeout_s = timeout_s
        return {"status": "succeeded"}


@pytest.mark.asyncio
async def test_service_host_action_fulfillment_preserves_api_call_key() -> None:
    actor_id = uuid4()
    api_call_key = uuid4()
    client = _Client()
    invoker = ServiceHostActionTerminalFulfillmentInvoker(
        actor_id=actor_id,
        client_factory=lambda: client,
        request_timeout_s=7.5,
        invocation_context={"source": "experience.action_dispatch"},
    )

    response = await invoker.invoke_action_endpoint(
        endpoint_ref="memory.remember_event.remember_event",
        discriminant="memory.remember_event.remember_event",
        request_values={"event_id": str(uuid4())},
        api_call_key=api_call_key,
    )

    assert response == {"status": "succeeded"}
    assert client.request is not None
    assert client.request.actor_id == actor_id
    assert client.request.network_request_id == api_call_key
    assert client.request.request_payload["event_id"]
    assert client.request.invocation_context == {"source": "experience.action_dispatch"}
    assert client.timeout_s == 7.5
