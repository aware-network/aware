from __future__ import annotations

from dataclasses import replace
from uuid import UUID, uuid4

import pytest

from aware_experience.action_dispatch.fulfillment import (
    ActionDispatchTerminalOutcome,
)
from aware_experience.program.action_continuation import (
    ProgramActionContinuationContract,
    ProgramActionContinuationError,
    ProgramActionContinuationFieldBinding,
    ProgramActionContinuationReceiptFieldBinding,
    compose_program_action_continuation,
)
from aware_experience.program.action_continuation_chain import (
    ProgramActionContinuationChainError,
    ProgramActionContinuationChainStep,
    execute_program_action_continuation_chain,
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
        class_fqn=f"aware_test.continuation.{name}",
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
    response_payload: object | None,
    status: str = "succeeded",
    response_model_id: UUID | None = None,
) -> ActionDispatchTerminalOutcome:
    return ActionDispatchTerminalOutcome(
        status=status,
        endpoint_ref="memory.remember_event.remember_event",
        discriminant="memory.remember_event.remember_event",
        api_call_id=uuid4(),
        api_capability_endpoint_id=endpoint_id,
        api_call_key=uuid4(),
        request_model_id=uuid4(),
        api_call_outcome_id=uuid4(),
        response_model_id=response_model_id or uuid4(),
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
        error=None if status == "succeeded" else "provider_failed",
    )


def _contract(
    *,
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
        source_program_impl_instruction_intent_id=uuid4(),
        target_program_impl_instruction_intent_id=uuid4(),
        source_sequence=1,
        target_sequence=2,
        source_action_config_id=uuid4(),
        target_action_config_id=uuid4(),
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


def test_compose_program_action_continuation_copies_only_declared_typed_fields() -> (
    None
):
    uuid_descriptor_id = uuid4()
    string_descriptor_id = uuid4()
    source_class, source_attributes = _inline_class(
        name="RememberEventResponse",
        fields=(
            ("memory_item_id", uuid_descriptor_id, True),
            ("provider_ref", string_descriptor_id, True),
            ("internal_note", string_descriptor_id, False),
        ),
    )
    target_class, target_attributes = _inline_class(
        name="ResolveMeaningRequest",
        fields=(
            ("remembered_item_id", uuid_descriptor_id, True),
            ("source_provider_ref", string_descriptor_id, True),
        ),
    )
    source_endpoint_id = uuid4()
    target_endpoint_id = uuid4()
    memory_item_id = uuid4()
    contract = _contract(
        source_endpoint_id=source_endpoint_id,
        target_endpoint_id=target_endpoint_id,
        source_class=source_class,
        target_class=target_class,
        field_bindings=(
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=(
                    source_attributes["memory_item_id"].id
                ),
                target_request_attribute_config_id=(
                    target_attributes["remembered_item_id"].id
                ),
                position=0,
            ),
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=(
                    source_attributes["provider_ref"].id
                ),
                target_request_attribute_config_id=(
                    target_attributes["source_provider_ref"].id
                ),
                position=1,
            ),
        ),
    )
    outcome = _outcome(
        endpoint_id=source_endpoint_id,
        response_class_config_id=source_class.id,
        response_payload={
            "memory_item_id": memory_item_id,
            "provider_ref": "conversation",
            "internal_note": "must-not-cross",
        },
    )

    result = compose_program_action_continuation(
        contract=contract,
        source_outcome=outcome,
        source_response_class_config=source_class,
        target_request_class_config=target_class,
    )

    assert result.request_payload == {
        "remembered_item_id": memory_item_id,
        "source_provider_ref": "conversation",
    }
    assert "internal_note" not in result.request_payload
    assert result.source_api_call_outcome_id == outcome.api_call_outcome_id
    assert result.source_response_model_id == outcome.response_model_id
    assert result.target_action_config_id == contract.target_action_config_id
    assert result.target_api_capability_endpoint_id == target_endpoint_id
    assert result.target_values_by_attribute_config_id == {
        target_attributes["remembered_item_id"].id: memory_item_id,
        target_attributes["source_provider_ref"].id: "conversation",
    }


