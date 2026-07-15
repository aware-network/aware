from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_request_config import (
    ApiCapabilityEndpointRequestConfig,
)
from aware_api_ontology.api.api_capability_endpoint_response_config import (
    ApiCapabilityEndpointResponseConfig,
)
from aware_experience.action_dispatch.fulfillment import ActionDispatchTerminalOutcome
from aware_experience.materialization.program_materialization import (
    _program_impl_instruction_snapshots,
)
from aware_experience.materialization.snapshot_commit import (
    _build_program_impl_objects,
)
from aware_experience.program.action_continuation_graph import (
    ProgramActionContinuationActivationInput,
    ProgramActionContinuationCompositeResult,
    ProgramActionContinuationGraphStep,
    execute_program_action_continuation_graph,
)
from aware_experience.program.action_continuation_hydration import (
    hydrate_program_action_continuation_graph,
)
from aware_experience.program.language import compile_invocation_plans
from aware_experience_ontology.program.impl.program_impl_instruction import (
    ProgramImplInstruction,
)
from aware_experience_ontology.program.impl.program_impl_instruction_enums import (
    ProgramImplInstructionType,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent import (
    ProgramImplInstructionIntent,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent_activation_field_binding import (
    ProgramImplInstructionIntentActivationFieldBinding,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent_outcome_field_binding import (
    ProgramImplInstructionIntentOutcomeFieldBinding,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent_receipt_field_binding import (
    ProgramImplInstructionIntentReceiptFieldBinding,
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
from aware_reactivity_ontology.action.action_config import ActionConfig


REPO_ROOT = Path(__file__).resolve().parents[8]
CONVERSATION_GRAPH_SOURCE = (
    REPO_ROOT
    / "workspaces/aware_coordination/modules/conversation/experiences/aware-conversations"
    / "programs/reactivity/conversation_memory_event_meaning_graph_v1.aware"
)


def _inline_class(
    *,
    name: str,
    fields: tuple[tuple[str, UUID], ...],
) -> tuple[ClassConfig, dict[str, AttributeConfig]]:
    class_config = ClassConfig(
        id=uuid4(),
        name=name,
        class_fqn=f"aware_test.continuation_materialization.{name}",
        value_mode=ClassValueMode.inline_value,
    )
    attributes: dict[str, AttributeConfig] = {}
    for position, (field_name, descriptor_id) in enumerate(fields):
        descriptor = AttributeTypeDescriptor(
            id=descriptor_id,
            kind=AttributeTypeDescriptorKind.primitive,
        )
        attribute = AttributeConfig(
            id=uuid4(),
            owner_key=class_config.class_fqn,
            name=field_name,
            is_required=True,
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


def _endpoint(
    *,
    request_class: ClassConfig,
    response_class: ClassConfig,
) -> ApiCapabilityEndpoint:
    endpoint_id = uuid4()
    request_config = ApiCapabilityEndpointRequestConfig(
        id=uuid4(),
        api_capability_endpoint_id=endpoint_id,
        class_config_id=request_class.id,
        class_config=request_class,
    )
    request_config.response_config = ApiCapabilityEndpointResponseConfig(
        id=uuid4(),
        api_capability_endpoint_request_config_id=request_config.id,
        class_config_id=response_class.id,
        class_config=response_class,
    )
    return ApiCapabilityEndpoint(
        id=endpoint_id,
        api_capability_id=uuid4(),
        name="test",
        request_config=request_config,
    )


def _outcome(
    *,
    endpoint: ApiCapabilityEndpoint,
    response_class: ClassConfig,
    payload: object,
) -> ActionDispatchTerminalOutcome:
    return ActionDispatchTerminalOutcome(
        status="succeeded",
        endpoint_ref="test.endpoint",
        discriminant="test.endpoint",
        api_call_id=uuid4(),
        api_capability_endpoint_id=endpoint.id,
        api_call_key=uuid4(),
        request_model_id=uuid4(),
        api_call_outcome_id=uuid4(),
        response_model_id=uuid4(),
        response_class_config_id=response_class.id,
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
        response_payload=payload,
        error=None,
    )


def test_conversation_graph_materializes_exact_stable_program_edges() -> None:
    source = CONVERSATION_GRAPH_SOURCE.read_text(encoding="utf-8")
    plan = compile_invocation_plans(source)[0]
    program_config_id = uuid4()

    first = _program_impl_instruction_snapshots(
        index=cast(Any, SimpleNamespace()),
        program_config_id=program_config_id,
        invocation_plan=plan,
        port_ids_by_key={},
        port_node_ids_by_ref={},
    )
    second = _program_impl_instruction_snapshots(
        index=cast(Any, SimpleNamespace()),
        program_config_id=program_config_id,
        invocation_plan=plan,
        port_ids_by_key={},
        port_node_ids_by_ref={},
    )
    assert first == second

    root, objects = _build_program_impl_objects(
        program_config_id=program_config_id,
        key=plan.name,
        instructions=first,
    )
    intents = [
        instruction.instruction_intent
        for instruction in root.instructions
        if instruction.instruction_intent is not None
    ]
    assert [intent.continuation_key for intent in intents] == [
        "remember",
        "resolve",
        "record",
    ]
    assert len(objects) == 56
    assert [
        (
            len(intent.activation_field_bindings),
            len(intent.outcome_field_bindings),
            len(intent.receipt_field_bindings),
        )
        for intent in intents
    ] == [(0, 0, 0), (1, 0, 0), (0, 2, 22)]
    edge_ids = {
        edge.id
        for intent in intents
        for edge in (
            *intent.activation_field_bindings,
            *intent.outcome_field_bindings,
            *intent.receipt_field_bindings,
        )
    }
    assert len(edge_ids) == 25


@pytest.mark.asyncio
async def test_hydrated_program_truth_executes_existing_continuation_dag() -> None:
    event_type = uuid4()
    item_type = uuid4()
    meaning_type = uuid4()
    status_type = uuid4()
    empty_type = uuid4()
    activation_class, activation_attrs = _inline_class(
        name="Activation",
        fields=(("event", event_type),),
    )
    remember_request, _ = _inline_class(
        name="RememberRequest", fields=(("event", event_type),)
    )
    remember_response, remember_attrs = _inline_class(
        name="RememberResponse", fields=(("memory_working_item_id", item_type),)
    )
    resolve_request, resolve_request_attrs = _inline_class(
        name="ResolveRequest", fields=(("event", event_type),)
    )
    resolve_response, resolve_response_attrs = _inline_class(
        name="ResolveResponse", fields=(("resolved_meaning", meaning_type),)
    )
    receipt_class, receipt_attrs = _inline_class(
        name="ContinuationReceipt", fields=(("status", status_type),)
    )
    record_request, record_request_attrs = _inline_class(
        name="RecordRequest",
        fields=(
            ("memory_working_item_id", item_type),
            ("resolved_meaning", meaning_type),
            ("resolver_status", status_type),
        ),
    )
    record_response, _ = _inline_class(
        name="RecordResponse", fields=(("status", empty_type),)
    )

    classes = {
        item.id: item
        for item in (
            activation_class,
            remember_request,
            remember_response,
            resolve_request,
            resolve_response,
            receipt_class,
            record_request,
            record_response,
        )
    }
    remember_endpoint = _endpoint(
        request_class=remember_request, response_class=remember_response
    )
    resolve_endpoint = _endpoint(
        request_class=resolve_request, response_class=resolve_response
    )
    record_endpoint = _endpoint(
        request_class=record_request, response_class=record_response
    )
    endpoints = {
        endpoint.id: endpoint
        for endpoint in (remember_endpoint, resolve_endpoint, record_endpoint)
    }

    event_config_id = uuid4()
    intent_rows: list[ProgramImplInstructionIntent] = []
    instruction_rows: list[ProgramImplInstruction] = []
    actions: dict[UUID, ActionConfig] = {}
    for sequence, (key, endpoint, request_class, response_class) in enumerate(
        (
            ("remember", remember_endpoint, remember_request, remember_response),
            ("resolve", resolve_endpoint, resolve_request, resolve_response),
            ("record", record_endpoint, record_request, record_response),
        )
    ):
        action = ActionConfig(
            id=uuid4(),
            name=key,
            description=f"{key} action",
            action_type=key,
            api_capability_endpoint_id=endpoint.id,
            api_capability_endpoint=endpoint,
        )
        actions[action.id] = action
        instruction_id = uuid4()
        intent = ProgramImplInstructionIntent(
            id=uuid4(),
            program_impl_instruction_id=instruction_id,
            action_config_id=action.id,
            event_config_id=event_config_id,
            continuation_key=key,
            api_capability_endpoint_id=endpoint.id,
            request_class_config_id=request_class.id,
            response_class_config_id=response_class.id,
        )
        intent_rows.append(intent)
        instruction_rows.append(
            ProgramImplInstruction(
                id=instruction_id,
                program_impl_id=uuid4(),
                type=ProgramImplInstructionType.intent,
                sequence=sequence,
                instruction_intent=intent,
            )
        )

    remember_intent, resolve_intent, record_intent = intent_rows
    activation_binding = ProgramImplInstructionIntentActivationFieldBinding(
        id=uuid4(),
        program_impl_instruction_intent_id=resolve_intent.id,
        source_class_config_id=activation_class.id,
        source_attribute_config_id=activation_attrs["event"].id,
        target_request_attribute_config_id=resolve_request_attrs["event"].id,
        source_input_key="semantic_event",
    )
    remember_binding = ProgramImplInstructionIntentOutcomeFieldBinding(
        id=uuid4(),
        program_impl_instruction_intent_id=record_intent.id,
        source_program_impl_instruction_intent_id=remember_intent.id,
        source_response_attribute_config_id=remember_attrs["memory_working_item_id"].id,
        target_request_attribute_config_id=record_request_attrs[
            "memory_working_item_id"
        ].id,
    )
    meaning_binding = ProgramImplInstructionIntentOutcomeFieldBinding(
        id=uuid4(),
        program_impl_instruction_intent_id=record_intent.id,
        source_program_impl_instruction_intent_id=resolve_intent.id,
        source_response_attribute_config_id=resolve_response_attrs[
            "resolved_meaning"
        ].id,
        target_request_attribute_config_id=record_request_attrs["resolved_meaning"].id,
    )
    status_binding = ProgramImplInstructionIntentReceiptFieldBinding(
        id=uuid4(),
        program_impl_instruction_intent_id=record_intent.id,
        source_program_impl_instruction_intent_id=resolve_intent.id,
        source_receipt_class_config_id=receipt_class.id,
        source_receipt_attribute_config_id=receipt_attrs["status"].id,
        target_request_attribute_config_id=record_request_attrs["resolver_status"].id,
    )
    snapshot = SimpleNamespace(
        instruction_rows=tuple(instruction_rows),
        instruction_intents_by_id={item.id: item for item in intent_rows},
        activation_field_bindings_by_intent_id={
            resolve_intent.id: (activation_binding,)
        },
        outcome_field_bindings_by_intent_id={
            record_intent.id: (remember_binding, meaning_binding)
        },
        receipt_field_bindings_by_intent_id={record_intent.id: (status_binding,)},
    )
    hydrated = hydrate_program_action_continuation_graph(
        snapshot=cast(Any, snapshot),
        action_configs_by_id=actions,
        api_capability_endpoints_by_id=endpoints,
        class_configs_by_id=classes,
    )
    assert hydrated.initial_program_impl_instruction_intent_ids == (remember_intent.id,)
    assert [
        step.target_program_impl_instruction_intent_id for step in hydrated.steps
    ] == [
        resolve_intent.id,
        record_intent.id,
    ]

    memory_item_id = uuid4()
    remember_outcome = _outcome(
        endpoint=remember_endpoint,
        response_class=remember_response,
        payload={"memory_working_item_id": memory_item_id},
    )
    resolved_meaning = {"meaning_text": "Conversation message created"}

    async def dispatch(
        step: ProgramActionContinuationGraphStep,
        continuation: ProgramActionContinuationCompositeResult,
    ) -> ActionDispatchTerminalOutcome:
        if step.target_program_impl_instruction_intent_id == resolve_intent.id:
            assert continuation.request_payload["event"] == {"event_id": "event-1"}
            return _outcome(
                endpoint=resolve_endpoint,
                response_class=resolve_response,
                payload={"resolved_meaning": resolved_meaning},
            )
        assert continuation.request_payload == {
            "memory_working_item_id": memory_item_id,
            "resolved_meaning": resolved_meaning,
            "resolver_status": "succeeded",
        }
        return _outcome(
            endpoint=record_endpoint,
            response_class=record_response,
            payload={"status": "recorded"},
        )

    result = await execute_program_action_continuation_graph(
        initial_outcomes_by_instruction_intent_id={
            remember_intent.id: remember_outcome
        },
        activation_inputs_by_key={
            "semantic_event": ProgramActionContinuationActivationInput(
                input_key="semantic_event",
                model_id=uuid4(),
                class_config=activation_class,
                payload={"event": {"event_id": "event-1"}},
            )
        },
        steps=hydrated.steps,
        dispatch=dispatch,
        class_configs_by_id=classes,
    )
    assert result.outcomes_by_instruction_intent_id[record_intent.id].succeeded
