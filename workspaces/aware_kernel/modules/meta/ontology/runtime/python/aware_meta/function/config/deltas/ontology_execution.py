from __future__ import annotations

from collections.abc import Iterable, Mapping
from uuid import UUID

from aware_meta.materialization.deltas.ontology_execution.contracts import (
    OntologyExecutionPlanningContext,
    OntologyInvocationIntent,
    OntologyOperationHandlerResult,
    OntologyTypedOperation,
    blocked_handler_result,
)
from aware_meta.materialization.deltas.ontology_execution.receiver_resolution import (
    mapping_value,
    optional_text,
)
from aware_meta.graph.config.stable_ids import (
    stable_function_config_attribute_config_id,
)


HANDLER_KEY = "function.scalar_function_calls"
FUNCTION_INVOCATION_HANDLER_KEY = "function.invocation_plan_function_calls"
CLASS_CONFIG_CREATE_FUNCTION_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.class_.class_config.ClassConfig.create_function_config"
)
CLASS_CONFIG_REMOVE_FUNCTION_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.class_.class_config.ClassConfig.remove_function_config"
)
FUNCTION_CONFIG_UPDATE_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.function.function_config.FunctionConfig.update_config"
)
FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.function.function_config."
    "FunctionConfig.add_primitive_attribute_config"
)
FUNCTION_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.function.function_config.FunctionConfig.remove_attribute_config"
)
FUNCTION_CONFIG_CREATE_INVOCATION_FUNCTION_REF = (
    "aware_meta_ontology.function.function_config.FunctionConfig.create_invocation"
)


def plan_function_operation(
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    if operation.ontology_subject_kind != "function":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_ontology_handler_subject_mismatch",
            blockers=(f"unsupported_subject:{operation.ontology_subject_kind}",),
        )
    if operation.operation_family == "create":
        return _plan_function_create_operation(operation=operation, context=context)
    if operation.operation_family == "delete":
        return _plan_function_delete_operation(operation=operation, context=context)
    if operation.operation_family != "update":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_function_delta_requires_supported_operation",
            blockers=(f"unsupported_operation_family:{operation.operation_family}",),
        )
    return _plan_function_update_operation(operation=operation)


def plan_function_invocation_operation(
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    del context
    if operation.ontology_subject_kind != "function_invocation":
        return blocked_handler_result(
            operation=operation,
            handler_key=FUNCTION_INVOCATION_HANDLER_KEY,
            reason="meta_ocg_ontology_handler_subject_mismatch",
            blockers=(f"unsupported_subject:{operation.ontology_subject_kind}",),
        )
    if operation.operation_family != "create":
        return blocked_handler_result(
            operation=operation,
            handler_key=FUNCTION_INVOCATION_HANDLER_KEY,
            reason="meta_ocg_function_invocation_delta_requires_create_operation",
            blockers=(f"unsupported_operation_family:{operation.operation_family}",),
        )
    return _plan_function_invocation_create_operation(operation=operation)


def _plan_function_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    owner_semantic_key = _function_owner_semantic_key(operation=operation)
    class_config_id = _function_owner_class_config_id(
        operation=operation,
        context=context,
        owner_semantic_key=owner_semantic_key,
    )
    function_config_id = _function_create_object_id(operation=operation)
    function_name = _function_name(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("owner_semantic_key", owner_semantic_key),
            ("class_config_id", class_config_id),
            ("function_config_id", function_config_id),
            ("function_name", function_name),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_function_create_requires_owner_and_signature",
            blockers=tuple(f"missing_function_create_{field}" for field in missing),
        )

    assert owner_semantic_key is not None
    assert class_config_id is not None
    assert function_config_id is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_function_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_function",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=0,
                invocation_mode="instance",
                owner_class_name="ClassConfig",
                function_name="create_function_config",
                function_ref=CLASS_CONFIG_CREATE_FUNCTION_CONFIG_FUNCTION_REF,
                target_object_id=class_config_id,
                receiver_semantic_key=owner_semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=function_config_id,
                kwargs=_function_create_arguments(operation=operation),
                reason="meta_ocg_function_create_config_function_call_ready",
            ),
        ),
    )


