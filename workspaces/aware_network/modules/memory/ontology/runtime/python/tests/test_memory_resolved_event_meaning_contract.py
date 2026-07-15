from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from ._memory_module_proof_paths import extend_sys_path_for_memory_tests


extend_sys_path_for_memory_tests()

from aware_memory.handlers.impl.memory.memory_working_event_frame import (
    record_resolved_meaning,
)
from aware_memory.handlers.impl.memory.memory_working_event_meaning import (
    build_via_memory_working_event_frame,
)
from aware_memory_ontology.memory.memory_working_event_frame import (
    MemoryWorkingEventFrame,
)
from aware_memory_ontology.memory.memory_working_event_meaning import (
    MemoryWorkingEventMeaning,
)
from aware_memory_ontology.stable_ids import stable_memory_working_event_meaning_id


def _resolver_evidence(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "resolver_api_call_outcome_id": uuid4(),
        "meaning_text": "Conversation message created",
        "resolver_status": "succeeded",
        "resolver_endpoint_ref": "conversation.memory.resolve_event_meaning",
        "resolver_discriminant": "conversation.message.created",
        "resolver_program_impl_instruction_intent_id": uuid4(),
        "resolver_action_config_id": uuid4(),
        "resolver_api_capability_endpoint_id": uuid4(),
        "resolver_api_call_id": uuid4(),
        "resolver_api_call_key": uuid4(),
        "resolver_request_model_id": uuid4(),
        "resolver_response_model_id": uuid4(),
        "resolver_response_class_config_id": uuid4(),
        "resolver_service_operation_id": uuid4(),
        "resolver_service_operation_config_id": uuid4(),
        "resolver_service_operation_commit_id": uuid4(),
        "resolver_service_operation_head_commit_id": uuid4(),
        "resolver_service_operation_branch_id": uuid4(),
        "resolver_service_operation_projection_hash": "sha256:service-operation",
        "resolver_api_call_outcome_commit_id": uuid4(),
        "resolver_api_call_outcome_head_commit_id": uuid4(),
        "resolver_api_call_outcome_branch_id": uuid4(),
        "resolver_api_call_outcome_projection_hash": "sha256:api-call-outcome",
        "provider_reference": "conversation:message:123",
    }
    values.update(overrides)
    return values


@pytest.mark.asyncio
async def test_build_resolved_event_meaning_normalizes_and_pins_terminal_evidence() -> None:
    event_frame_id = uuid4()
    evidence = _resolver_evidence(
        meaning_text="  Conversation message created  ",
        resolver_endpoint_ref="  conversation.memory.resolve_event_meaning  ",
    )

    meaning = await build_via_memory_working_event_frame(
        memory_working_event_frame_id=event_frame_id,
        **evidence,
    )

    assert meaning.id == stable_memory_working_event_meaning_id(
        memory_working_event_frame_id=event_frame_id,
        resolver_api_call_outcome_id=evidence["resolver_api_call_outcome_id"],
    )
    assert meaning.meaning_text == "Conversation message created"
    assert meaning.resolver_status == "succeeded"
    assert meaning.resolver_endpoint_ref == (
        "conversation.memory.resolve_event_meaning"
    )
    assert meaning.resolved_at.tzinfo is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (("meaning_text", "  "), ("resolver_status", "failed")),
)
async def test_build_resolved_event_meaning_rejects_non_terminal_result(
    field_name: str,
    field_value: str,
) -> None:
    evidence = _resolver_evidence(**{field_name: field_value})

    with pytest.raises(ValueError):
        await build_via_memory_working_event_frame(
            memory_working_event_frame_id=uuid4(),
            **evidence,
        )


@pytest.mark.asyncio
async def test_record_resolved_event_meaning_is_exact_retry_idempotent_and_unique(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_frame = MemoryWorkingEventFrame(id=uuid4(), event_id=uuid4())
    resolved_at = datetime.now(timezone.utc)
    evidence = _resolver_evidence(resolved_at=resolved_at)

    async def _build(
        cls: type[MemoryWorkingEventMeaning],
        memory_working_event_frame_id: UUID,
        **kwargs: object,
    ) -> MemoryWorkingEventMeaning:
        del cls
        return await build_via_memory_working_event_frame(
            memory_working_event_frame_id=memory_working_event_frame_id,
            **kwargs,
        )

    monkeypatch.setattr(
        MemoryWorkingEventMeaning,
        "build_via_memory_working_event_frame",
        classmethod(_build),
    )

    created = await record_resolved_meaning(event_frame, **evidence)
    retried = await record_resolved_meaning(event_frame, **evidence)

    assert retried is created
    assert event_frame.resolved_meaning is created

    with pytest.raises(ValueError, match="different resolved meaning"):
        await record_resolved_meaning(
            event_frame,
            **_resolver_evidence(resolved_at=resolved_at),
        )