def test_program_action_continuation_composes_typed_terminal_receipt_fields() -> None:
    uuid_descriptor_id = uuid4()
    string_descriptor_id = uuid4()
    source_class, source_attributes = _inline_class(
        name="ResolvedMeaningResponse",
        fields=(("meaning_text", string_descriptor_id, True),),
    )
    receipt_class, receipt_attributes = _inline_class(
        name="ProgramActionContinuationReceipt",
        fields=(
            ("source_action_config_id", uuid_descriptor_id, True),
            ("api_call_outcome_id", uuid_descriptor_id, True),
            ("service_operation_projection_hash", string_descriptor_id, False),
        ),
    )
    target_class, target_attributes = _inline_class(
        name="RecordResolvedMeaningRequest",
        fields=(
            ("meaning_text", string_descriptor_id, True),
            ("resolver_action_config_id", uuid_descriptor_id, True),
            ("resolver_api_call_outcome_id", uuid_descriptor_id, True),
            ("resolver_service_projection_hash", string_descriptor_id, True),
        ),
    )
    source_endpoint_id = uuid4()
    contract = _contract(
        source_endpoint_id=source_endpoint_id,
        target_endpoint_id=uuid4(),
        source_class=source_class,
        target_class=target_class,
        field_bindings=(
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=(
                    source_attributes["meaning_text"].id
                ),
                target_request_attribute_config_id=(
                    target_attributes["meaning_text"].id
                ),
            ),
        ),
        receipt_class=receipt_class,
        receipt_field_bindings=(
            ProgramActionContinuationReceiptFieldBinding(
                source_receipt_attribute_config_id=(
                    receipt_attributes["source_action_config_id"].id
                ),
                target_request_attribute_config_id=(
                    target_attributes["resolver_action_config_id"].id
                ),
            ),
            ProgramActionContinuationReceiptFieldBinding(
                source_receipt_attribute_config_id=(
                    receipt_attributes["api_call_outcome_id"].id
                ),
                target_request_attribute_config_id=(
                    target_attributes["resolver_api_call_outcome_id"].id
                ),
            ),
            ProgramActionContinuationReceiptFieldBinding(
                source_receipt_attribute_config_id=(
                    receipt_attributes["service_operation_projection_hash"].id
                ),
                target_request_attribute_config_id=(
                    target_attributes["resolver_service_projection_hash"].id
                ),
            ),
        ),
    )
    provider_echoed_outcome_id = uuid4()
    outcome = _outcome(
        endpoint_id=source_endpoint_id,
        response_class_config_id=source_class.id,
        response_payload={
            "meaning_text": "Conversation message was committed",
            "api_call_outcome_id": provider_echoed_outcome_id,
        },
    )

    result = compose_program_action_continuation(
        contract=contract,
        source_outcome=outcome,
        source_response_class_config=source_class,
        source_receipt_class_config=receipt_class,
        target_request_class_config=target_class,
    )

    assert result.request_payload == {
        "meaning_text": "Conversation message was committed",
        "resolver_action_config_id": contract.source_action_config_id,
        "resolver_api_call_outcome_id": outcome.api_call_outcome_id,
        "resolver_service_projection_hash": (outcome.service_operation_projection_hash),
    }
    assert (
        result.request_payload["resolver_api_call_outcome_id"]
        != provider_echoed_outcome_id
    )
    assert result.source_receipt_class_config_id == receipt_class.id


def test_program_action_continuation_requires_declared_receipt_class() -> None:
    descriptor_id = uuid4()
    source_class, _ = _inline_class(
        name="SourceResponse",
        fields=(("value", descriptor_id, True),),
    )
    receipt_class, receipt_attributes = _inline_class(
        name="ProgramActionContinuationReceipt",
        fields=(("api_call_outcome_id", descriptor_id, True),),
    )
    target_class, target_attributes = _inline_class(
        name="TargetRequest",
        fields=(("outcome_id", descriptor_id, True),),
    )
    endpoint_id = uuid4()
    contract = _contract(
        source_endpoint_id=endpoint_id,
        target_endpoint_id=uuid4(),
        source_class=source_class,
        target_class=target_class,
        field_bindings=(),
        receipt_class=receipt_class,
        receipt_field_bindings=(
            ProgramActionContinuationReceiptFieldBinding(
                source_receipt_attribute_config_id=(
                    receipt_attributes["api_call_outcome_id"].id
                ),
                target_request_attribute_config_id=target_attributes["outcome_id"].id,
            ),
        ),
    )

    with pytest.raises(
        ProgramActionContinuationError,
        match="program_action_continuation_source_receipt_class_missing",
    ):
        compose_program_action_continuation(
            contract=contract,
            source_outcome=_outcome(
                endpoint_id=endpoint_id,
                response_class_config_id=source_class.id,
                response_payload={"value": "ok"},
            ),
            source_response_class_config=source_class,
            target_request_class_config=target_class,
        )