def _plan_function_delete_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    owner_semantic_key = _function_owner_semantic_key(operation=operation)
    class_config_id = _function_owner_class_config_id(
        operation=operation,
        context=context,
        owner_semantic_key=owner_semantic_key,
    )
    function_config_id = _function_delete_object_id(operation=operation)
    function_name = _function_name(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("owner_semantic_key", owner_semantic_key),
            ("class_config_id", class_config_id),
            ("function_config_id", function_config_id),
            ("function_name", function_name),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_function_delete_requires_parent_and_function_identity",
            blockers=tuple(f"missing_function_delete_{field}" for field in missing),
        )

    assert owner_semantic_key is not None
    assert class_config_id is not None
    assert function_config_id is not None
    assert function_name is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_function_delete_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:delete_function",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=0,
                invocation_mode="instance",
                owner_class_name="ClassConfig",
                function_name="remove_function_config",
                function_ref=CLASS_CONFIG_REMOVE_FUNCTION_CONFIG_FUNCTION_REF,
                target_object_id=class_config_id,
                receiver_semantic_key=owner_semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=function_config_id,
                commit_required=True,
                kwargs={
                    "name": function_name,
                    "function_config_id": function_config_id,
                },
                reason="meta_ocg_function_delete_membership_remove_ready",
            ),
        ),
    )


def _plan_function_update_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    function_config_id = _function_update_source_object_id(operation=operation)
    receiver_object_id = _function_update_receiver_object_id(operation=operation)
    if receiver_object_id is None:
        receiver_object_id = function_config_id
    identity_blockers = _function_identity_update_blockers(operation=operation)
    blockers = (
        ("missing_function_update_function_config_id",)
        if function_config_id is None
        else ()
    )
    blockers += (
        ("missing_function_update_receiver_object_id",)
        if receiver_object_id is None
        else ()
    )
    blockers += identity_blockers
    if blockers:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_function_update_requires_existing_function_config",
            blockers=blockers,
        )

    assert function_config_id is not None
    assert receiver_object_id is not None
    membership_intents_or_blockers = _function_signature_membership_intents(
        operation=operation,
        function_config_id=function_config_id,
        receiver_object_id=receiver_object_id,
    )
    if membership_intents_or_blockers and all(
        isinstance(item, str) for item in membership_intents_or_blockers
    ):
        membership_blockers = tuple(
            item
            for item in membership_intents_or_blockers
            if isinstance(item, str)
        )
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_function_update_signature_membership_blocked",
            blockers=membership_blockers,
        )
    membership_intents = tuple(
        intent
        for intent in membership_intents_or_blockers
        if isinstance(intent, OntologyInvocationIntent)
    )
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_function_update_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:update_function",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=0,
                invocation_mode="instance",
                owner_class_name="FunctionConfig",
                function_name="update_config",
                function_ref=FUNCTION_CONFIG_UPDATE_CONFIG_FUNCTION_REF,
                target_object_id=receiver_object_id,
                receiver_semantic_key=operation.semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=function_config_id,
                kwargs=_function_update_arguments(operation=operation),
                reason="meta_ocg_function_update_mutable_config_ready",
            ),
            *membership_intents,
        ),
    )


