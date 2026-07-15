from __future__ import annotations

from dataclasses import replace
from uuid import UUID, uuid4

import pytest

from aware_experience.action_dispatch.fulfillment import (
    ActionDispatchTerminalOutcome,
)
from aware_experience.program.action_continuation import (
    ProgramActionContinuationContract,
    ProgramActionContinuationFieldBinding,
    ProgramActionContinuationReceiptFieldBinding,
)
from aware_experience.program.action_continuation_graph import (
    ProgramActionContinuationActivationFieldBinding,
    ProgramActionContinuationActivationInput,
    ProgramActionContinuationCompositeResult,
    ProgramActionContinuationGraphError,
    ProgramActionContinuationGraphStep,
    ProgramActionContinuationOutcomeSource,
    execute_program_action_continuation_graph,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_enums import ClassValueMode


def _inline_class(
    *,
    name: str,
    fields: tuple[tuple[str, UUID, bool], ...],
) -> tuple[ClassConfig, dict[str, AttributeConfig]]:
    class_config = ClassConfig(
        id=uuid4(),
        name=name,
        class_fqn=f"aware_test.continuation_graph.{name}",
        value_mode=ClassValueMode.inline_value,
    )
    attributes: dict[str, AttributeConfig] = {}
    for position, (field_name, descriptor_id, required) in enumerate(fields):
        descriptor = AttributeTypeDescriptor(
            id=descriptor_id,
            kind=AttributeTypeDescriptorKind.primitive,
        )
        attribute = AttributeConfig(
            id=uuid4(),
            owner_key=class_config.class_fqn,
            name=field_name,
            is_required=required,
            type_descriptor=descriptor,
            type_descriptor_id=descriptor.id,
        )
        attributes[field_name] = attribute
        class_config.class_config_attribute_configs.append(
            ClassConfigAttributeConfig(
                id=uuid4(),
                class_config_id=class_config.id,
                attribute_config=attribute,
                attribute_config_id=attribute.id,
                position=position,
            )
        )
    return class_config, attributes


def _outcome(
    *,
    endpoint_id: UUID,
    response_class_config_id: UUID,
    response_payload: object,
    status: str = "succeeded",
) -> ActionDispatchTerminalOutcome:
    return ActionDispatchTerminalOutcome(
        status=status,
        endpoint_ref="test.endpoint",
        discriminant="test.endpoint",
        api_call_id=uuid4(),
        api_capability_endpoint_id=endpoint_id,
        api_call_key=uuid4(),
        request_model_id=uuid4(),
        api_call_outcome_id=uuid4(),
        response_model_id=uuid4(),
        response_class_config_id=response_class_config_id,
        service_operation_id=uuid4(),
        service_operation_config_id=uuid4(),
        service_operation_commit_id=uuid4(),
        service_operation_head_commit_id=uuid4(),
        service_operation_branch_id=uuid4(),
        service_operation_projection_hash="sha256:service",
        api_call_outcome_commit_id=uuid4(),
        api_call_outcome_head_commit_id=uuid4(),
        api_call_outcome_branch_id=uuid4(),
        api_call_outcome_projection_hash="sha256:outcome",
        response_payload=response_payload,
        error=None if status == "succeeded" else "dispatch_failed",
    )


def _contract(
    *,
    source_intent_id: UUID,
    target_intent_id: UUID,
    source_sequence: int,
    target_sequence: int,
    source_action_id: UUID,
    target_action_id: UUID,
    source_endpoint_id: UUID,
    target_endpoint_id: UUID,
    source_class: ClassConfig,
    target_class: ClassConfig,
    field_bindings: tuple[ProgramActionContinuationFieldBinding, ...],
    receipt_class: ClassConfig | None = None,
    receipt_field_bindings: tuple[
        ProgramActionContinuationReceiptFieldBinding, ...
    ] = (),
) -> ProgramActionContinuationContract:
    assert source_class.id is not None
    assert target_class.id is not None
    return ProgramActionContinuationContract(
        source_program_impl_instruction_intent_id=source_intent_id,
        target_program_impl_instruction_intent_id=target_intent_id,
        source_sequence=source_sequence,
        target_sequence=target_sequence,
        source_action_config_id=source_action_id,
        target_action_config_id=target_action_id,
        source_api_capability_endpoint_id=source_endpoint_id,
        target_api_capability_endpoint_id=target_endpoint_id,
        source_response_class_config_id=source_class.id,
        target_request_class_config_id=target_class.id,
        field_bindings=field_bindings,
        source_receipt_class_config_id=(
            receipt_class.id if receipt_class is not None else None
        ),
        receipt_field_bindings=receipt_field_bindings,
    )


@pytest.mark.asyncio
async def test_event_meaning_graph_composes_activation_and_two_outcomes() -> None:
    event_descriptor_id = uuid4()
    item_id_descriptor_id = uuid4()
    meaning_descriptor_id = uuid4()
    uuid_descriptor_id = uuid4()
    string_descriptor_id = uuid4()

    activation_class, activation_attributes = _inline_class(
        name="EventMeaningActivationInput",
        fields=(("event", event_descriptor_id, True),),
    )
    remember_response, remember_attributes = _inline_class(
        name="RememberEventContinuationResponse",
        fields=(("memory_working_item_id", item_id_descriptor_id, True),),
    )
    resolve_request, resolve_request_attributes = _inline_class(
        name="ReactivityEventMeaningResolutionRequest",
        fields=(("event", event_descriptor_id, True),),
    )
    resolve_response, resolve_response_attributes = _inline_class(
        name="ReactivityEventMeaningResolutionResponse",
        fields=(("resolved_meaning", meaning_descriptor_id, True),),
    )
    continuation_receipt, receipt_attributes = _inline_class(
        name="ProgramActionContinuationReceipt",
        fields=(
            ("status", string_descriptor_id, True),
            ("api_call_id", uuid_descriptor_id, True),
        ),
    )
    record_request, record_request_attributes = _inline_class(
        name="RecordResolvedEventMeaningRequest",
        fields=(
            ("memory_working_item_id", item_id_descriptor_id, True),
            ("resolved_meaning", meaning_descriptor_id, True),
            ("resolver_status", string_descriptor_id, True),
            ("resolver_api_call_id", uuid_descriptor_id, True),
        ),
    )
    record_response, _ = _inline_class(
        name="RecordResolvedEventMeaningResponse",
        fields=(("status", string_descriptor_id, True),),
    )

    remember_intent_id = uuid4()
    resolve_intent_id = uuid4()
    record_intent_id = uuid4()
    remember_action_id = uuid4()
    resolve_action_id = uuid4()
    record_action_id = uuid4()
    remember_endpoint_id = uuid4()
    resolve_endpoint_id = uuid4()
    record_endpoint_id = uuid4()
    memory_item_id = uuid4()
    event = {"id": str(uuid4()), "event_type": "conversation.message.created"}
    resolved_meaning = {
        "event_id": event["id"],
        "event_type": event["event_type"],
        "meaning_text": "Conversation message created",
    }

    remember_outcome = _outcome(
        endpoint_id=remember_endpoint_id,
        response_class_config_id=remember_response.id,
        response_payload={"memory_working_item_id": memory_item_id},
    )
    resolve_step = ProgramActionContinuationGraphStep(
        target_program_impl_instruction_intent_id=resolve_intent_id,
        target_sequence=2,
        target_action_config_id=resolve_action_id,
        target_api_capability_endpoint_id=resolve_endpoint_id,
        target_request_class_config=resolve_request,
        target_response_class_config_id=resolve_response.id,
        activation_field_bindings=(
            ProgramActionContinuationActivationFieldBinding(
                source_input_key="semantic_event",
                source_attribute_config_id=activation_attributes["event"].id,
                target_request_attribute_config_id=resolve_request_attributes[
                    "event"
                ].id,
            ),
        ),
    )
    record_step = ProgramActionContinuationGraphStep(
        target_program_impl_instruction_intent_id=record_intent_id,
        target_sequence=3,
        target_action_config_id=record_action_id,
        target_api_capability_endpoint_id=record_endpoint_id,
        target_request_class_config=record_request,
        target_response_class_config_id=record_response.id,
        outcome_sources=(
            ProgramActionContinuationOutcomeSource(
                contract=_contract(
                    source_intent_id=remember_intent_id,
                    target_intent_id=record_intent_id,
                    source_sequence=1,
                    target_sequence=3,
                    source_action_id=remember_action_id,
                    target_action_id=record_action_id,
                    source_endpoint_id=remember_endpoint_id,
                    target_endpoint_id=record_endpoint_id,
                    source_class=remember_response,
                    target_class=record_request,
                    field_bindings=(
                        ProgramActionContinuationFieldBinding(
                            source_response_attribute_config_id=(
                                remember_attributes["memory_working_item_id"].id
                            ),
                            target_request_attribute_config_id=(
                                record_request_attributes["memory_working_item_id"].id
                            ),
                        ),
                    ),
                ),
                source_response_class_config=remember_response,
            ),
            ProgramActionContinuationOutcomeSource(
                contract=_contract(
                    source_intent_id=resolve_intent_id,
                    target_intent_id=record_intent_id,
                    source_sequence=2,
                    target_sequence=3,
                    source_action_id=resolve_action_id,
                    target_action_id=record_action_id,
                    source_endpoint_id=resolve_endpoint_id,
                    target_endpoint_id=record_endpoint_id,
                    source_class=resolve_response,
                    target_class=record_request,
                    field_bindings=(
                        ProgramActionContinuationFieldBinding(
                            source_response_attribute_config_id=(
                                resolve_response_attributes["resolved_meaning"].id
                            ),
                            target_request_attribute_config_id=(
                                record_request_attributes["resolved_meaning"].id
                            ),
                        ),
                    ),
                    receipt_class=continuation_receipt,
                    receipt_field_bindings=(
                        ProgramActionContinuationReceiptFieldBinding(
                            source_receipt_attribute_config_id=(
                                receipt_attributes["status"].id
                            ),
                            target_request_attribute_config_id=(
                                record_request_attributes["resolver_status"].id
                            ),
                        ),
                        ProgramActionContinuationReceiptFieldBinding(
                            source_receipt_attribute_config_id=(
                                receipt_attributes["api_call_id"].id
                            ),
                            target_request_attribute_config_id=(
                                record_request_attributes["resolver_api_call_id"].id
                            ),
                        ),
                    ),
                ),
                source_response_class_config=resolve_response,
                source_receipt_class_config=continuation_receipt,
            ),
        ),
    )

    calls: list[
        tuple[
            ProgramActionContinuationGraphStep,
            ProgramActionContinuationCompositeResult,
        ]
    ] = []

    async def dispatch(
        step: ProgramActionContinuationGraphStep,
        continuation: ProgramActionContinuationCompositeResult,
    ) -> ActionDispatchTerminalOutcome:
        calls.append((step, continuation))
        if step.target_program_impl_instruction_intent_id == resolve_intent_id:
            assert continuation.request_payload == {"event": event}
            return _outcome(
                endpoint_id=resolve_endpoint_id,
                response_class_config_id=resolve_response.id,
                response_payload={"resolved_meaning": resolved_meaning},
            )
        assert continuation.request_payload["memory_working_item_id"] == (
            memory_item_id
        )
        assert continuation.request_payload["resolved_meaning"] == resolved_meaning
        assert continuation.request_payload["resolver_status"] == "succeeded"
        assert continuation.request_payload["resolver_api_call_id"] == (
            continuation.source_continuations[1].source_api_call_id
        )
        return _outcome(
            endpoint_id=record_endpoint_id,
            response_class_config_id=record_response.id,
            response_payload={"status": "recorded"},
        )

    result = await execute_program_action_continuation_graph(
        initial_outcomes_by_instruction_intent_id={
            remember_intent_id: remember_outcome
        },
        activation_inputs_by_key={
            "semantic_event": ProgramActionContinuationActivationInput(
                input_key="semantic_event",
                model_id=uuid4(),
                class_config=activation_class,
                payload={"event": event},
            )
        },
        steps=(record_step, resolve_step),
        dispatch=dispatch,
    )

    assert [step.target_program_impl_instruction_intent_id for step, _ in calls] == [
        resolve_intent_id,
        record_intent_id,
    ]
    assert len(result.continuations) == 2
    assert result.outcomes_by_instruction_intent_id[remember_intent_id] is (
        remember_outcome
    )
    assert result.outcomes_by_instruction_intent_id[record_intent_id].succeeded


@pytest.mark.asyncio
async def test_graph_rejects_activation_type_mismatch() -> None:
    source_class, source_attributes = _inline_class(
        name="ActivationTypeSource",
        fields=(("value", uuid4(), True),),
    )
    target_class, target_attributes = _inline_class(
        name="ActivationTypeTarget",
        fields=(("value", uuid4(), True),),
    )
    target_response, _ = _inline_class(
        name="ActivationTypeResponse",
        fields=(("status", uuid4(), True),),
    )
    step = ProgramActionContinuationGraphStep(
        target_program_impl_instruction_intent_id=uuid4(),
        target_sequence=1,
        target_action_config_id=uuid4(),
        target_api_capability_endpoint_id=uuid4(),
        target_request_class_config=target_class,
        target_response_class_config_id=target_response.id,
        activation_field_bindings=(
            ProgramActionContinuationActivationFieldBinding(
                source_input_key="activation",
                source_attribute_config_id=source_attributes["value"].id,
                target_request_attribute_config_id=target_attributes["value"].id,
            ),
        ),
    )

    async def dispatch(*_args: object) -> ActionDispatchTerminalOutcome:
        raise AssertionError("type mismatch must fail before dispatch")

    with pytest.raises(
        ProgramActionContinuationGraphError,
        match="program_action_continuation_type_descriptor_mismatch",
    ):
        _ = await execute_program_action_continuation_graph(
            initial_outcomes_by_instruction_intent_id={},
            activation_inputs_by_key={
                "activation": ProgramActionContinuationActivationInput(
                    input_key="activation",
                    model_id=uuid4(),
                    class_config=source_class,
                    payload={"value": "incompatible"},
                )
            },
            steps=(step,),
            dispatch=dispatch,
        )


@pytest.mark.asyncio
async def test_graph_rejects_forward_source_before_dispatch() -> None:
    descriptor_id = uuid4()
    source_class, source_attributes = _inline_class(
        name="ForwardSourceResponse",
        fields=(("value", descriptor_id, True),),
    )
    target_class, target_attributes = _inline_class(
        name="ForwardTargetRequest",
        fields=(("value", descriptor_id, True),),
    )
    target_response, _ = _inline_class(
        name="ForwardTargetResponse",
        fields=(("value", descriptor_id, True),),
    )
    source_intent_id = uuid4()
    target_intent_id = uuid4()
    source_endpoint_id = uuid4()
    target_endpoint_id = uuid4()
    contract = _contract(
        source_intent_id=source_intent_id,
        target_intent_id=target_intent_id,
        source_sequence=2,
        target_sequence=1,
        source_action_id=uuid4(),
        target_action_id=uuid4(),
        source_endpoint_id=source_endpoint_id,
        target_endpoint_id=target_endpoint_id,
        source_class=source_class,
        target_class=target_class,
        field_bindings=(
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=source_attributes["value"].id,
                target_request_attribute_config_id=target_attributes["value"].id,
            ),
        ),
    )
    step = ProgramActionContinuationGraphStep(
        target_program_impl_instruction_intent_id=target_intent_id,
        target_sequence=1,
        target_action_config_id=contract.target_action_config_id,
        target_api_capability_endpoint_id=target_endpoint_id,
        target_request_class_config=target_class,
        target_response_class_config_id=target_response.id,
        outcome_sources=(
            ProgramActionContinuationOutcomeSource(
                contract=contract,
                source_response_class_config=source_class,
            ),
        ),
    )

    async def dispatch(*_args: object) -> ActionDispatchTerminalOutcome:
        raise AssertionError("forward source must fail before dispatch")

    with pytest.raises(
        ProgramActionContinuationGraphError,
        match="program_action_continuation_graph_source_not_before_target",
    ):
        _ = await execute_program_action_continuation_graph(
            initial_outcomes_by_instruction_intent_id={
                source_intent_id: _outcome(
                    endpoint_id=source_endpoint_id,
                    response_class_config_id=source_class.id,
                    response_payload={"value": "future"},
                )
            },
            activation_inputs_by_key={},
            steps=(step,),
            dispatch=dispatch,
        )