def test_program_action_continuation_rejects_unknown_receipt_field() -> None:
    descriptor_id = uuid4()
    source_class, _ = _inline_class(
        name="SourceResponse",
        fields=(("value", descriptor_id, True),),
    )
    receipt_class, receipt_attributes = _inline_class(
        name="ForgedReceipt",
        fields=(("provider_supplied_outcome", descriptor_id, True),),
    )
    target_class, target_attributes = _inline_class(
        name="TargetRequest",
        fields=(("outcome_id", descriptor_id, True),),
    )
    endpoint_id = uuid4()
    contract = _contract(
        source_endpoint_id=endpoint_id,
        target_endpoint_id=uuid4(),
        source_class=source_class,
        target_class=target_class,
        field_bindings=(),
        receipt_class=receipt_class,
        receipt_field_bindings=(
            ProgramActionContinuationReceiptFieldBinding(
                source_receipt_attribute_config_id=(
                    receipt_attributes["provider_supplied_outcome"].id
                ),
                target_request_attribute_config_id=target_attributes["outcome_id"].id,
            ),
        ),
    )

    with pytest.raises(
        ProgramActionContinuationError,
        match="program_action_continuation_receipt_field_not_allowed",
    ):
        compose_program_action_continuation(
            contract=contract,
            source_outcome=_outcome(
                endpoint_id=endpoint_id,
                response_class_config_id=source_class.id,
                response_payload={"value": "ok"},
            ),
            source_response_class_config=source_class,
            source_receipt_class_config=receipt_class,
            target_request_class_config=target_class,
        )


def test_program_action_continuation_rejects_receipt_type_mismatch() -> None:
    uuid_descriptor_id = uuid4()
    source_class, _ = _inline_class(
        name="SourceResponse",
        fields=(("value", uuid_descriptor_id, True),),
    )
    receipt_class, receipt_attributes = _inline_class(
        name="ProgramActionContinuationReceipt",
        fields=(("api_call_outcome_id", uuid_descriptor_id, True),),
    )
    target_class, target_attributes = _inline_class(
        name="TargetRequest",
        fields=(("outcome_id", uuid4(), True),),
    )
    endpoint_id = uuid4()
    contract = _contract(
        source_endpoint_id=endpoint_id,
        target_endpoint_id=uuid4(),
        source_class=source_class,
        target_class=target_class,
        field_bindings=(),
        receipt_class=receipt_class,
        receipt_field_bindings=(
            ProgramActionContinuationReceiptFieldBinding(
                source_receipt_attribute_config_id=(
                    receipt_attributes["api_call_outcome_id"].id
                ),
                target_request_attribute_config_id=target_attributes["outcome_id"].id,
            ),
        ),
    )

    with pytest.raises(
        ProgramActionContinuationError,
        match="program_action_continuation_type_descriptor_mismatch",
    ):
        compose_program_action_continuation(
            contract=contract,
            source_outcome=_outcome(
                endpoint_id=endpoint_id,
                response_class_config_id=source_class.id,
                response_payload={"value": uuid4()},
            ),
            source_response_class_config=source_class,
            source_receipt_class_config=receipt_class,
            target_request_class_config=target_class,
        )


def test_program_action_continuation_rejects_missing_required_receipt_value() -> None:
    descriptor_id = uuid4()
    source_class, _ = _inline_class(
        name="SourceResponse",
        fields=(("value", descriptor_id, True),),
    )
    receipt_class, receipt_attributes = _inline_class(
        name="ProgramActionContinuationReceipt",
        fields=(("service_operation_id", descriptor_id, False),),
    )
    target_class, target_attributes = _inline_class(
        name="TargetRequest",
        fields=(("service_operation_id", descriptor_id, True),),
    )
    endpoint_id = uuid4()
    contract = _contract(
        source_endpoint_id=endpoint_id,
        target_endpoint_id=uuid4(),
        source_class=source_class,
        target_class=target_class,
        field_bindings=(),
        receipt_class=receipt_class,
        receipt_field_bindings=(
            ProgramActionContinuationReceiptFieldBinding(
                source_receipt_attribute_config_id=(
                    receipt_attributes["service_operation_id"].id
                ),
                target_request_attribute_config_id=(
                    target_attributes["service_operation_id"].id
                ),
            ),
        ),
    )
    outcome = replace(
        _outcome(
            endpoint_id=endpoint_id,
            response_class_config_id=source_class.id,
            response_payload={"value": "ok"},
        ),
        service_operation_id=None,
    )

    with pytest.raises(
        ProgramActionContinuationError,
        match="program_action_continuation_receipt_value_missing",
    ):
        compose_program_action_continuation(
            contract=contract,
            source_outcome=outcome,
            source_response_class_config=source_class,
            source_receipt_class_config=receipt_class,
            target_request_class_config=target_class,
        )