def _function_signature_membership_intents(
    *,
    operation: OntologyTypedOperation,
    function_config_id: str,
    receiver_object_id: str,
) -> tuple[OntologyInvocationIntent | str, ...]:
    baseline_inputs = _function_signature_inputs_by_name(
        signature=_function_baseline_signature(operation=operation),
    )
    current_inputs = _function_signature_inputs_by_name(
        signature=_function_signature(operation=operation),
    )
    if not baseline_inputs and not current_inputs:
        return ()
    blockers: list[str] = []
    function_config_uuid = _uuid_text(function_config_id)
    if function_config_uuid is None:
        return ("function_signature_membership_requires_function_config_uuid",)
    intents: list[OntologyInvocationIntent] = []
    removed_names = tuple(
        name for name in sorted(baseline_inputs) if name not in current_inputs
    )
    added_names = tuple(
        name for name in sorted(current_inputs) if name not in baseline_inputs
    )
    for index, name in enumerate(removed_names, start=10):
        baseline_input = baseline_inputs[name]
        intents.append(
            OntologyInvocationIntent(
                intent_key=(
                    f"{operation.operation_key}:remove_input:{name}"
                ),
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=index,
                invocation_mode="instance",
                owner_class_name="FunctionConfig",
                function_name="remove_attribute_config",
                function_ref=FUNCTION_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF,
                target_object_id=receiver_object_id,
                receiver_semantic_key=operation.semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=function_config_id,
                kwargs={
                    "name": name,
                    "type": _first_text(baseline_input.get("type"), "input"),
                    "attribute_config_id": baseline_input.get(
                        "function_config_attribute_config_id"
                    ),
                },
                reason="meta_ocg_function_signature_remove_input_ready",
            )
        )
    for offset, name in enumerate(added_names, start=20):
        current_input = current_inputs[name]
        primitive_base_type = _function_signature_input_primitive_base_type(
            input_payload=current_input,
        )
        if primitive_base_type is None:
            blockers.append(
                f"function_signature_input_requires_primitive_type:{name}"
            )
            continue
        input_type = _first_text(current_input.get("type"), "input") or "input"
        input_edge_id = stable_function_config_attribute_config_id(
            function_config_id=function_config_uuid,
            name=name,
            type=input_type,
        )
        intents.append(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:add_input:{name}",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=offset,
                invocation_mode="instance",
                owner_class_name="FunctionConfig",
                function_name="add_primitive_attribute_config",
                function_ref=(
                    FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_CONFIG_FUNCTION_REF
                ),
                target_object_id=receiver_object_id,
                receiver_semantic_key=operation.semantic_key,
                result_semantic_key=(
                    f"{operation.semantic_key}/attribute:input:{name}"
                ),
                expected_result_object_id=str(input_edge_id),
                kwargs={
                    "name": name,
                    "primitive_base_type": primitive_base_type,
                    "description": current_input.get("description"),
                    "default_value": current_input.get("default_value"),
                    "is_primary": current_input.get("is_primary") is True,
                    "is_public": current_input.get("is_public") is not False,
                    "is_required": current_input.get("is_required") is not False,
                    "is_unique": current_input.get("is_unique") is True,
                    "is_virtual": current_input.get("is_virtual") is True,
                    "type": input_type,
                    "position": _int_value(current_input.get("position")) or 0,
                    "is_identity_key": (
                        current_input.get("is_identity_key") is True
                    ),
                },
                reason="meta_ocg_function_signature_add_input_ready",
            )
        )
    if blockers:
        return tuple(blockers)
    return tuple(intents)


def _function_signature_inputs_by_name(
    *,
    signature: dict[str, object],
) -> dict[str, dict[str, object]]:
    inputs: dict[str, dict[str, object]] = {}
    for raw_input in _tuple_values(signature.get("inputs")):
        input_payload = mapping_value(raw_input)
        input_name = optional_text(input_payload.get("name"))
        input_type = _first_text(input_payload.get("type"), "input")
        if input_name is None or input_type != "input":
            continue
        inputs[input_name] = input_payload
    return inputs


def _function_signature_input_primitive_base_type(
    *,
    input_payload: dict[str, object],
) -> str | None:
    descriptor = mapping_value(input_payload.get("type_descriptor"))
    descriptor_kind = _first_text(
        descriptor.get("descriptor_kind"),
        descriptor.get("kind"),
    )
    if descriptor_kind not in {None, "primitive"}:
        return None
    return _first_text(
        descriptor.get("primitive_base_type"),
        input_payload.get("primitive_base_type"),
        "any",
    )