@pytest.mark.asyncio
async def test_graph_rejects_cycle_before_dispatch() -> None:
    descriptor_id = uuid4()
    response_a, attributes_a = _inline_class(
        name="CycleResponseA", fields=(("value", descriptor_id, True),)
    )
    response_b, attributes_b = _inline_class(
        name="CycleResponseB", fields=(("value", descriptor_id, True),)
    )
    request_a, request_attributes_a = _inline_class(
        name="CycleRequestA", fields=(("value", descriptor_id, True),)
    )
    request_b, request_attributes_b = _inline_class(
        name="CycleRequestB", fields=(("value", descriptor_id, True),)
    )
    intent_a = uuid4()
    intent_b = uuid4()
    action_a = uuid4()
    action_b = uuid4()
    endpoint_a = uuid4()
    endpoint_b = uuid4()
    step_a = ProgramActionContinuationGraphStep(
        target_program_impl_instruction_intent_id=intent_a,
        target_sequence=2,
        target_action_config_id=action_a,
        target_api_capability_endpoint_id=endpoint_a,
        target_request_class_config=request_a,
        target_response_class_config_id=response_a.id,
        outcome_sources=(
            ProgramActionContinuationOutcomeSource(
                contract=_contract(
                    source_intent_id=intent_b,
                    target_intent_id=intent_a,
                    source_sequence=3,
                    target_sequence=2,
                    source_action_id=action_b,
                    target_action_id=action_a,
                    source_endpoint_id=endpoint_b,
                    target_endpoint_id=endpoint_a,
                    source_class=response_b,
                    target_class=request_a,
                    field_bindings=(
                        ProgramActionContinuationFieldBinding(
                            source_response_attribute_config_id=attributes_b[
                                "value"
                            ].id,
                            target_request_attribute_config_id=(
                                request_attributes_a["value"].id
                            ),
                        ),
                    ),
                ),
                source_response_class_config=response_b,
            ),
        ),
    )
    step_b = ProgramActionContinuationGraphStep(
        target_program_impl_instruction_intent_id=intent_b,
        target_sequence=3,
        target_action_config_id=action_b,
        target_api_capability_endpoint_id=endpoint_b,
        target_request_class_config=request_b,
        target_response_class_config_id=response_b.id,
        outcome_sources=(
            ProgramActionContinuationOutcomeSource(
                contract=_contract(
                    source_intent_id=intent_a,
                    target_intent_id=intent_b,
                    source_sequence=2,
                    target_sequence=3,
                    source_action_id=action_a,
                    target_action_id=action_b,
                    source_endpoint_id=endpoint_a,
                    target_endpoint_id=endpoint_b,
                    source_class=response_a,
                    target_class=request_b,
                    field_bindings=(
                        ProgramActionContinuationFieldBinding(
                            source_response_attribute_config_id=attributes_a[
                                "value"
                            ].id,
                            target_request_attribute_config_id=(
                                request_attributes_b["value"].id
                            ),
                        ),
                    ),
                ),
                source_response_class_config=response_a,
            ),
        ),
    )

    async def dispatch(*_args: object) -> ActionDispatchTerminalOutcome:
        raise AssertionError("cycle must fail before dispatch")

    with pytest.raises(
        ProgramActionContinuationGraphError,
        match="program_action_continuation_graph_cycle",
    ):
        _ = await execute_program_action_continuation_graph(
            initial_outcomes_by_instruction_intent_id={},
            activation_inputs_by_key={},
            steps=(step_a, step_b),
            dispatch=dispatch,
        )


