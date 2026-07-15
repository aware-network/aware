from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_code.types import JsonObject
from aware_api_ontology.stable_ids import stable_api_call_id
from aware_experience.program.action_continuation_activation import (
    HydratedProgramActionContinuationActivationRuntime,
    ProgramActionContinuationActivationError,
    ProgramActionContinuationEndpointRoute,
    derive_program_action_continuation_api_call_key,
)
from aware_experience.program.action_continuation_graph import (
    ProgramActionContinuationActivationInput,
)
from aware_experience.program import snapshot_reader as snapshot_reader_module
from aware_experience.program.snapshot_reader import ProgramOntologySnapshotReader
from aware_experience_ontology.program.impl.program_impl import ProgramImpl
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
from aware_experience_ontology.program.program_config import ProgramConfig
from aware_reactivity_ontology.action.action_config import ActionConfig
from aware_service_runtime.action_dispatch_fulfillment import (
    ServiceHostActionTerminalFulfillmentInvoker,
)

from .test_experience_program_action_continuation_materialization import (
    _endpoint,
    _inline_class,
    _outcome,
)


class _SnapshotResolver:
    def __init__(self, *snapshots: object) -> None:
        self.snapshots = snapshots
        self.calls: list[tuple[UUID, UUID]] = []

    async def resolve_action_continuation_candidates(
        self,
        *,
        action_config_id: UUID,
        event_config_id: UUID,
    ) -> tuple[Any, ...]:
        self.calls.append((action_config_id, event_config_id))
        return cast(tuple[Any, ...], self.snapshots)


@pytest.mark.asyncio
async def test_snapshot_reader_discovers_only_committed_initial_action_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    action_config_id = uuid4()
    event_config_id = uuid4()
    branch_id = uuid4()
    program_config = ProgramConfig.model_construct(id=uuid4(), key="continuation")
    initial_impl = ProgramImpl.model_construct(
        id=uuid4(),
        program_config_id=program_config.id,
        key="initial",
    )
    noninitial_impl = ProgramImpl.model_construct(
        id=uuid4(),
        program_config_id=program_config.id,
        key="noninitial",
    )
    initial_intent = ProgramImplInstructionIntent.model_construct(
        id=uuid4(),
        action_config_id=action_config_id,
        event_config_id=event_config_id,
        continuation_key="remember",
    )
    noninitial_intent = ProgramImplInstructionIntent.model_construct(
        id=uuid4(),
        action_config_id=action_config_id,
        event_config_id=event_config_id,
        continuation_key="resolve",
    )
    snapshots = {
        "initial": SimpleNamespace(
            instruction_intents_by_id={initial_intent.id: initial_intent},
            activation_field_bindings_by_intent_id={},
            outcome_field_bindings_by_intent_id={},
            receipt_field_bindings_by_intent_id={},
        ),
        "noninitial": SimpleNamespace(
            instruction_intents_by_id={noninitial_intent.id: noninitial_intent},
            activation_field_bindings_by_intent_id={noninitial_intent.id: (object(),)},
            outcome_field_bindings_by_intent_id={},
            receipt_field_bindings_by_intent_id={},
        ),
    }

    async def _hydrate(
        *,
        session: Any,
        projection_name: str,
    ) -> None:
        if projection_name == "ProgramConfig":
            session.imap_add(program_config)
        if projection_name == "ProgramImpl":
            session.imap_add(initial_impl)
            session.imap_add(noninitial_impl)

    async def _load(
        *,
        program_config_id: UUID,
        preferred_program_impl_key: str | None,
        lane_reader: object,
    ) -> Any:
        assert program_config_id == program_config.id
        _ = lane_reader
        return snapshots[str(preferred_program_impl_key)]

    reader = ProgramOntologySnapshotReader(
        branch_id=branch_id,
        environment_id=uuid4(),
    )
    monkeypatch.setattr(reader, "_hydrate_projection_lane_into_session", _hydrate)
    monkeypatch.setattr(
        snapshot_reader_module,
        "load_program_config_impl_snapshot",
        _load,
    )

    candidates = await reader.resolve_action_continuation_candidates(
        action_config_id=action_config_id,
        event_config_id=event_config_id,
    )
    assert candidates == (snapshots["initial"],)