def _plan_function_invocation_create_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    function_config_id = _function_invocation_owner_function_config_id(
        operation=operation,
    )
    position = _function_invocation_position(operation=operation)
    kind = _function_invocation_kind(operation=operation)
    target_function_config_id = _function_invocation_target_function_config_id(
        operation=operation,
    )
    relationship_fingerprint = _function_invocation_relationship_fingerprint(
        operation=operation,
    )
    class_config_relationship_id = _function_invocation_class_relationship_id(
        operation=operation,
    )
    missing = tuple(
        field_name
        for field_name, value in (
            ("function_config_id", function_config_id),
            ("position", position),
            ("kind", kind),
            ("target_function_config_id", target_function_config_id),
        )
        if value is None
    )
    blockers = tuple(
        f"missing_function_invocation_create_{field}"
        for field in missing
    )
    if (
        class_config_relationship_id is None
        and relationship_fingerprint is not None
        and relationship_fingerprint != "owner"
    ):
        blockers += (
            "function_invocation_relationship_fingerprint_requires_relationship_id",
        )
    if blockers:
        return blocked_handler_result(
            operation=operation,
            handler_key=FUNCTION_INVOCATION_HANDLER_KEY,
            reason="meta_ocg_function_invocation_create_requires_parent_and_target",
            blockers=blockers,
        )

    assert function_config_id is not None
    assert position is not None
    assert kind is not None
    assert target_function_config_id is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=FUNCTION_INVOCATION_HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_function_invocation_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_invocation",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=0,
                invocation_mode="instance",
                owner_class_name="FunctionConfig",
                function_name="create_invocation",
                function_ref=FUNCTION_CONFIG_CREATE_INVOCATION_FUNCTION_REF,
                target_object_id=function_config_id,
                receiver_semantic_key=_function_invocation_function_semantic_key(
                    operation=operation,
                ),
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=_function_invocation_object_id(
                    operation=operation,
                ),
                kwargs=_function_invocation_create_arguments(
                    operation=operation,
                    position=position,
                    kind=kind,
                    target_function_config_id=target_function_config_id,
                ),
                reason=(
                    "meta_ocg_function_invocation_create_config_function_call_ready"
                ),
            ),
        ),
    )