@pytest.mark.parametrize(
    ("contract_update", "outcome_update", "expected_error"),
    [
        (
            {"target_sequence": 1},
            {},
            "program_action_continuation_target_not_after_source",
        ),
        (
            {},
            {"status": "failed"},
            "program_action_continuation_source_outcome_not_succeeded",
        ),
        (
            {},
            {"api_capability_endpoint_id": uuid4()},
            "program_action_continuation_source_endpoint_mismatch",
        ),
        (
            {},
            {"response_model_id": None},
            "program_action_continuation_source_response_model_missing",
        ),
    ],
)
def test_program_action_continuation_rejects_invalid_source_or_order(
    contract_update: dict[str, object],
    outcome_update: dict[str, object],
    expected_error: str,
) -> None:
    descriptor_id = uuid4()
    source_class, source_attributes = _inline_class(
        name="SourceResponse",
        fields=(("value", descriptor_id, True),),
    )
    target_class, target_attributes = _inline_class(
        name="TargetRequest",
        fields=(("value", descriptor_id, True),),
    )
    source_endpoint_id = uuid4()
    contract = _contract(
        source_endpoint_id=source_endpoint_id,
        target_endpoint_id=uuid4(),
        source_class=source_class,
        target_class=target_class,
        field_bindings=(
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=source_attributes["value"].id,
                target_request_attribute_config_id=target_attributes["value"].id,
            ),
        ),
    )
    outcome = _outcome(
        endpoint_id=source_endpoint_id,
        response_class_config_id=source_class.id,
        response_payload={"value": "ok"},
    )

    with pytest.raises(ProgramActionContinuationError, match=expected_error):
        compose_program_action_continuation(
            contract=replace(contract, **contract_update),
            source_outcome=replace(outcome, **outcome_update),
            source_response_class_config=source_class,
            target_request_class_config=target_class,
        )


def test_program_action_continuation_rejects_type_descriptor_mismatch() -> None:
    source_class, source_attributes = _inline_class(
        name="SourceResponse",
        fields=(("value", uuid4(), True),),
    )
    target_class, target_attributes = _inline_class(
        name="TargetRequest",
        fields=(("value", uuid4(), True),),
    )
    source_endpoint_id = uuid4()
    contract = _contract(
        source_endpoint_id=source_endpoint_id,
        target_endpoint_id=uuid4(),
        source_class=source_class,
        target_class=target_class,
        field_bindings=(
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=source_attributes["value"].id,
                target_request_attribute_config_id=target_attributes["value"].id,
            ),
        ),
    )

    with pytest.raises(
        ProgramActionContinuationError,
        match="program_action_continuation_type_descriptor_mismatch",
    ):
        compose_program_action_continuation(
            contract=contract,
            source_outcome=_outcome(
                endpoint_id=source_endpoint_id,
                response_class_config_id=source_class.id,
                response_payload={"value": "not-convertible"},
            ),
            source_response_class_config=source_class,
            target_request_class_config=target_class,
        )


def test_program_action_continuation_requires_terminal_outcome() -> None:
    descriptor_id = uuid4()
    source_class, source_attributes = _inline_class(
        name="SourceResponse",
        fields=(("value", descriptor_id, True),),
    )
    target_class, target_attributes = _inline_class(
        name="TargetRequest",
        fields=(("value", descriptor_id, True),),
    )
    contract = _contract(
        source_endpoint_id=uuid4(),
        target_endpoint_id=uuid4(),
        source_class=source_class,
        target_class=target_class,
        field_bindings=(
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=source_attributes["value"].id,
                target_request_attribute_config_id=target_attributes["value"].id,
            ),
        ),
    )

    with pytest.raises(
        ProgramActionContinuationError,
        match="program_action_continuation_source_outcome_missing",
    ):
        compose_program_action_continuation(
            contract=contract,
            source_outcome=None,
            source_response_class_config=source_class,
            target_request_class_config=target_class,
        )


