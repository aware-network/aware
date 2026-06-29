from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import cast
from uuid import UUID

from aware_meta.materialization.deltas.ontology_execution.contracts import (
    OntologyInvocationIntent,
    OntologyOperationHandlerResult,
    OntologyTypedOperation,
    blocked_handler_result,
)
from aware_meta.materialization.deltas.ontology_execution.receiver_resolution import (
    mapping_value,
    optional_text,
    string_value,
    tuple_mappings,
)
from aware_meta_ontology.stable_ids import (
    stable_function_impl_instruction_id,
    stable_function_impl_instruction_set_id,
    stable_function_impl_value_source_id,
)


HANDLER_KEY = "function_impl.additive_instruction_body"
FUNCTION_IMPL_INSTRUCTION_IDENTITY_FIELDS = ("type", "sequence")
FUNCTION_IMPL_INSTRUCTION_IDENTITY_CONTRACT = (
    "function_impl_instruction_identity_type_sequence"
)
FUNCTION_IMPL_CREATE_INSTRUCTION_REF = (
    "aware_meta_ontology.function.function_impl.FunctionImpl.create_instruction"
)
FUNCTION_IMPL_REMOVE_INSTRUCTION_REF = (
    "aware_meta_ontology.function.function_impl.FunctionImpl.remove_instruction"
)
FUNCTION_IMPL_INSTRUCTION_CREATE_VALUE_SOURCE_REF = (
    "aware_meta_ontology.function.function_impl_instruction."
    "FunctionImplInstruction.create_value_source"
)
FUNCTION_IMPL_INSTRUCTION_ATTACH_SET_REF = (
    "aware_meta_ontology.function.function_impl_instruction."
    "FunctionImplInstruction.attach_set"
)
FUNCTION_IMPL_VALUE_SOURCE_UPDATE_FUNCTION_INPUT_REF = (
    "aware_meta_ontology.function.function_impl_value_source."
    "FunctionImplValueSource.update_function_input_ref"
)
FUNCTION_IMPL_INSTRUCTION_SET_UPDATE_ASSIGNMENT_REF = (
    "aware_meta_ontology.function.function_impl_instruction_set."
    "FunctionImplInstructionSet.update_assignment"
)
_FUNCTION_IMPL_INVOCATION_ORDER_BASE = 1000


def plan_function_impl_operation(
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    if operation.ontology_subject_kind != "function_impl":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_ontology_handler_subject_mismatch",
            blockers=(f"unsupported_subject:{operation.ontology_subject_kind}",),
        )
    if operation.operation_family not in {"create", "update"}:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_function_impl_delta_requires_additive_create_or_update",
            blockers=(f"unsupported_operation_family:{operation.operation_family}",),
        )

    current_signature = _function_impl_signature(operation.current)
    baseline_signature = _function_impl_signature_from_baseline(operation.baseline)
    current_instructions = _instruction_signatures(current_signature)
    baseline_instructions = _instruction_signatures(baseline_signature)
    baseline_instruction_count = _int_value(
        baseline_signature.get("instruction_count")
    )
    if not current_instructions:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_function_impl_delta_requires_current_instructions",
            blockers=("function_impl_current_instruction_body_empty",),
        )
    if baseline_instruction_count and not baseline_instructions:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason=(
                "meta_ocg_function_impl_replacement_requires_baseline_instruction_index"
            ),
            blockers=("function_impl_baseline_instruction_index_unavailable",),
        )
    if baseline_instructions:
        intents_or_blocker = _instruction_replacement_intents(
            operation=operation,
            current_instructions=current_instructions,
            baseline_instructions=baseline_instructions,
        )
    else:
        intents_or_blocker = _instruction_intents(
            operation=operation,
            instructions=current_instructions,
            invocation_order_base=_FUNCTION_IMPL_INVOCATION_ORDER_BASE,
        )
    if isinstance(intents_or_blocker, tuple) and all(
        isinstance(intent, OntologyInvocationIntent) for intent in intents_or_blocker
    ):
        invocation_intents = cast(
            tuple[OntologyInvocationIntent, ...],
            intents_or_blocker,
        )
        return OntologyOperationHandlerResult(
            operation_key=operation.operation_key,
            semantic_key=operation.semantic_key,
            handler_key=HANDLER_KEY,
            status="ontology_operation_handler_ready",
            reason="meta_ocg_function_impl_instruction_body_function_calls_ready",
            invocation_intents=invocation_intents,
        )
    return blocked_handler_result(
        operation=operation,
        handler_key=HANDLER_KEY,
        reason="meta_ocg_function_impl_instruction_body_function_calls_blocked",
        blockers=tuple(str(item) for item in intents_or_blocker),
    )