def _function_create_arguments(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    signature = _function_signature(operation=operation)
    membership_signature = _function_membership_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return {
        "name": _function_name(operation=operation),
        "description": _first_text(
            operation.current.get("description"),
            operation.current.get("function_description"),
            payload.get("description"),
            payload.get("function_description"),
            signature.get("description"),
        ),
        "verb": _first_text(
            operation.current.get("verb"),
            operation.current.get("function_verb"),
            payload.get("verb"),
            payload.get("function_verb"),
            signature.get("verb"),
        ),
        "is_async": _bool_value(
            _first_value(
                operation.current.get("is_async"),
                payload.get("is_async"),
                signature.get("is_async"),
                False,
            )
        ),
        "kind": _first_text(
            operation.current.get("kind"),
            payload.get("kind"),
            signature.get("kind"),
            "instance",
        ),
        "is_public": _bool_value(
            _first_value(
                operation.current.get("is_public"),
                payload.get("is_public"),
                membership_signature.get("is_public"),
                True,
            )
        ),
        "is_constructor": _bool_value(
            _first_value(
                operation.current.get("is_constructor"),
                payload.get("is_constructor"),
                membership_signature.get("is_constructor"),
                False,
            )
        ),
        "position": _int_value(
            _first_value(
                operation.current.get("position"),
                payload.get("position"),
                membership_signature.get("position"),
                0,
            )
        ),
    }


def _function_invocation_create_arguments(
    *,
    operation: OntologyTypedOperation,
    position: int,
    kind: str,
    target_function_config_id: str,
) -> dict[str, object]:
    signature = _function_invocation_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return {
        "position": position,
        "kind": kind,
        "target_function_config_id": target_function_config_id,
        "relationship_fingerprint": _first_text(
            operation.current.get("relationship_fingerprint"),
            payload.get("relationship_fingerprint"),
            signature.get("relationship_fingerprint"),
            "owner",
        ),
        "class_config_relationship_id": _first_text(
            operation.current.get("class_config_relationship_id"),
            payload.get("class_config_relationship_id"),
            signature.get("class_config_relationship_id"),
        ),
        "root_invocation_id": _first_text(
            operation.current.get("root_invocation_id"),
            payload.get("root_invocation_id"),
            signature.get("root_invocation_id"),
        ),
        "root_kind": _first_text(
            operation.current.get("root_kind"),
            payload.get("root_kind"),
            signature.get("root_kind"),
            "owner",
        ),
        "capture_name": _first_text(
            operation.current.get("capture_name"),
            payload.get("capture_name"),
            signature.get("capture_name"),
        ),
    }


def _function_update_arguments(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    signature = _function_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return {
        "description": _first_text(
            operation.current.get("function_description"),
            payload.get("function_description"),
            signature.get("description"),
            operation.current.get("description"),
            payload.get("description"),
        ),
        "verb": _first_text(
            operation.current.get("function_verb"),
            payload.get("function_verb"),
            signature.get("verb"),
        ),
        "is_async": _bool_value(
            _first_value(
                operation.current.get("is_async"),
                payload.get("is_async"),
                signature.get("is_async"),
            )
        ),
    }


def _function_update_receiver_object_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        operation.current.get("semantic_apply_receiver_object_id"),
        payload.get("semantic_apply_receiver_object_id"),
        operation.current.get("receiver_object_id"),
        payload.get("receiver_object_id"),
        operation.current.get("executable_object_id"),
        payload.get("executable_object_id"),
        baseline_object.get("semantic_apply_receiver_object_id"),
        baseline_payload.get("semantic_apply_receiver_object_id"),
        baseline_object.get("receiver_object_id"),
        baseline_payload.get("receiver_object_id"),
        baseline_object.get("executable_object_id"),
        baseline_payload.get("executable_object_id"),
    )


def _function_update_source_object_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        operation.current.get("entity_id"),
        payload.get("entity_id"),
        operation.current.get("function_config_id"),
        payload.get("function_config_id"),
        baseline_object.get("entity_id"),
        baseline_payload.get("entity_id"),
        baseline_object.get("function_config_id"),
        baseline_payload.get("function_config_id"),
        operation.baseline.get("entity_id"),
        operation.baseline.get("function_config_id"),
        operation.baseline.get("object_id"),
        baseline_object.get("object_id"),
        operation.current.get("object_id"),
        payload.get("object_id"),
    )


def _function_delete_object_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        operation.current.get("semantic_source_object_id"),
        payload.get("semantic_source_object_id"),
        baseline_object.get("semantic_source_object_id"),
        baseline_payload.get("semantic_source_object_id"),
        operation.baseline.get("semantic_source_object_id"),
        operation.baseline.get("entity_id"),
        operation.baseline.get("function_config_id"),
        baseline_object.get("entity_id"),
        baseline_payload.get("entity_id"),
        baseline_object.get("function_config_id"),
        baseline_payload.get("function_config_id"),
        _function_update_source_object_id(operation=operation),
    )


def _function_invocation_owner_function_config_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _function_invocation_signature(operation=operation)
    return _first_text(
        operation.current.get("function_config_id"),
        payload.get("function_config_id"),
        signature.get("function_config_id"),
    )


def _function_invocation_object_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _function_invocation_signature(operation=operation)
    return _first_text(
        operation.current.get("function_config_invocation_id"),
        operation.current.get("entity_id"),
        operation.current.get("object_id"),
        payload.get("function_config_invocation_id"),
        payload.get("entity_id"),
        payload.get("object_id"),
        signature.get("function_config_invocation_id"),
        signature.get("entity_id"),
        signature.get("object_id"),
    )