def _runtime_fixture() -> SimpleNamespace:
    event_type = uuid4()
    item_type = uuid4()
    meaning_type = uuid4()
    status_type = uuid4()
    activation_class, activation_attrs = _inline_class(
        name="ActivationRuntimeEvent",
        fields=(("event", event_type),),
    )
    remember_request, _ = _inline_class(
        name="ActivationRuntimeRememberRequest",
        fields=(("event", event_type),),
    )
    remember_response, remember_attrs = _inline_class(
        name="ActivationRuntimeRememberResponse",
        fields=(("memory_working_item_id", item_type),),
    )
    resolve_request, resolve_request_attrs = _inline_class(
        name="ActivationRuntimeResolveRequest",
        fields=(("event", event_type),),
    )
    resolve_response, resolve_response_attrs = _inline_class(
        name="ActivationRuntimeResolveResponse",
        fields=(("resolved_meaning", meaning_type),),
    )
    receipt_class, receipt_attrs = _inline_class(
        name="ActivationRuntimeReceipt",
        fields=(("status", status_type),),
    )
    record_request, record_request_attrs = _inline_class(
        name="ActivationRuntimeRecordRequest",
        fields=(
            ("memory_working_item_id", item_type),
            ("resolved_meaning", meaning_type),
            ("resolver_status", status_type),
        ),
    )
    record_response, _ = _inline_class(
        name="ActivationRuntimeRecordResponse",
        fields=(("status", status_type),),
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
        request_class=remember_request,
        response_class=remember_response,
    )
    resolve_endpoint = _endpoint(
        request_class=resolve_request,
        response_class=resolve_response,
    )
    record_endpoint = _endpoint(
        request_class=record_request,
        response_class=record_response,
    )
    endpoints = {
        item.id: item for item in (remember_endpoint, resolve_endpoint, record_endpoint)
    }
    event_config_id = uuid4()
    program_impl_id = uuid4()
    actions: dict[UUID, ActionConfig] = {}
    intents: list[ProgramImplInstructionIntent] = []
    instructions: list[ProgramImplInstruction] = []
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
        intents.append(intent)
        instructions.append(
            ProgramImplInstruction(
                id=instruction_id,
                program_impl_id=program_impl_id,
                type=ProgramImplInstructionType.intent,
                sequence=sequence,
                instruction_intent=intent,
            )
        )
    remember_intent, resolve_intent, record_intent = intents
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
        source_response_attribute_config_id=(
            remember_attrs["memory_working_item_id"].id
        ),
        target_request_attribute_config_id=(
            record_request_attrs["memory_working_item_id"].id
        ),
    )
    meaning_binding = ProgramImplInstructionIntentOutcomeFieldBinding(
        id=uuid4(),
        program_impl_instruction_intent_id=record_intent.id,
        source_program_impl_instruction_intent_id=resolve_intent.id,
        source_response_attribute_config_id=(
            resolve_response_attrs["resolved_meaning"].id
        ),
        target_request_attribute_config_id=(
            record_request_attrs["resolved_meaning"].id
        ),
    )
    receipt_binding = ProgramImplInstructionIntentReceiptFieldBinding(
        id=uuid4(),
        program_impl_instruction_intent_id=record_intent.id,
        source_program_impl_instruction_intent_id=resolve_intent.id,
        source_receipt_class_config_id=receipt_class.id,
        source_receipt_attribute_config_id=receipt_attrs["status"].id,
        target_request_attribute_config_id=(record_request_attrs["resolver_status"].id),
    )
    snapshot = SimpleNamespace(
        program_config=SimpleNamespace(id=uuid4()),
        program_impl=SimpleNamespace(id=program_impl_id),
        instruction_rows=tuple(instructions),
        instruction_intents_by_id={item.id: item for item in intents},
        activation_field_bindings_by_intent_id={
            resolve_intent.id: (activation_binding,)
        },
        outcome_field_bindings_by_intent_id={
            record_intent.id: (remember_binding, meaning_binding)
        },
        receipt_field_bindings_by_intent_id={record_intent.id: (receipt_binding,)},
    )
    return SimpleNamespace(
        snapshot=snapshot,
        classes=classes,
        endpoints=endpoints,
        actions=actions,
        event_config_id=event_config_id,
        activation_class=activation_class,
        remember_intent=remember_intent,
        resolve_intent=resolve_intent,
        record_intent=record_intent,
        remember_endpoint=remember_endpoint,
        remember_response=remember_response,
        resolve_endpoint=resolve_endpoint,
        resolve_response=resolve_response,
        record_endpoint=record_endpoint,
        record_response=record_response,
    )