def _instruction_replacement_intents(
    *,
    operation: OntologyTypedOperation,
    current_instructions: tuple[Mapping[str, object], ...],
    baseline_instructions: tuple[Mapping[str, object], ...],
) -> tuple[OntologyInvocationIntent, ...] | tuple[str, ...]:
    function_impl_receiver_id = _function_impl_receiver_id(operation=operation)
    if function_impl_receiver_id is None:
        return ("function_impl_object_id_unavailable_or_invalid",)
    function_impl_source_id = (
        _function_impl_source_id(operation=operation) or function_impl_receiver_id
    )

    baseline_by_key = _instructions_by_identity_key(
        instructions=baseline_instructions,
    )
    current_by_key = _instructions_by_identity_key(
        instructions=current_instructions,
    )
    blockers: list[str] = []
    if len(baseline_by_key) != len(baseline_instructions):
        blockers.append("function_impl_baseline_instruction_identity_duplicate")
    if len(current_by_key) != len(current_instructions):
        blockers.append("function_impl_current_instruction_identity_duplicate")
    stale_keys = tuple(
        key for key in sorted(baseline_by_key) if key not in current_by_key
    )
    if blockers:
        return tuple(blockers)

    intents: list[OntologyInvocationIntent] = []
    invocation_order = _FUNCTION_IMPL_INVOCATION_ORDER_BASE
    for instruction_key in sorted(stale_keys, key=_instruction_key_sort_key):
        remove_intent = _instruction_remove_intent(
            operation=operation,
            function_impl_receiver_id=function_impl_receiver_id,
            function_impl_source_id=function_impl_source_id,
            instruction=baseline_by_key[instruction_key],
            invocation_order=invocation_order,
        )
        if isinstance(remove_intent, OntologyInvocationIntent):
            intents.append(remove_intent)
            invocation_order += 1
            continue
        return tuple(str(item) for item in remove_intent)
    for instruction_key in sorted(current_by_key, key=_instruction_key_sort_key):
        current_instruction = current_by_key[instruction_key]
        baseline_instruction = baseline_by_key.get(instruction_key)
        if baseline_instruction is None:
            additive = _instruction_intents(
                operation=operation,
                instructions=(current_instruction,),
                invocation_order_base=invocation_order,
            )
            if _is_intents_tuple(additive):
                intents.extend(cast(tuple[OntologyInvocationIntent, ...], additive))
                invocation_order += len(additive)
                continue
            return tuple(str(item) for item in additive)
        update = _instruction_update_intents(
            operation=operation,
            function_impl_source_id=function_impl_source_id,
            current_instruction=current_instruction,
            baseline_instruction=baseline_instruction,
            invocation_order_base=invocation_order,
        )
        if _is_intents_tuple(update):
            intents.extend(cast(tuple[OntologyInvocationIntent, ...], update))
            invocation_order += len(update)
            continue
        return tuple(str(item) for item in update)
    if not intents:
        return ("function_impl_instruction_body_noop_not_executable",)
    return tuple(intents)


