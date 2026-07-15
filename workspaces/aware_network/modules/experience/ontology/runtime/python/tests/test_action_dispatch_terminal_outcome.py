from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_experience.action_dispatch.fulfillment import (
    ActionTerminalFulfillmentError,
    invoke_terminal_action_fulfillment,
)


class _Invoker:
    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    async def invoke_action_endpoint(self, **kwargs: object) -> object:
        self.calls.append(dict(kwargs))
        return self.response


def _response(
    *,
    endpoint_ref: str,
    endpoint_id,
    call_key,
    api_call_id,
    response_model_id=None,
    status: str = "succeeded",
    include_api_call_outcome: bool = True,
) -> object:
    receipt_values = {
        "endpoint_ref": endpoint_ref,
        "discriminant": endpoint_ref,
        "status": status,
        "api_call_id": api_call_id,
        "api_capability_endpoint_id": endpoint_id,
        "call_key": call_key,
        "request_model_id": uuid4(),
        "response_model_id": response_model_id,
        "service_operation_id": uuid4(),
    }
    if include_api_call_outcome:
        receipt_values["api_call_outcome_id"] = uuid4()
    return SimpleNamespace(
        status=status,
        response_payload={"ok": True} if status == "succeeded" else None,
        error=None if status == "succeeded" else "provider_failed",
        receipt=SimpleNamespace(**receipt_values),
    )


@pytest.mark.asyncio
async def test_terminal_fulfillment_requires_matching_committed_receipt() -> None:
    endpoint_ref = "memory.remember_event.remember_event"
    endpoint_id = uuid4()
    call_key = uuid4()
    api_call_id = uuid4()
    response_model_id = uuid4()
    invoker = _Invoker(
        _response(
            endpoint_ref=endpoint_ref,
            endpoint_id=endpoint_id,
            call_key=call_key,
            api_call_id=api_call_id,
            response_model_id=response_model_id,
        )
    )

    outcome = await invoke_terminal_action_fulfillment(
        invoker=invoker,
        endpoint_ref=endpoint_ref,
        discriminant=endpoint_ref,
        request_values={"event_id": str(uuid4())},
        api_call_key=call_key,
        expected_api_call_id=api_call_id,
        expected_api_capability_endpoint_id=endpoint_id,
        response_class_config_id=uuid4(),
    )

    assert outcome.succeeded is True
    assert outcome.api_call_key == call_key
    assert outcome.response_model_id == response_model_id
    assert outcome.response_payload == {"ok": True}
    assert invoker.calls[0]["api_call_key"] == call_key


@pytest.mark.asyncio
async def test_terminal_fulfillment_rejects_mismatched_call_key() -> None:
    endpoint_ref = "memory.remember_event.remember_event"
    endpoint_id = uuid4()
    expected_call_key = uuid4()
    api_call_id = uuid4()
    invoker = _Invoker(
        _response(
            endpoint_ref=endpoint_ref,
            endpoint_id=endpoint_id,
            call_key=uuid4(),
            api_call_id=api_call_id,
        )
    )

    with pytest.raises(
        ActionTerminalFulfillmentError,
        match="action_terminal_fulfillment_api_call_key_mismatch",
    ):
        await invoke_terminal_action_fulfillment(
            invoker=invoker,
            endpoint_ref=endpoint_ref,
            discriminant=endpoint_ref,
            request_values={},
            api_call_key=expected_call_key,
            expected_api_call_id=api_call_id,
            expected_api_capability_endpoint_id=endpoint_id,
            response_class_config_id=None,
        )


@pytest.mark.asyncio
async def test_terminal_fulfillment_requires_typed_response_model() -> None:
    endpoint_ref = "memory.remember_event.remember_event"
    endpoint_id = uuid4()
    call_key = uuid4()
    api_call_id = uuid4()
    invoker = _Invoker(
        _response(
            endpoint_ref=endpoint_ref,
            endpoint_id=endpoint_id,
            call_key=call_key,
            api_call_id=api_call_id,
        )
    )

    with pytest.raises(
        ActionTerminalFulfillmentError,
        match="action_terminal_fulfillment_response_model_missing",
    ):
        await invoke_terminal_action_fulfillment(
            invoker=invoker,
            endpoint_ref=endpoint_ref,
            discriminant=endpoint_ref,
            request_values={},
            api_call_key=call_key,
            expected_api_call_id=api_call_id,
            expected_api_capability_endpoint_id=endpoint_id,
            response_class_config_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_terminal_fulfillment_requires_committed_api_call_outcome() -> None:
    endpoint_ref = "memory.remember_event.remember_event"
    endpoint_id = uuid4()
    call_key = uuid4()
    api_call_id = uuid4()
    invoker = _Invoker(
        _response(
            endpoint_ref=endpoint_ref,
            endpoint_id=endpoint_id,
            call_key=call_key,
            api_call_id=api_call_id,
            include_api_call_outcome=False,
        )
    )

    with pytest.raises(
        ActionTerminalFulfillmentError,
        match="action_terminal_fulfillment_api_call_outcome_id_missing",
    ):
        await invoke_terminal_action_fulfillment(
            invoker=invoker,
            endpoint_ref=endpoint_ref,
            discriminant=endpoint_ref,
            request_values={},
            api_call_key=call_key,
            expected_api_call_id=api_call_id,
            expected_api_capability_endpoint_id=endpoint_id,
            response_class_config_id=None,
        )


@pytest.mark.asyncio
async def test_terminal_fulfillment_rejects_mismatched_endpoint() -> None:
    endpoint_ref = "memory.remember_event.remember_event"
    endpoint_id = uuid4()
    call_key = uuid4()
    api_call_id = uuid4()
    invoker = _Invoker(
        _response(
            endpoint_ref="conversation.message.resolve_meaning",
            endpoint_id=endpoint_id,
            call_key=call_key,
            api_call_id=api_call_id,
        )
    )

    with pytest.raises(
        ActionTerminalFulfillmentError,
        match="action_terminal_fulfillment_endpoint_mismatch",
    ):
        await invoke_terminal_action_fulfillment(
            invoker=invoker,
            endpoint_ref=endpoint_ref,
            discriminant=endpoint_ref,
            request_values={},
            api_call_key=call_key,
            expected_api_call_id=api_call_id,
            expected_api_capability_endpoint_id=endpoint_id,
            response_class_config_id=None,
        )