@pytest.mark.asyncio
async def test_activation_runtime_executes_committed_graph_through_terminal_fulfillment() -> (
    None
):
    fixture = _runtime_fixture()
    memory_item_id = uuid4()
    initial_outcome = _outcome(
        endpoint=fixture.remember_endpoint,
        response_class=fixture.remember_response,
        payload={"memory_working_item_id": memory_item_id},
    )
    calls: list[object] = []

    class _ServiceHostClient:
        async def send_api_ingress_request(
            self,
            *,
            request: Any,
            timeout_s: float | None = None,
        ) -> object:
            _ = timeout_s
            calls.append(request)
            endpoint_ref = request.endpoint_ref
            call_key = cast(UUID, request.network_request_id)
            if endpoint_ref == "conversation.resolve_event_meaning":
                endpoint = fixture.resolve_endpoint
                response_payload = {
                    "resolved_meaning": {"meaning_text": "Conversation message created"}
                }
            else:
                endpoint = fixture.record_endpoint
                assert dict(request.request_payload) == {
                    "memory_working_item_id": memory_item_id,
                    "resolved_meaning": {
                        "meaning_text": "Conversation message created"
                    },
                    "resolver_status": "succeeded",
                }
                response_payload = {"status": "recorded"}
            return SimpleNamespace(
                status="succeeded",
                response_payload=response_payload,
                receipt=SimpleNamespace(
                    endpoint_ref=endpoint_ref,
                    discriminant=endpoint_ref,
                    status="succeeded",
                    api_call_id=stable_api_call_id(
                        api_capability_endpoint_id=endpoint.id,
                        call_key=call_key,
                    ),
                    api_capability_endpoint_id=endpoint.id,
                    call_key=call_key,
                    request_model_id=uuid4(),
                    api_call_outcome_id=uuid4(),
                    response_model_id=uuid4(),
                ),
            )

    resolver = _SnapshotResolver(fixture.snapshot)
    runtime = HydratedProgramActionContinuationActivationRuntime(
        snapshot_resolver=resolver,
        action_configs_by_id=fixture.actions,
        api_capability_endpoints_by_id=fixture.endpoints,
        class_configs_by_id=fixture.classes,
        endpoint_routes_by_id={
            fixture.resolve_endpoint.id: ProgramActionContinuationEndpointRoute(
                api_capability_endpoint_id=fixture.resolve_endpoint.id,
                endpoint_ref="conversation.resolve_event_meaning",
                discriminant="conversation.resolve_event_meaning",
            ),
            fixture.record_endpoint.id: ProgramActionContinuationEndpointRoute(
                api_capability_endpoint_id=fixture.record_endpoint.id,
                endpoint_ref="memory.record_resolved_event_meaning",
                discriminant="memory.record_resolved_event_meaning",
            ),
        },
        activation_inputs_by_key={
            "semantic_event": ProgramActionContinuationActivationInput(
                input_key="semantic_event",
                model_id=uuid4(),
                class_config=fixture.activation_class,
                payload={"event": {"event_id": "event-1"}},
            )
        },
        terminal_fulfillment_invoker=ServiceHostActionTerminalFulfillmentInvoker(
            actor_id=uuid4(),
            client_factory=_ServiceHostClient,
            invocation_context=JsonObject({"source": "program.continuation"}),
        ),
    )
    result = await runtime.activate(
        initial_action_config_id=fixture.remember_intent.action_config_id,
        initial_event_config_id=fixture.event_config_id,
        initial_api_capability_endpoint_id=fixture.remember_endpoint.id,
        initial_outcome=initial_outcome,
    )

    assert result is not None
    assert result.initial_program_impl_instruction_intent_id == (
        fixture.remember_intent.id
    )
    assert len(result.graph_result.dispatched_outcomes) == 2
    assert [getattr(call, "endpoint_ref") for call in calls] == [
        "conversation.resolve_event_meaning",
        "memory.record_resolved_event_meaning",
    ]
    assert [getattr(call, "network_request_id") for call in calls] == [
        derive_program_action_continuation_api_call_key(
            initial_api_call_key=initial_outcome.api_call_key,
            program_impl_id=fixture.snapshot.program_impl.id,
            target_program_impl_instruction_intent_id=fixture.resolve_intent.id,
        ),
        derive_program_action_continuation_api_call_key(
            initial_api_call_key=initial_outcome.api_call_key,
            program_impl_id=fixture.snapshot.program_impl.id,
            target_program_impl_instruction_intent_id=fixture.record_intent.id,
        ),
    ]


@pytest.mark.asyncio
async def test_activation_runtime_rejects_ambiguous_or_mismatched_initial_graph() -> (
    None
):
    fixture = _runtime_fixture()
    initial_outcome = _outcome(
        endpoint=fixture.remember_endpoint,
        response_class=fixture.remember_response,
        payload={"memory_working_item_id": uuid4()},
    )
    runtime = HydratedProgramActionContinuationActivationRuntime(
        snapshot_resolver=_SnapshotResolver(fixture.snapshot, fixture.snapshot),
        action_configs_by_id=fixture.actions,
        api_capability_endpoints_by_id=fixture.endpoints,
        class_configs_by_id=fixture.classes,
        endpoint_routes_by_id={},
        activation_inputs_by_key={},
        terminal_fulfillment_invoker=cast(Any, object()),
    )
    with pytest.raises(
        ProgramActionContinuationActivationError,
        match="activation_ambiguous",
    ):
        _ = await runtime.activate(
            initial_action_config_id=fixture.remember_intent.action_config_id,
            initial_event_config_id=fixture.event_config_id,
            initial_api_capability_endpoint_id=fixture.remember_endpoint.id,
            initial_outcome=initial_outcome,
        )
    with pytest.raises(
        ProgramActionContinuationActivationError,
        match="initial_endpoint_mismatch",
    ):
        _ = await runtime.activate(
            initial_action_config_id=fixture.remember_intent.action_config_id,
            initial_event_config_id=fixture.event_config_id,
            initial_api_capability_endpoint_id=uuid4(),
            initial_outcome=initial_outcome,
        )