def _instruction_intents(
    *,
    operation: OntologyTypedOperation,
    instructions: tuple[Mapping[str, object], ...],
    invocation_order_base: int,
) -> tuple[OntologyInvocationIntent, ...] | tuple[str, ...]:
    blockers: list[str] = []
    intents: list[OntologyInvocationIntent] = []
    function_impl_receiver_id = _function_impl_receiver_id(
        operation=operation,
    )
    if function_impl_receiver_id is None:
        blockers.append("function_impl_object_id_unavailable_or_invalid")
    function_impl_source_id = _function_impl_source_id(operation=operation)
    if function_impl_source_id is None:
        blockers.append("function_impl_source_object_id_unavailable_or_invalid")
    if len(instructions) != 1:
        blockers.append("function_impl_additive_body_requires_single_instruction")
    if blockers:
        return tuple(blockers)
    assert function_impl_receiver_id is not None
    assert function_impl_source_id is not None
    instruction = instructions[0]
    instruction_type = string_value(instruction.get("type"))
    if instruction_type != "set":
        return (f"unsupported_function_impl_instruction_type:{instruction_type}",)
    sequence = _int_value(instruction.get("sequence"))
    if sequence is None:
        return ("function_impl_instruction_sequence_unavailable",)
    set_payload = mapping_value(instruction.get("set"))
    value_source = mapping_value(set_payload.get("value_source"))
    target_edge_id = _uuid_value(
        optional_text(set_payload.get("target_class_config_attribute_config_id"))
    )
    if target_edge_id is None:
        return ("function_impl_set_target_edge_id_unavailable_or_invalid",)
    value_source_key = optional_text(value_source.get("key"))
    if value_source_key is None:
        return ("function_impl_set_value_source_key_unavailable",)
    value_source_id = stable_function_impl_value_source_id(
        function_impl_instruction_id=stable_function_impl_instruction_id(
            function_impl_id=function_impl_source_id,
            type=instruction_type,
            sequence=sequence,
        ),
        key=value_source_key,
    )
    source_input_id = _uuid_value(
        optional_text(value_source.get("source_function_config_attribute_config_id"))
    )
    if source_input_id is None:
        # Runtime delta signatures expose names for humans. The durable call
        # needs the FunctionConfigAttributeConfig id, so this stays blocked
        # until the transformer/index emits that canonical id.
        return ("function_impl_value_source_input_edge_id_unavailable",)
    instruction_id = stable_function_impl_instruction_id(
        function_impl_id=function_impl_source_id,
        type=instruction_type,
        sequence=sequence,
    )
    intents.append(
        OntologyInvocationIntent(
            intent_key=f"{operation.operation_key}:create_instruction:{sequence}",
            operation_key=operation.operation_key,
            semantic_key=operation.semantic_key,
            invocation_order=0,
            invocation_mode="instance",
            owner_class_name="FunctionImpl",
            function_name="create_instruction",
            function_ref=FUNCTION_IMPL_CREATE_INSTRUCTION_REF,
            target_object_id=str(function_impl_receiver_id),
            receiver_semantic_key=operation.semantic_key,
            result_semantic_key=f"{operation.semantic_key}/instruction:{sequence}",
            expected_result_object_id=str(instruction_id),
            kwargs={"type": instruction_type, "sequence": sequence},
            reason=(
                f"{FUNCTION_IMPL_INSTRUCTION_IDENTITY_CONTRACT}_create_ready"
            ),
        )
    )
    intents.append(
        OntologyInvocationIntent(
            intent_key=f"{operation.operation_key}:create_value_source:{sequence}",
            operation_key=operation.operation_key,
            semantic_key=operation.semantic_key,
            invocation_order=1,
            invocation_mode="instance",
            owner_class_name="FunctionImplInstruction",
            function_name="create_value_source",
            function_ref=FUNCTION_IMPL_INSTRUCTION_CREATE_VALUE_SOURCE_REF,
            target_object_id=str(instruction_id),
            receiver_semantic_key=f"{operation.semantic_key}/instruction:{sequence}",
            result_semantic_key=(
                f"{operation.semantic_key}/instruction:{sequence}"
                f"/value_source:{value_source_key}"
            ),
            expected_result_object_id=str(value_source_id),
            kwargs={
                "key": value_source_key,
                "kind": _value_source_kind(value_source),
                "source_function_config_attribute_config_id": str(source_input_id),
                "source_instruction_let_id": None,
            },
            reason="function_impl_value_source_create_ready",
        )
    )
    intents.append(
        OntologyInvocationIntent(
            intent_key=f"{operation.operation_key}:attach_set:{sequence}",
            operation_key=operation.operation_key,
            semantic_key=operation.semantic_key,
            invocation_order=2,
            invocation_mode="instance",
            owner_class_name="FunctionImplInstruction",
            function_name="attach_set",
            function_ref=FUNCTION_IMPL_INSTRUCTION_ATTACH_SET_REF,
            target_object_id=str(instruction_id),
            receiver_semantic_key=f"{operation.semantic_key}/instruction:{sequence}",
            result_semantic_key=(
                f"{operation.semantic_key}/instruction:{sequence}/set"
            ),
            expected_result_object_id=str(
                stable_function_impl_instruction_set_id(
                    function_impl_instruction_id=instruction_id,
                )
            ),
            kwargs={
                "target_class_config_attribute_config_id": str(target_edge_id),
                "value_source_id": str(value_source_id),
            },
            reason="function_impl_instruction_set_attach_ready",
        )
    )
    intents = [
        _intent_with_order(
            intent=intent,
            invocation_order=invocation_order_base + index,
        )
        for index, intent in enumerate(intents)
    ]
    return tuple(intents)