def _function_invocation_function_semantic_key(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _function_invocation_signature(operation=operation)
    return _first_text(
        operation.current.get("function_semantic_key"),
        operation.current.get("parent_semantic_key"),
        payload.get("function_semantic_key"),
        payload.get("parent_semantic_key"),
        signature.get("function_semantic_key"),
        _function_semantic_key_from_invocation_semantic_key(
            operation.semantic_key,
        ),
    )


def _function_invocation_position(
    *,
    operation: OntologyTypedOperation,
) -> int | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _function_invocation_signature(operation=operation)
    return _optional_int(
        _first_value(
            operation.current.get("position"),
            payload.get("position"),
            signature.get("position"),
        )
    )


def _function_invocation_kind(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _function_invocation_signature(operation=operation)
    return _first_text(
        operation.current.get("kind"),
        payload.get("kind"),
        signature.get("kind"),
    )


def _function_invocation_target_function_config_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _function_invocation_signature(operation=operation)
    return _first_text(
        operation.current.get("target_function_config_id"),
        payload.get("target_function_config_id"),
        signature.get("target_function_config_id"),
    )


def _function_invocation_relationship_fingerprint(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _function_invocation_signature(operation=operation)
    return _first_text(
        operation.current.get("relationship_fingerprint"),
        payload.get("relationship_fingerprint"),
        signature.get("relationship_fingerprint"),
        "owner",
    )


def _function_invocation_class_relationship_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _function_invocation_signature(operation=operation)
    return _first_text(
        operation.current.get("class_config_relationship_id"),
        payload.get("class_config_relationship_id"),
        signature.get("class_config_relationship_id"),
    )


def _function_create_object_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    membership_signature = _function_membership_signature(operation=operation)
    return _first_text(
        operation.current.get("entity_id"),
        payload.get("entity_id"),
        operation.current.get("function_config_id"),
        payload.get("function_config_id"),
        membership_signature.get("function_config_id"),
    )


def _function_owner_class_config_id(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
    owner_semantic_key: str | None,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    membership_signature = _function_membership_signature(operation=operation)
    direct = _first_text(
        operation.current.get("class_config_id"),
        payload.get("class_config_id"),
        membership_signature.get("class_config_id"),
    )
    if direct is not None:
        return direct
    if owner_semantic_key is None:
        return None
    owner_operation = context.operation_by_semantic_key.get(owner_semantic_key)
    if owner_operation is None:
        return None
    owner_payload = mapping_value(owner_operation.current.get("payload"))
    owner_baseline_object = mapping_value(owner_operation.baseline.get("object"))
    return _first_text(
        owner_operation.current.get("entity_id"),
        owner_payload.get("entity_id"),
        owner_operation.current.get("class_config_id"),
        owner_payload.get("class_config_id"),
        owner_operation.baseline.get("object_id"),
        owner_operation.baseline.get("entity_id"),
        owner_baseline_object.get("object_id"),
        owner_baseline_object.get("entity_id"),
        owner_baseline_object.get("class_config_id"),
    )


def _function_owner_semantic_key(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("owner_semantic_key"),
        operation.current.get("parent_semantic_key"),
        operation.current.get("class_semantic_key"),
        payload.get("owner_semantic_key"),
        payload.get("parent_semantic_key"),
        payload.get("class_semantic_key"),
    )


def _function_name(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    signature = _function_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("function_name"),
        operation.current.get("name"),
        operation.current.get("entity_name"),
        payload.get("function_name"),
        payload.get("name"),
        payload.get("entity_name"),
        signature.get("name"),
        _function_name_from_semantic_key(operation.semantic_key),
    )


def _function_identity_update_blockers(
    *,
    operation: OntologyTypedOperation,
) -> tuple[str, ...]:
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_signature = _function_baseline_signature(operation=operation)
    current_signature = _function_signature(operation=operation)
    current_payload = mapping_value(operation.current.get("payload"))

    baseline_owner_key = _first_text(
        operation.baseline.get("owner_key"),
        baseline_object.get("owner_key"),
        baseline_signature.get("owner_key"),
        operation.baseline.get("owner_semantic_key"),
        baseline_object.get("owner_semantic_key"),
    )
    current_owner_key = _first_text(
        operation.current.get("owner_key"),
        current_payload.get("owner_key"),
        current_signature.get("owner_key"),
        operation.current.get("owner_semantic_key"),
        current_payload.get("owner_semantic_key"),
    )
    baseline_name = _first_text(
        operation.baseline.get("name"),
        baseline_object.get("name"),
        baseline_object.get("function_name"),
        baseline_signature.get("name"),
        baseline_signature.get("function_name"),
        _function_name_from_semantic_key(operation.semantic_key),
    )
    current_name = _first_text(
        operation.current.get("name"),
        operation.current.get("function_name"),
        operation.current.get("entity_name"),
        current_payload.get("name"),
        current_payload.get("function_name"),
        current_payload.get("entity_name"),
        current_signature.get("name"),
        current_signature.get("function_name"),
        _function_name_from_semantic_key(operation.semantic_key),
    )
    baseline_kind = _first_text(
        operation.baseline.get("kind"),
        baseline_object.get("kind"),
        baseline_signature.get("kind"),
    )
    current_kind = _first_text(
        operation.current.get("kind"),
        current_payload.get("kind"),
        current_signature.get("kind"),
    )

    blockers: list[str] = []
    if (
        baseline_owner_key is not None
        and current_owner_key is not None
        and baseline_owner_key != current_owner_key
    ):
        blockers.append("function_identity_change_requires_replacement:owner_key")
    if (
        baseline_name is not None
        and current_name is not None
        and baseline_name != current_name
    ):
        blockers.append("function_identity_change_requires_replacement:name")
    if (
        baseline_kind is not None
        and current_kind is not None
        and baseline_kind != current_kind
    ):
        blockers.append("function_identity_change_requires_replacement:kind")
    return tuple(blockers)


def _function_signature(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    return mapping_value(
        operation.current.get("function_signature")
        or payload.get("function_signature")
    )


def _function_membership_signature(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    return mapping_value(
        operation.current.get("function_membership_signature")
        or payload.get("function_membership_signature")
    )


def _function_invocation_signature(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    return mapping_value(
        operation.current.get("function_invocation_signature")
        or payload.get("function_invocation_signature")
    )


def _function_baseline_signature(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    baseline_object = mapping_value(operation.baseline.get("object"))
    return mapping_value(
        operation.baseline.get("function_signature")
        or baseline_object.get("function_signature")
    )


def _function_name_from_semantic_key(value: str) -> str | None:
    _, function_separator, function_tail = value.partition("/function:")
    if function_separator:
        return optional_text(function_tail.split("/", 1)[0])
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    leaf = node_key.rsplit(".", 1)[-1]
    return optional_text(leaf.split("/", 1)[0])


def _function_semantic_key_from_invocation_semantic_key(
    value: str,
) -> str | None:
    for separator in ("/invocation:", "/function_invocation:"):
        function_key, found, _tail = value.partition(separator)
        if found:
            return optional_text(function_key)
    return None


def _first_text(*values: object) -> str | None:
    for value in values:
        text = optional_text(value)
        if text is not None:
            return text
    return None


def _first_value(*values: object) -> object | None:
    for value in values:
        if value is not None:
            return value
    return None


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = optional_text(value)
    if text is None:
        return False
    return text.casefold() in {"1", "true", "yes", "y", "on"}


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = optional_text(value)
    if text is None:
        return 0
    return int(text)


def _tuple_values(value: object) -> tuple[object, ...]:
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
        return tuple(value)
    return ()


def _uuid_text(value: object) -> UUID | None:
    text = optional_text(value)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return _int_value(value)


__all__ = [
    "CLASS_CONFIG_CREATE_FUNCTION_CONFIG_FUNCTION_REF",
    "FUNCTION_CONFIG_ADD_PRIMITIVE_ATTRIBUTE_CONFIG_FUNCTION_REF",
    "FUNCTION_CONFIG_CREATE_INVOCATION_FUNCTION_REF",
    "FUNCTION_CONFIG_REMOVE_ATTRIBUTE_CONFIG_FUNCTION_REF",
    "FUNCTION_CONFIG_UPDATE_CONFIG_FUNCTION_REF",
    "FUNCTION_INVOCATION_HANDLER_KEY",
    "HANDLER_KEY",
    "plan_function_invocation_operation",
    "plan_function_operation",
]