def test_program_action_continuation_rejects_undeclared_or_duplicate_targets() -> None:
    descriptor_id = uuid4()
    source_class, source_attributes = _inline_class(
        name="SourceResponse",
        fields=(
            ("first", descriptor_id, True),
            ("second", descriptor_id, True),
        ),
    )
    target_class, target_attributes = _inline_class(
        name="TargetRequest",
        fields=(("target", descriptor_id, True),),
    )
    source_endpoint_id = uuid4()
    duplicate_contract = _contract(
        source_endpoint_id=source_endpoint_id,
        target_endpoint_id=uuid4(),
        source_class=source_class,
        target_class=target_class,
        field_bindings=(
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=source_attributes["first"].id,
                target_request_attribute_config_id=target_attributes["target"].id,
            ),
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=source_attributes["second"].id,
                target_request_attribute_config_id=target_attributes["target"].id,
            ),
        ),
    )
    outcome = _outcome(
        endpoint_id=source_endpoint_id,
        response_class_config_id=source_class.id,
        response_payload={"first": "a", "second": "b"},
    )

    with pytest.raises(
        ProgramActionContinuationError,
        match="program_action_continuation_duplicate_target_attribute",
    ):
        compose_program_action_continuation(
            contract=duplicate_contract,
            source_outcome=outcome,
            source_response_class_config=source_class,
            target_request_class_config=target_class,
        )

    missing_source_contract = replace(
        duplicate_contract,
        field_bindings=(
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=uuid4(),
                target_request_attribute_config_id=target_attributes["target"].id,
            ),
        ),
    )
    with pytest.raises(
        ProgramActionContinuationError,
        match="program_action_continuation_source_attribute_not_in_response_class",
    ):
        compose_program_action_continuation(
            contract=missing_source_contract,
            source_outcome=outcome,
            source_response_class_config=source_class,
            target_request_class_config=target_class,
        )

    missing_target_contract = replace(
        duplicate_contract,
        field_bindings=(
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=source_attributes["first"].id,
                target_request_attribute_config_id=uuid4(),
            ),
        ),
    )
    with pytest.raises(
        ProgramActionContinuationError,
        match="program_action_continuation_target_attribute_not_in_request_class",
    ):
        compose_program_action_continuation(
            contract=missing_target_contract,
            source_outcome=outcome,
            source_response_class_config=source_class,
            target_request_class_config=target_class,
        )


def test_program_action_continuation_rejects_missing_required_source_value() -> None:
    descriptor_id = uuid4()
    source_class, source_attributes = _inline_class(
        name="SourceResponse",
        fields=(("required_value", descriptor_id, True),),
    )
    target_class, target_attributes = _inline_class(
        name="TargetRequest",
        fields=(("required_value", descriptor_id, True),),
    )
    source_endpoint_id = uuid4()
    contract = _contract(
        source_endpoint_id=source_endpoint_id,
        target_endpoint_id=uuid4(),
        source_class=source_class,
        target_class=target_class,
        field_bindings=(
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=(
                    source_attributes["required_value"].id
                ),
                target_request_attribute_config_id=(
                    target_attributes["required_value"].id
                ),
            ),
        ),
    )

    with pytest.raises(
        ProgramActionContinuationError,
        match="program_action_continuation_source_value_missing",
    ):
        compose_program_action_continuation(
            contract=contract,
            source_outcome=_outcome(
                endpoint_id=source_endpoint_id,
                response_class_config_id=source_class.id,
                response_payload={"ignored": "not-bound"},
            ),
            source_response_class_config=source_class,
            target_request_class_config=target_class,
        )