def _instruction_update_intents(
    *,
    operation: OntologyTypedOperation,
    function_impl_source_id: UUID,
    current_instruction: Mapping[str, object],
    baseline_instruction: Mapping[str, object],
    invocation_order_base: int,
) -> tuple[OntologyInvocationIntent, ...] | tuple[str, ...]:
    instruction_type = string_value(current_instruction.get("type"))
    baseline_instruction_type = string_value(baseline_instruction.get("type"))
    if instruction_type != baseline_instruction_type:
        return ("function_impl_instruction_type_replacement_not_supported",)
    if instruction_type != "set":
        return (f"unsupported_function_impl_instruction_type:{instruction_type}",)
    sequence = _int_value(current_instruction.get("sequence"))
    if sequence is None:
        return ("function_impl_instruction_sequence_unavailable",)

    instruction_id = stable_function_impl_instruction_id(
        function_impl_id=function_impl_source_id,
        type=instruction_type,
        sequence=sequence,
    )
    instruction_receiver_id = _nested_receiver_id(
        baseline_instruction,
        fallback=instruction_id,
    )
    set_payload = mapping_value(current_instruction.get("set"))
    baseline_set_payload = mapping_value(baseline_instruction.get("set"))
    if not set_payload:
        return ("function_impl_set_payload_unavailable",)
    if not baseline_set_payload:
        return ("function_impl_baseline_set_payload_unavailable",)

    current_value_source = mapping_value(set_payload.get("value_source"))
    baseline_value_source = mapping_value(baseline_set_payload.get("value_source"))
    current_value_source_key = optional_text(current_value_source.get("key"))
    baseline_value_source_key = optional_text(baseline_value_source.get("key"))
    if current_value_source_key is None:
        return ("function_impl_set_value_source_key_unavailable",)
    if baseline_value_source_key is None:
        return ("function_impl_baseline_set_value_source_key_unavailable",)

    target_edge_id = _uuid_value(
        optional_text(set_payload.get("target_class_config_attribute_config_id"))
    )
    if target_edge_id is None:
        return ("function_impl_set_target_edge_id_unavailable_or_invalid",)
    source_input_id = _uuid_value(
        optional_text(
            current_value_source.get("source_function_config_attribute_config_id")
        )
    )
    if source_input_id is None:
        return ("function_impl_value_source_input_edge_id_unavailable",)

    value_source_id = stable_function_impl_value_source_id(
        function_impl_instruction_id=instruction_id,
        key=current_value_source_key,
    )
    baseline_value_source_id = stable_function_impl_value_source_id(
        function_impl_instruction_id=instruction_id,
        key=baseline_value_source_key,
    )

    intents: list[OntologyInvocationIntent] = []
    if baseline_value_source_key != current_value_source_key:
        intents.append(
            _value_source_create_intent(
                operation=operation,
                instruction_target_object_id=instruction_receiver_id,
                sequence=sequence,
                value_source_key=current_value_source_key,
                value_source_id=value_source_id,
                value_source=current_value_source,
                source_input_id=source_input_id,
                invocation_order=invocation_order_base + len(intents),
            )
        )
    elif _value_source_needs_function_input_update(
        current_value_source=current_value_source,
        baseline_value_source=baseline_value_source,
    ):
        current_value_source_kind = _value_source_kind(current_value_source)
        baseline_value_source_kind = _value_source_kind(baseline_value_source)
        if (
            current_value_source_kind != "function_input_ref"
            or baseline_value_source_kind != "function_input_ref"
        ):
            return (
                "function_impl_value_source_replacement_requires_specific_update_function:"
                f"{baseline_value_source_kind}->{current_value_source_kind}",
            )
        intents.append(
            OntologyInvocationIntent(
                intent_key=(
                    f"{operation.operation_key}:update_value_source:"
                    f"{sequence}:{current_value_source_key}"
                ),
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=invocation_order_base + len(intents),
                invocation_mode="instance",
                owner_class_name="FunctionImplValueSource",
                function_name="update_function_input_ref",
                function_ref=FUNCTION_IMPL_VALUE_SOURCE_UPDATE_FUNCTION_INPUT_REF,
                target_object_id=str(
                    _nested_receiver_id(
                        baseline_value_source,
                        fallback=baseline_value_source_id,
                    )
                ),
                receiver_semantic_key=(
                    f"{operation.semantic_key}/instruction:{sequence}"
                    f"/value_source:{baseline_value_source_key}"
                ),
                result_semantic_key=(
                    f"{operation.semantic_key}/instruction:{sequence}"
                    f"/value_source:{current_value_source_key}"
                ),
                expected_result_object_id=str(baseline_value_source_id),
                kwargs={
                    "source_function_config_attribute_config_id": str(
                        source_input_id
                    ),
                },
                reason=(
                    f"{FUNCTION_IMPL_INSTRUCTION_IDENTITY_CONTRACT}"
                    "_value_source_update_ready"
                ),
            )
        )

    baseline_target_edge_id = _uuid_value(
        optional_text(
            baseline_set_payload.get("target_class_config_attribute_config_id")
        )
    )
    baseline_set_value_source_id = _uuid_value(
        optional_text(baseline_set_payload.get("value_source_id"))
    )
    if (
        baseline_target_edge_id != target_edge_id
        or baseline_set_value_source_id not in {None, value_source_id}
        or baseline_value_source_key != current_value_source_key
    ):
        instruction_set_id = stable_function_impl_instruction_set_id(
            function_impl_instruction_id=instruction_id,
        )
        instruction_set_receiver_id = _nested_receiver_id(
            baseline_set_payload,
            fallback=instruction_set_id,
        )
        intents.append(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:update_set:{sequence}",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=invocation_order_base + len(intents),
                invocation_mode="instance",
                owner_class_name="FunctionImplInstructionSet",
                function_name="update_assignment",
                function_ref=FUNCTION_IMPL_INSTRUCTION_SET_UPDATE_ASSIGNMENT_REF,
                target_object_id=str(instruction_set_receiver_id),
                receiver_semantic_key=(
                    f"{operation.semantic_key}/instruction:{sequence}/set"
                ),
                result_semantic_key=(
                    f"{operation.semantic_key}/instruction:{sequence}/set"
                ),
                expected_result_object_id=str(instruction_set_id),
                kwargs={
                    "target_class_config_attribute_config_id": str(target_edge_id),
                    "value_source_id": str(value_source_id),
                },
                reason=(
                    f"{FUNCTION_IMPL_INSTRUCTION_IDENTITY_CONTRACT}"
                    "_set_update_ready"
                ),
            )
        )
    return tuple(intents)


