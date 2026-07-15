from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from aware_code.types.json import JsonObject
from aware_experience_service_dto.experience.program import (
    SubmitProgramTurnRequest,
    SubmitProgramTurnResponse,
)
from aware_experience.program import operations as program_operations


def _submit_program_turn_request() -> SubmitProgramTurnRequest:
    return SubmitProgramTurnRequest(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=None,
        projection_hash=None,
        target_actor_id=uuid4(),
        program_ref="conversation_default:HumanConversationMessage_v1",
        symbols=JsonObject({"plan.message_text": "hello"}),
        message="hello",
        turn_index=1,
        mailbox_key="mailbox:test",
        idempotency_key=None,
        max_attempts=1,
        wait_for_terminal=False,
    )


def _submit_program_turn_response(
    request: SubmitProgramTurnRequest,
) -> SubmitProgramTurnResponse:
    return SubmitProgramTurnResponse(
        actor_id=request.actor_id,
        environment_id=request.environment_id,
        process_id=request.process_id,
        thread_id=request.thread_id,
        branch_id=request.branch_id,
        projection_hash=request.projection_hash,
        status="accepted",
        error=None,
        turn_id=uuid4(),
        mailbox_key=request.mailbox_key,
        deduped=False,
    )


@pytest.mark.asyncio
async def test_run_program_requires_injected_submit_program_turn_op() -> None:
    with pytest.raises(RuntimeError, match="Experience-owned submit turn"):
        await program_operations.run_program(
            resolver=object(),
            request=_submit_program_turn_request(),
        )


@pytest.mark.asyncio
async def test_run_program_uses_injected_submit_program_turn_op() -> None:
    resolver = object()
    apply_program_ref_op = object()
    store = object()
    request = _submit_program_turn_request()
    expected_response = _submit_program_turn_response(request)
    captured: dict[str, Any] = {}

    async def _submit(
        resolver: Any,
        request: SubmitProgramTurnRequest,
        *,
        apply_program_ref_op: object = object(),
        store: Any | None = None,
    ) -> SubmitProgramTurnResponse:
        captured["resolver"] = resolver
        captured["request"] = request
        captured["apply_program_ref_op"] = apply_program_ref_op
        captured["store"] = store
        return expected_response

    response = await program_operations.run_program(
        resolver=resolver,
        request=request,
        apply_program_ref_op=apply_program_ref_op,
        store=store,
        submit_program_turn_op=_submit,
    )

    assert response is expected_response
    assert captured == {
        "resolver": resolver,
        "request": request,
        "apply_program_ref_op": apply_program_ref_op,
        "store": store,
    }


def test_program_operations_source_has_no_deprecated_turn_bridge() -> None:
    source = Path(str(program_operations.__file__)).read_text()

    assert "environment.operation.ops.turns" not in source
    assert "import_module(" not in source