def _continuation_chain_fixture() -> tuple[
    ActionDispatchTerminalOutcome,
    tuple[ProgramActionContinuationChainStep, ...],
    ClassConfig,
    ClassConfig,
]:
    source_value_descriptor_id = uuid4()
    transformed_value_descriptor_id = uuid4()
    status_descriptor_id = uuid4()
    source_response, source_attributes = _inline_class(
        name="ContinuationSourceResponse",
        fields=(("source_value", source_value_descriptor_id, False),),
    )
    transform_request, transform_request_attributes = _inline_class(
        name="ContinuationTransformRequest",
        fields=(("source_value", source_value_descriptor_id, True),),
    )
    transform_response, transform_response_attributes = _inline_class(
        name="ContinuationTransformResponse",
        fields=(("transformed_value", transformed_value_descriptor_id, True),),
    )
    sink_request, sink_request_attributes = _inline_class(
        name="ContinuationSinkRequest",
        fields=(("transformed_value", transformed_value_descriptor_id, True),),
    )
    sink_response, _ = _inline_class(
        name="ContinuationSinkResponse",
        fields=(("status", status_descriptor_id, True),),
    )
    source_endpoint_id = uuid4()
    transform_endpoint_id = uuid4()
    sink_endpoint_id = uuid4()
    first_contract = _contract(
        source_endpoint_id=source_endpoint_id,
        target_endpoint_id=transform_endpoint_id,
        source_class=source_response,
        target_class=transform_request,
        field_bindings=(
            ProgramActionContinuationFieldBinding(
                source_response_attribute_config_id=source_attributes[
                    "source_value"
                ].id,
                target_request_attribute_config_id=(
                    transform_request_attributes["source_value"].id
                ),
            ),
        ),
    )
    second_contract = replace(
        _contract(
            source_endpoint_id=transform_endpoint_id,
            target_endpoint_id=sink_endpoint_id,
            source_class=transform_response,
            target_class=sink_request,
            field_bindings=(
                ProgramActionContinuationFieldBinding(
                    source_response_attribute_config_id=(
                        transform_response_attributes["transformed_value"].id
                    ),
                    target_request_attribute_config_id=(
                        sink_request_attributes["transformed_value"].id
                    ),
                ),
            ),
        ),
        source_program_impl_instruction_intent_id=(
            first_contract.target_program_impl_instruction_intent_id
        ),
        source_sequence=first_contract.target_sequence,
        target_sequence=first_contract.target_sequence + 1,
        source_action_config_id=first_contract.target_action_config_id,
    )
    initial_outcome = _outcome(
        endpoint_id=source_endpoint_id,
        response_class_config_id=source_response.id,
        response_payload={"source_value": {"id": str(uuid4())}},
    )
    return (
        initial_outcome,
        (
            ProgramActionContinuationChainStep(
                contract=first_contract,
                source_response_class_config=source_response,
                target_request_class_config=transform_request,
                target_response_class_config_id=transform_response.id,
            ),
            ProgramActionContinuationChainStep(
                contract=second_contract,
                source_response_class_config=transform_response,
                target_request_class_config=sink_request,
                target_response_class_config_id=sink_response.id,
            ),
        ),
        transform_response,
        sink_response,
    )


@pytest.mark.asyncio
async def test_program_action_continuation_chain_dispatches_explicit_sequence() -> None:
    initial_outcome, steps, transform_response, sink_response = (
        _continuation_chain_fixture()
    )
    calls = []

    async def _dispatch(step, continuation):  # noqa: ANN001, ANN202
        calls.append((step, continuation))
        if len(calls) == 1:
            return _outcome(
                endpoint_id=step.contract.target_api_capability_endpoint_id,
                response_class_config_id=transform_response.id,
                response_payload={
                    "transformed_value": {"description": "transformed source"}
                },
            )
        return _outcome(
            endpoint_id=step.contract.target_api_capability_endpoint_id,
            response_class_config_id=sink_response.id,
            response_payload={"status": "recorded"},
        )

    result = await execute_program_action_continuation_chain(
        initial_outcome=initial_outcome,
        steps=steps,
        dispatch=_dispatch,
    )

    assert len(calls) == 2
    assert calls[0][1].request_payload["source_value"] == (
        initial_outcome.response_payload["source_value"]
    )
    assert calls[1][1].request_payload["transformed_value"] == (
        calls[0][1].request_payload.get("transformed_value")
        or result.dispatched_outcomes[0].response_payload["transformed_value"]
    )
    assert result.terminal_outcome.response_payload == {"status": "recorded"}


@pytest.mark.asyncio
async def test_program_action_continuation_chain_stops_on_failed_target() -> None:
    initial_outcome, steps, transform_response, _ = _continuation_chain_fixture()
    calls = []

    async def _dispatch(step, continuation):  # noqa: ANN001, ANN202
        calls.append((step, continuation))
        return _outcome(
            endpoint_id=step.contract.target_api_capability_endpoint_id,
            response_class_config_id=transform_response.id,
            response_payload={"error": "provider failed"},
            status="failed",
        )

    with pytest.raises(
        ProgramActionContinuationChainError,
        match="program_action_continuation_chain_target_outcome_not_succeeded",
    ):
        await execute_program_action_continuation_chain(
            initial_outcome=initial_outcome,
            steps=steps,
            dispatch=_dispatch,
        )

    assert len(calls) == 1