def _instruction_remove_intent(
    *,
    operation: OntologyTypedOperation,
    function_impl_receiver_id: UUID,
    function_impl_source_id: UUID,
    instruction: Mapping[str, object],
    invocation_order: int,
) -> OntologyInvocationIntent | tuple[str, ...]:
    instruction_type = string_value(instruction.get("type"))
    if instruction_type != "set":
        return (f"unsupported_function_impl_instruction_type:{instruction_type}",)
    sequence = _int_value(instruction.get("sequence"))
    if sequence is None:
        return ("function_impl_instruction_sequence_unavailable",)
    instruction_id = stable_function_impl_instruction_id(
        function_impl_id=function_impl_source_id,
        type=instruction_type,
        sequence=sequence,
    )
    return OntologyInvocationIntent(
        intent_key=f"{operation.operation_key}:remove_instruction:{sequence}",
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        invocation_order=invocation_order,
        invocation_mode="instance",
        owner_class_name="FunctionImpl",
        function_name="remove_instruction",
        function_ref=FUNCTION_IMPL_REMOVE_INSTRUCTION_REF,
        target_object_id=str(function_impl_receiver_id),
        receiver_semantic_key=operation.semantic_key,
        result_semantic_key=f"{operation.semantic_key}/instruction:{sequence}",
        expected_result_object_id=str(instruction_id),
        kwargs={"type": instruction_type, "sequence": sequence},
        reason=(
            f"{FUNCTION_IMPL_INSTRUCTION_IDENTITY_CONTRACT}"
            "_stale_remove_ready"
        ),
    )


