from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_experience.handlers.impl.impl import (
    program_impl_instruction_intent as intent_handler,
)
from aware_experience.handlers.impl.impl import (
    program_impl_instruction_intent_activation_field_binding as activation_handler,
)
from aware_experience.handlers.impl.impl import (
    program_impl_instruction_intent_outcome_field_binding as outcome_handler,
)
from aware_experience.handlers.impl.impl import (
    program_impl_instruction_intent_receipt_field_binding as receipt_handler,
)
from aware_experience.stable_ids import (
    stable_program_impl_instruction_intent_activation_field_binding_id,
    stable_program_impl_instruction_intent_outcome_field_binding_id,
    stable_program_impl_instruction_intent_receipt_field_binding_id,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent import (
    ProgramImplInstructionIntent,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent_activation_field_binding import (
    ProgramImplInstructionIntentActivationFieldBinding,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig


class _Session:
    def __init__(self) -> None:
        self._instances: dict[tuple[type[object], UUID], object] = {}

    def imap_get(self, model: type[object], object_id: UUID) -> object | None:
        return self._instances.get((model, object_id))

    def put(self, value: object) -> None:
        self._instances[(type(value), getattr(value, "id"))] = value


@pytest.mark.asyncio
async def test_continuation_binding_constructors_are_stable_and_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    for module in (activation_handler, outcome_handler, receipt_handler):
        monkeypatch.setattr(module, "current_handler_session", lambda: session)

    target_intent = ProgramImplInstructionIntent.model_construct(
        id=uuid4(),
        action_config_id=uuid4(),
        event_config_id=uuid4(),
    )
    source_intent = ProgramImplInstructionIntent.model_construct(
        id=uuid4(),
        action_config_id=uuid4(),
        event_config_id=uuid4(),
    )
    source_class = ClassConfig.model_construct(id=uuid4())
    receipt_class = ClassConfig.model_construct(id=uuid4())
    source_attribute = AttributeConfig.model_construct(id=uuid4())
    receipt_attribute = AttributeConfig.model_construct(id=uuid4())
    target_attribute = AttributeConfig.model_construct(id=uuid4())
    for value in (
        target_intent,
        source_intent,
        source_class,
        receipt_class,
        source_attribute,
        receipt_attribute,
        target_attribute,
    ):
        session.put(value)

    activation = await activation_handler.build_via_program_impl_instruction_intent(
        program_impl_instruction_intent_id=target_intent.id,
        source_class_config_id=source_class.id,
        source_attribute_config_id=source_attribute.id,
        target_request_attribute_config_id=target_attribute.id,
        source_input_key=" Semantic_Event ",
        position=0,
    )
    assert activation.id == (
        stable_program_impl_instruction_intent_activation_field_binding_id(
            program_impl_instruction_intent_id=target_intent.id,
            source_class_config_id=source_class.id,
            source_attribute_config_id=source_attribute.id,
            target_request_attribute_config_id=target_attribute.id,
            source_input_key="semantic_event",
        )
    )
    assert activation.source_input_key == "semantic_event"
    session.put(activation)
    assert (
        await activation_handler.build_via_program_impl_instruction_intent(
            program_impl_instruction_intent_id=target_intent.id,
            source_class_config_id=source_class.id,
            source_attribute_config_id=source_attribute.id,
            target_request_attribute_config_id=target_attribute.id,
            source_input_key="semantic_event",
            position=0,
        )
        is activation
    )
    with pytest.raises(RuntimeError, match="payload mismatch"):
        _ = await activation_handler.build_via_program_impl_instruction_intent(
            program_impl_instruction_intent_id=target_intent.id,
            source_class_config_id=source_class.id,
            source_attribute_config_id=source_attribute.id,
            target_request_attribute_config_id=target_attribute.id,
            source_input_key="semantic_event",
            required=False,
            position=0,
        )

    outcome = await outcome_handler.build_via_program_impl_instruction_intent(
        program_impl_instruction_intent_id=target_intent.id,
        source_program_impl_instruction_intent_id=source_intent.id,
        source_response_attribute_config_id=source_attribute.id,
        target_request_attribute_config_id=target_attribute.id,
        position=1,
    )
    assert (
        outcome.id
        == stable_program_impl_instruction_intent_outcome_field_binding_id(
            program_impl_instruction_intent_id=target_intent.id,
            source_program_impl_instruction_intent_id=source_intent.id,
            source_response_attribute_config_id=source_attribute.id,
            target_request_attribute_config_id=target_attribute.id,
        )
    )

    receipt = await receipt_handler.build_via_program_impl_instruction_intent(
        program_impl_instruction_intent_id=target_intent.id,
        source_program_impl_instruction_intent_id=source_intent.id,
        source_receipt_class_config_id=receipt_class.id,
        source_receipt_attribute_config_id=receipt_attribute.id,
        target_request_attribute_config_id=target_attribute.id,
        position=2,
    )
    assert (
        receipt.id
        == stable_program_impl_instruction_intent_receipt_field_binding_id(
            program_impl_instruction_intent_id=target_intent.id,
            source_program_impl_instruction_intent_id=source_intent.id,
            source_receipt_class_config_id=receipt_class.id,
            source_receipt_attribute_config_id=receipt_attribute.id,
            target_request_attribute_config_id=target_attribute.id,
        )
    )


@pytest.mark.asyncio
async def test_intent_handler_attaches_activation_binding_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intent = ProgramImplInstructionIntent.model_construct(
        id=uuid4(),
        action_config_id=uuid4(),
        event_config_id=uuid4(),
        activation_field_bindings=[],
        outcome_field_bindings=[],
        receipt_field_bindings=[],
    )
    binding = ProgramImplInstructionIntentActivationFieldBinding.model_construct(
        id=uuid4(),
        program_impl_instruction_intent_id=intent.id,
        source_class_config_id=uuid4(),
        source_attribute_config_id=uuid4(),
        target_request_attribute_config_id=uuid4(),
        source_input_key="semantic_event",
        required=True,
        position=0,
    )

    async def _build(
        **_kwargs: object,
    ) -> ProgramImplInstructionIntentActivationFieldBinding:
        return binding

    monkeypatch.setattr(
        ProgramImplInstructionIntentActivationFieldBinding,
        "build_via_program_impl_instruction_intent",
        _build,
    )

    async def _attach() -> ProgramImplInstructionIntentActivationFieldBinding:
        return await intent_handler.add_activation_field_binding(
            program_impl_instruction_intent=intent,
            source_class_config_id=binding.source_class_config_id,
            source_attribute_config_id=binding.source_attribute_config_id,
            target_request_attribute_config_id=(
                binding.target_request_attribute_config_id
            ),
            source_input_key=binding.source_input_key,
            position=binding.position,
        )

    assert await _attach() is binding
    assert await _attach() is binding
    assert intent.activation_field_bindings == [binding]