@pytest.mark.asyncio
async def test_graph_rejects_missing_source_and_duplicate_target() -> None:
    descriptor_id = uuid4()
    source_class, source_attributes = _inline_class(
        name="MissingSourceResponse", fields=(("value", descriptor_id, True),)
    )
    target_class, target_attributes = _inline_class(
        name="DuplicateTargetRequest", fields=(("value", descriptor_id, True),)
    )
    target_response, _ = _inline_class(
        name="DuplicateTargetResponse", fields=(("value", descriptor_id, True),)
    )
    target_intent_id = uuid4()
    target_action_id = uuid4()
    target_endpoint_id = uuid4()
    contract = _contract(
        source_intent_id=uuid4(),
        target_intent_id=target_intent_id,
        source_sequence=1,
        target_sequence=2,
        source_action_id=uuid4(),
        target_action_id=target_action_id,
        source_endpoint_id=uuid4(),
        target_endpoint_id=target_endpoint_id,
        source_class=source_class,
        target_class=target_class,
        field_bindings=(
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=source_attributes["value"].id,
                target_request_attribute_config_id=target_attributes["value"].id,
            ),
        ),
    )
    missing_source_step = ProgramActionContinuationGraphStep(
        target_program_impl_instruction_intent_id=target_intent_id,
        target_sequence=2,
        target_action_config_id=target_action_id,
        target_api_capability_endpoint_id=target_endpoint_id,
        target_request_class_config=target_class,
        target_response_class_config_id=target_response.id,
        outcome_sources=(
            ProgramActionContinuationOutcomeSource(
                contract=contract,
                source_response_class_config=source_class,
            ),
        ),
    )

    async def dispatch(*_args: object) -> ActionDispatchTerminalOutcome:
        raise AssertionError("invalid graph must fail before dispatch")

    with pytest.raises(
        ProgramActionContinuationGraphError,
        match="program_action_continuation_graph_source_intent_missing",
    ):
        _ = await execute_program_action_continuation_graph(
            initial_outcomes_by_instruction_intent_id={},
            activation_inputs_by_key={},
            steps=(missing_source_step,),
            dispatch=dispatch,
        )

    duplicate_step = replace(
        missing_source_step,
        activation_field_bindings=(
            ProgramActionContinuationActivationFieldBinding(
                source_input_key="input",
                source_attribute_config_id=source_attributes["value"].id,
                target_request_attribute_config_id=target_attributes["value"].id,
            ),
        ),
    )
    with pytest.raises(
        ProgramActionContinuationGraphError,
        match="program_action_continuation_graph_duplicate_target_attribute",
    ):
        _ = await execute_program_action_continuation_graph(
            initial_outcomes_by_instruction_intent_id={
                contract.source_program_impl_instruction_intent_id: _outcome(
                    endpoint_id=contract.source_api_capability_endpoint_id,
                    response_class_config_id=source_class.id,
                    response_payload={"value": "source"},
                )
            },
            activation_inputs_by_key={
                "input": ProgramActionContinuationActivationInput(
                    input_key="input",
                    model_id=uuid4(),
                    class_config=source_class,
                    payload={"value": "activation"},
                )
            },
            steps=(duplicate_step,),
            dispatch=dispatch,
        )