def _value_source_create_intent(
    *,
    operation: OntologyTypedOperation,
    instruction_target_object_id: UUID,
    sequence: int,
    value_source_key: str,
    value_source_id: UUID,
    value_source: Mapping[str, object],
    source_input_id: UUID,
    invocation_order: int,
) -> OntologyInvocationIntent:
    return OntologyInvocationIntent(
        intent_key=f"{operation.operation_key}:create_value_source:{sequence}",
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        invocation_order=invocation_order,
        invocation_mode="instance",
        owner_class_name="FunctionImplInstruction",
        function_name="create_value_source",
        function_ref=FUNCTION_IMPL_INSTRUCTION_CREATE_VALUE_SOURCE_REF,
        target_object_id=str(instruction_target_object_id),
        receiver_semantic_key=f"{operation.semantic_key}/instruction:{sequence}",
        result_semantic_key=(
            f"{operation.semantic_key}/instruction:{sequence}"
            f"/value_source:{value_source_key}"
        ),
        expected_result_object_id=str(value_source_id),
        kwargs={
            "key": value_source_key,
            "kind": _value_source_kind(value_source),
            "source_function_config_attribute_config_id": str(source_input_id),
            "source_instruction_let_id": None,
        },
        reason="function_impl_value_source_create_ready",
    )


def _instructions_by_identity_key(
    *,
    instructions: tuple[Mapping[str, object], ...],
) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for instruction in instructions:
        instruction_key = _instruction_identity_key(instruction=instruction)
        if instruction_key is not None:
            result[instruction_key] = instruction
    return result


def _instruction_identity_key(*, instruction: Mapping[str, object]) -> str | None:
    # Stable FunctionImplInstruction OIG ids are derived from type + sequence.
    # Do not semantic-match body payloads until the ontology exposes an
    # explicit instruction key independent of order.
    instruction_type = optional_text(instruction.get("type"))
    sequence = _int_value(instruction.get("sequence"))
    if instruction_type is None or sequence is None:
        return None
    return f"{instruction_type}:{sequence}"


def _instruction_key_sort_key(instruction_key: str) -> tuple[int, str]:
    if ":" not in instruction_key:
        return (0, instruction_key)
    instruction_type, raw_sequence = instruction_key.rsplit(":", 1)
    try:
        sequence = int(raw_sequence)
    except ValueError:
        sequence = 0
    return (sequence, instruction_type)


def _is_intents_tuple(value: object) -> bool:
    return isinstance(value, tuple) and all(
        isinstance(intent, OntologyInvocationIntent) for intent in value
    )


def _intent_with_order(
    *,
    intent: OntologyInvocationIntent,
    invocation_order: int,
) -> OntologyInvocationIntent:
    return replace(intent, invocation_order=invocation_order)


def _value_source_needs_function_input_update(
    *,
    current_value_source: Mapping[str, object],
    baseline_value_source: Mapping[str, object],
) -> bool:
    return (
        _value_source_kind(current_value_source)
        != _value_source_kind(baseline_value_source)
        or optional_text(
            current_value_source.get("source_function_config_attribute_config_id")
        )
        != optional_text(
            baseline_value_source.get(
                "source_function_config_attribute_config_id"
            )
        )
        or optional_text(current_value_source.get("source_instruction_let_id"))
        != optional_text(baseline_value_source.get("source_instruction_let_id"))
    )


def _value_source_kind(value_source: Mapping[str, object]) -> str:
    kind = string_value(value_source.get("kind"))
    if kind == "function_input":
        return "function_input_ref"
    return kind


def _nested_receiver_id(
    payload: Mapping[str, object],
    *,
    fallback: UUID,
) -> UUID:
    return (
        _first_uuid(
            payload.get("semantic_apply_receiver_object_id"),
            payload.get("receiver_object_id"),
            payload.get("executable_object_id"),
        )
        or fallback
    )


def _function_impl_receiver_id(
    *,
    operation: OntologyTypedOperation,
) -> UUID | None:
    baseline_id = _first_uuid(
        operation.baseline.get("object_id"),
        mapping_value(operation.baseline.get("object")).get("object_id"),
    )
    current_id = _first_uuid(
        operation.current.get("entity_id"),
        mapping_value(operation.current.get("payload")).get("entity_id"),
    )
    if operation.operation_family == "update":
        return baseline_id or current_id
    return current_id or baseline_id


def _function_impl_source_id(
    *,
    operation: OntologyTypedOperation,
) -> UUID | None:
    current_payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(operation.baseline.get("payload"))
    return _first_uuid(
        operation.current.get("semantic_source_object_id"),
        operation.current.get("source_object_id"),
        operation.current.get("function_impl_id"),
        current_payload.get("semantic_source_object_id"),
        current_payload.get("source_object_id"),
        current_payload.get("function_impl_id"),
        baseline_object.get("semantic_source_object_id"),
        baseline_object.get("source_object_id"),
        baseline_object.get("function_impl_id"),
        operation.baseline.get("semantic_source_object_id"),
        operation.baseline.get("source_object_id"),
        operation.baseline.get("function_impl_id"),
        baseline_payload.get("semantic_source_object_id"),
        baseline_payload.get("source_object_id"),
        baseline_payload.get("function_impl_id"),
        _function_impl_receiver_id(operation=operation),
    )


def _function_impl_signature(
    current: Mapping[str, object],
) -> dict[str, object]:
    return mapping_value(
        current.get("function_impl_signature")
        or mapping_value(current.get("payload")).get("function_impl_signature")
    )


def _function_impl_signature_from_baseline(
    baseline: Mapping[str, object],
) -> dict[str, object]:
    baseline_object = mapping_value(baseline.get("object"))
    return mapping_value(
        baseline_object.get("function_impl_signature")
        or baseline.get("function_impl_signature")
    )


def _instruction_signatures(
    signature: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    return tuple_mappings(signature.get("instructions"))


def _uuid_value(value: object) -> UUID | None:
    text = optional_text(value)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _first_uuid(*values: object) -> UUID | None:
    for value in values:
        uuid_value = _uuid_value(value)
        if uuid_value is not None:
            return uuid_value
    return None


def _int_value(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = optional_text(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


__all__ = ["HANDLER_KEY", "plan_function_impl_operation"]
