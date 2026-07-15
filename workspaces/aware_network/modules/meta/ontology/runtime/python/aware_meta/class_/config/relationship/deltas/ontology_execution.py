from __future__ import annotations

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
    string_value,
)


HANDLER_KEY = "relationship.class_config_function_calls"
CLASS_CONFIG_CREATE_RELATIONSHIP_FUNCTION_REF = (
    "aware_meta_ontology.class_.class_config.ClassConfig.create_relationship"
)
CLASS_CONFIG_REMOVE_RELATIONSHIP_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.class_.class_config.ClassConfig.remove_relationship_config"
)
CLASS_CONFIG_RELATIONSHIP_UPDATE_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.class_.class_config_relationship."
    "ClassConfigRelationship.update_config"
)
CLASS_CONFIG_RELATIONSHIP_CREATE_ASSOCIATION_FUNCTION_REF = (
    "aware_meta_ontology.class_.class_config_relationship."
    "ClassConfigRelationship.create_association"
)
CLASS_CONFIG_RELATIONSHIP_CREATE_ATTRIBUTE_FUNCTION_REF = (
    "aware_meta_ontology.class_.class_config_relationship."
    "ClassConfigRelationship.create_attribute"
)


def plan_relationship_operation(
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    if operation.ontology_subject_kind != "relationship":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_ontology_handler_subject_mismatch",
            blockers=(f"unsupported_subject:{operation.ontology_subject_kind}",),
        )
    if operation.operation_family == "create":
        return _plan_relationship_create_operation(
            operation=operation,
            context=context,
        )
    if operation.operation_family == "update":
        return _plan_relationship_update_operation(operation=operation)
    if operation.operation_family == "delete":
        return _plan_relationship_delete_operation(
            operation=operation,
            context=context,
        )
    return blocked_handler_result(
        operation=operation,
        handler_key=HANDLER_KEY,
        reason="meta_ocg_relationship_delta_requires_supported_operation",
        blockers=(f"unsupported_operation_family:{operation.operation_family}",),
    )


def _plan_relationship_association_create_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    relationship_object_id = _relationship_receiver_object_id(operation=operation)
    association_class_config_id = _relationship_association_class_config_id(
        operation=operation,
    )
    missing = tuple(
        field_name
        for field_name, value in (
            ("relationship_object_id", relationship_object_id),
            ("association_class_config_id", association_class_config_id),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason=("meta_ocg_relationship_association_create_requires_signature"),
            blockers=tuple(
                f"missing_relationship_association_create_{field}" for field in missing
            ),
        )

    assert relationship_object_id is not None
    assert association_class_config_id is not None
    signature = _relationship_association_signature(operation=operation)
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_relationship_association_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_association",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=0,
                invocation_mode="instance",
                owner_class_name="ClassConfigRelationship",
                function_name="create_association",
                function_ref=(
                    CLASS_CONFIG_RELATIONSHIP_CREATE_ASSOCIATION_FUNCTION_REF
                ),
                target_object_id=relationship_object_id,
                receiver_semantic_key=_relationship_receiver_semantic_key(
                    operation=operation,
                ),
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=(
                    _relationship_association_object_id(operation=operation)
                ),
                kwargs={
                    "class_config_id": association_class_config_id,
                    "forward_loading_strategy": _first_text(
                        operation.current.get("forward_loading_strategy"),
                        signature.get("forward_loading_strategy"),
                    ),
                    "reverse_loading_strategy": _first_text(
                        operation.current.get("reverse_loading_strategy"),
                        signature.get("reverse_loading_strategy"),
                    ),
                },
                reason=("meta_ocg_relationship_association_create_child_edge_ready"),
            ),
        ),
    )


def _plan_relationship_attribute_create_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    relationship_object_id = _relationship_receiver_object_id(operation=operation)
    attribute_config_id = _relationship_attribute_config_id(operation=operation)
    direction = _relationship_attribute_direction(operation=operation)
    role = _relationship_attribute_role(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("relationship_object_id", relationship_object_id),
            ("attribute_config_id", attribute_config_id),
            ("direction", direction),
            ("role", role),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_relationship_attribute_create_requires_signature",
            blockers=tuple(
                f"missing_relationship_attribute_create_{field}" for field in missing
            ),
        )

    assert relationship_object_id is not None
    assert attribute_config_id is not None
    assert direction is not None
    assert role is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_relationship_attribute_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_attribute",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=0,
                invocation_mode="instance",
                owner_class_name="ClassConfigRelationship",
                function_name="create_attribute",
                function_ref=(CLASS_CONFIG_RELATIONSHIP_CREATE_ATTRIBUTE_FUNCTION_REF),
                target_object_id=relationship_object_id,
                receiver_semantic_key=_relationship_receiver_semantic_key(
                    operation=operation,
                ),
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=(
                    _relationship_attribute_object_id(operation=operation)
                ),
                kwargs={
                    "attribute_config_id": attribute_config_id,
                    "direction": direction,
                    "role": role,
                },
                reason=("meta_ocg_relationship_attribute_create_child_edge_ready"),
            ),
        ),
    )


def _plan_relationship_update_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    relationship_object_id = _relationship_update_object_id(operation=operation)
    relationship_type = _relationship_type(operation=operation)
    identity_blockers = _relationship_identity_update_blockers(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("relationship_object_id", relationship_object_id),
            ("relationship_type", relationship_type),
        )
        if value is None
    )
    blockers = tuple(f"missing_relationship_update_{field}" for field in missing)
    blockers += identity_blockers
    if blockers:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_relationship_update_requires_existing_relationship",
            blockers=blockers,
        )

    assert relationship_object_id is not None
    assert relationship_type is not None
    arguments = _relationship_update_arguments(
        operation=operation,
        relationship_type=relationship_type,
    )
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_relationship_update_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:update_relationship",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=0,
                invocation_mode="instance",
                owner_class_name="ClassConfigRelationship",
                function_name="update_config",
                function_ref=CLASS_CONFIG_RELATIONSHIP_UPDATE_CONFIG_FUNCTION_REF,
                target_object_id=relationship_object_id,
                receiver_semantic_key=operation.semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=relationship_object_id,
                kwargs=arguments,
                reason="meta_ocg_relationship_update_mutable_config_ready",
            ),
        ),
    )


def _plan_relationship_delete_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    relationship_object_id = _relationship_delete_object_id(operation=operation)
    source_class_config_id = _relationship_source_class_config_id(
        operation=operation,
        context=context,
    )
    relationship_key = _relationship_key(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("relationship_object_id", relationship_object_id),
            ("source_class_config_id", source_class_config_id),
            ("relationship_key", relationship_key),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_relationship_delete_requires_baseline_identity",
            blockers=tuple(f"missing_relationship_delete_{field}" for field in missing),
        )

    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_relationship_delete_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:delete_relationship",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=0,
                invocation_mode="instance",
                owner_class_name="ClassConfig",
                function_name="remove_relationship_config",
                function_ref=CLASS_CONFIG_REMOVE_RELATIONSHIP_CONFIG_FUNCTION_REF,
                target_object_id=source_class_config_id,
                receiver_semantic_key=_relationship_source_semantic_key(
                    semantic_key=operation.semantic_key,
                ),
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=relationship_object_id,
                kwargs={
                    "relationship_key": relationship_key,
                    "relationship_config_id": relationship_object_id,
                },
                reason="meta_ocg_relationship_delete_membership_remove_ready",
            ),
        ),
    )


def _plan_relationship_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    if _provider_operation_type(operation=operation) == (
        "meta_ocg.relationship.association.create"
    ):
        return _plan_relationship_association_create_operation(operation=operation)
    if _provider_operation_type(operation=operation) == (
        "meta_ocg.relationship.attribute.create"
    ):
        return _plan_relationship_attribute_create_operation(operation=operation)

    source_class_config_id = _relationship_source_class_config_id(
        operation=operation,
        context=context,
    )
    target_class_config_id = _relationship_target_class_config_id(operation=operation)
    relationship_key = _relationship_key(operation=operation)
    relationship_type = _relationship_type(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("source_class_config_id", source_class_config_id),
            ("target_class_config_id", target_class_config_id),
            ("relationship_key", relationship_key),
            ("relationship_type", relationship_type),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_relationship_create_requires_signature",
            blockers=tuple(f"missing_relationship_create_{field}" for field in missing),
        )

    arguments = _relationship_create_arguments(
        operation=operation,
        target_class_config_id=string_value(target_class_config_id),
        relationship_key=string_value(relationship_key),
        relationship_type=string_value(relationship_type),
    )
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_relationship_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_relationship",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=0,
                invocation_mode="instance",
                owner_class_name="ClassConfig",
                function_name="create_relationship",
                function_ref=CLASS_CONFIG_CREATE_RELATIONSHIP_FUNCTION_REF,
                target_object_id=source_class_config_id,
                receiver_semantic_key=_relationship_source_semantic_key(
                    semantic_key=operation.semantic_key,
                ),
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=_relationship_object_id(operation=operation),
                kwargs=arguments,
            ),
        ),
    )


def _relationship_create_arguments(
    *,
    operation: OntologyTypedOperation,
    target_class_config_id: str,
    relationship_key: str,
    relationship_type: str,
) -> dict[str, object]:
    signature = _relationship_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return {
        "target_class_config_id": target_class_config_id,
        "relationship_key": relationship_key,
        "relationship_type": relationship_type,
        "identity_rail": _first_text(
            operation.current.get("identity_rail"),
            payload.get("identity_rail"),
            signature.get("identity_rail"),
        ),
        "forward_required": _bool_value(
            _first_value(
                operation.current.get("forward_required"),
                payload.get("forward_required"),
                signature.get("forward_required"),
            )
        ),
        "forward_loading_strategy": _first_text(
            operation.current.get("forward_loading_strategy"),
            payload.get("forward_loading_strategy"),
            signature.get("forward_loading_strategy"),
        ),
        "reverse_loading_strategy": _first_text(
            operation.current.get("reverse_loading_strategy"),
            payload.get("reverse_loading_strategy"),
            signature.get("reverse_loading_strategy"),
        ),
        "reified_from_relationship_id": _first_text(
            operation.current.get("reified_from_relationship_id"),
            payload.get("reified_from_relationship_id"),
            signature.get("reified_from_relationship_id"),
        ),
        "reified_role": _first_text(
            operation.current.get("reified_role"),
            payload.get("reified_role"),
            signature.get("reified_role"),
        ),
    }


def _relationship_update_arguments(
    *,
    operation: OntologyTypedOperation,
    relationship_type: str,
) -> dict[str, object]:
    signature = _relationship_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return {
        "relationship_type": relationship_type,
        "identity_rail": _first_text(
            operation.current.get("identity_rail"),
            payload.get("identity_rail"),
            signature.get("identity_rail"),
        ),
        "forward_required": _bool_value(
            _first_value(
                operation.current.get("forward_required"),
                payload.get("forward_required"),
                signature.get("forward_required"),
            )
        ),
        "forward_loading_strategy": _first_text(
            operation.current.get("forward_loading_strategy"),
            payload.get("forward_loading_strategy"),
            signature.get("forward_loading_strategy"),
        ),
        "reverse_loading_strategy": _first_text(
            operation.current.get("reverse_loading_strategy"),
            payload.get("reverse_loading_strategy"),
            signature.get("reverse_loading_strategy"),
        ),
        "reified_from_relationship_id": _first_text(
            operation.current.get("reified_from_relationship_id"),
            payload.get("reified_from_relationship_id"),
            signature.get("reified_from_relationship_id"),
        ),
        "reified_role": _first_text(
            operation.current.get("reified_role"),
            payload.get("reified_role"),
            signature.get("reified_role"),
        ),
    }


def _relationship_source_class_config_id(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> str | None:
    signature = _relationship_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    direct = _first_text(
        operation.current.get("source_class_config_id"),
        payload.get("source_class_config_id"),
        signature.get("source_class_config_id"),
        operation.current.get("class_config_id"),
        payload.get("class_config_id"),
        signature.get("class_config_id"),
    )
    if direct is not None:
        return direct
    source_semantic_key = _relationship_source_semantic_key(
        semantic_key=operation.semantic_key,
    )
    if source_semantic_key is None:
        return None
    anchor = context.operation_by_semantic_key.get(source_semantic_key)
    if anchor is None:
        return None
    return _first_text(
        anchor.current.get("entity_id"),
        anchor.current.get("object_id"),
        anchor.baseline.get("object_id"),
    )


def _relationship_target_class_config_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    signature = _relationship_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("target_class_config_id"),
        payload.get("target_class_config_id"),
        signature.get("target_class_config_id"),
    )


def _relationship_key(*, operation: OntologyTypedOperation) -> str | None:
    signature = _relationship_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("relationship_key"),
        payload.get("relationship_key"),
        signature.get("relationship_key"),
        _relationship_key_from_semantic_key(operation.semantic_key),
    )


def _relationship_type(*, operation: OntologyTypedOperation) -> str | None:
    signature = _relationship_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("relationship_type"),
        payload.get("relationship_type"),
        signature.get("relationship_type"),
        _relationship_type_from_semantic_key(operation.semantic_key),
    )


def _relationship_signature(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    return mapping_value(
        operation.current.get("relationship_signature")
        or payload.get("relationship_signature")
    )


def _relationship_baseline_signature(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    baseline_object = mapping_value(operation.baseline.get("object"))
    return mapping_value(
        operation.baseline.get("relationship_signature")
        or baseline_object.get("relationship_signature")
    )


def _relationship_association_signature(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    return mapping_value(
        operation.current.get("relationship_association_signature")
        or operation.current.get("association_signature")
        or payload.get("relationship_association_signature")
        or payload.get("association_signature")
    )


def _relationship_attribute_signature(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    return mapping_value(
        operation.current.get("relationship_attribute_signature")
        or operation.current.get("attribute_signature")
        or payload.get("relationship_attribute_signature")
        or payload.get("attribute_signature")
    )


def _relationship_receiver_object_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _relationship_signature(operation=operation)
    baseline_object = mapping_value(operation.baseline.get("object"))
    return _first_text(
        operation.current.get("relationship_config_id"),
        operation.current.get("class_config_relationship_id"),
        operation.current.get("relationship_object_id"),
        payload.get("relationship_config_id"),
        payload.get("class_config_relationship_id"),
        payload.get("relationship_object_id"),
        signature.get("relationship_config_id"),
        signature.get("class_config_relationship_id"),
        operation.baseline.get("relationship_config_id"),
        operation.baseline.get("class_config_relationship_id"),
        baseline_object.get("relationship_config_id"),
        baseline_object.get("class_config_relationship_id"),
    )


def _relationship_receiver_semantic_key(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    direct = _first_text(
        operation.current.get("relationship_semantic_key"),
        payload.get("relationship_semantic_key"),
    )
    if direct is not None:
        return direct
    semantic_key = operation.semantic_key
    for marker in ("/association:", "/attribute:"):
        if marker in semantic_key:
            return semantic_key.split(marker, maxsplit=1)[0]
    return semantic_key


def _relationship_association_class_config_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _relationship_association_signature(operation=operation)
    return _first_text(
        operation.current.get("association_class_config_id"),
        operation.current.get("class_config_id"),
        payload.get("association_class_config_id"),
        payload.get("class_config_id"),
        signature.get("association_class_config_id"),
        signature.get("class_config_id"),
    )


def _relationship_association_object_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _relationship_association_signature(operation=operation)
    return _first_text(
        operation.current.get("relationship_association_id"),
        operation.current.get("association_edge_id"),
        operation.current.get("entity_id"),
        payload.get("relationship_association_id"),
        payload.get("association_edge_id"),
        payload.get("entity_id"),
        signature.get("relationship_association_id"),
        signature.get("association_edge_id"),
    )


def _relationship_attribute_config_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _relationship_attribute_signature(operation=operation)
    return _first_text(
        operation.current.get("attribute_config_id"),
        payload.get("attribute_config_id"),
        signature.get("attribute_config_id"),
    )


def _relationship_attribute_direction(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _relationship_attribute_signature(operation=operation)
    return _first_text(
        operation.current.get("direction"),
        payload.get("direction"),
        signature.get("direction"),
    )


def _relationship_attribute_role(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _relationship_attribute_signature(operation=operation)
    return _first_text(
        operation.current.get("role"),
        payload.get("role"),
        signature.get("role"),
    )


def _relationship_attribute_object_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    signature = _relationship_attribute_signature(operation=operation)
    return _first_text(
        operation.current.get("relationship_attribute_id"),
        operation.current.get("relationship_attribute_config_id"),
        operation.current.get("entity_id"),
        payload.get("relationship_attribute_id"),
        payload.get("relationship_attribute_config_id"),
        payload.get("entity_id"),
        signature.get("relationship_attribute_id"),
        signature.get("relationship_attribute_config_id"),
    )


def _provider_operation_type(*, operation: OntologyTypedOperation) -> str | None:
    return optional_text(operation.provider_operation_type)


def _relationship_object_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    return _first_text(
        operation.current.get("relationship_config_id"),
        operation.current.get("class_config_relationship_id"),
        operation.current.get("semantic_source_object_id"),
        payload.get("relationship_config_id"),
        payload.get("class_config_relationship_id"),
        payload.get("semantic_source_object_id"),
        baseline_object.get("relationship_config_id"),
        baseline_object.get("class_config_relationship_id"),
        operation.current.get("entity_id"),
        payload.get("entity_id"),
        operation.baseline.get("object_id"),
        baseline_object.get("object_id"),
    )


def _relationship_delete_object_id(*, operation: OntologyTypedOperation) -> str | None:
    baseline_object = mapping_value(operation.baseline.get("object"))
    return _first_text(
        baseline_object.get("entity_id"),
        baseline_object.get("class_config_relationship_id"),
        operation.baseline.get("entity_id"),
        operation.baseline.get("class_config_relationship_id"),
        operation.baseline.get("object_id"),
        baseline_object.get("object_id"),
        operation.current.get("entity_id"),
    )


def _relationship_update_object_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    return _first_text(
        baseline_object.get("relationship_config_id"),
        baseline_object.get("class_config_relationship_id"),
        baseline_object.get("semantic_source_object_id"),
        operation.baseline.get("relationship_config_id"),
        operation.baseline.get("class_config_relationship_id"),
        operation.current.get("relationship_config_id"),
        operation.current.get("class_config_relationship_id"),
        operation.current.get("semantic_source_object_id"),
        payload.get("relationship_config_id"),
        payload.get("class_config_relationship_id"),
        payload.get("semantic_source_object_id"),
        baseline_object.get("entity_id"),
        baseline_object.get("class_config_relationship_id"),
        operation.baseline.get("entity_id"),
        operation.baseline.get("class_config_relationship_id"),
        operation.current.get("entity_id"),
        payload.get("entity_id"),
        operation.baseline.get("object_id"),
        baseline_object.get("object_id"),
        operation.current.get("object_id"),
        payload.get("object_id"),
    )


def _relationship_identity_update_blockers(
    *,
    operation: OntologyTypedOperation,
) -> tuple[str, ...]:
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_signature = _relationship_baseline_signature(operation=operation)
    current_signature = _relationship_signature(operation=operation)
    current_payload = mapping_value(operation.current.get("payload"))
    baseline_relationship_key = _first_text(
        operation.baseline.get("relationship_key"),
        baseline_object.get("relationship_key"),
        baseline_signature.get("relationship_key"),
        _relationship_key_from_semantic_key(operation.semantic_key),
    )
    current_relationship_key = _first_text(
        operation.current.get("relationship_key"),
        current_payload.get("relationship_key"),
        current_signature.get("relationship_key"),
        _relationship_key_from_semantic_key(operation.semantic_key),
    )
    baseline_target_class_config_id = _first_text(
        operation.baseline.get("target_class_config_id"),
        baseline_object.get("target_class_config_id"),
        baseline_signature.get("target_class_config_id"),
    )
    current_target_class_config_id = _first_text(
        operation.current.get("target_class_config_id"),
        current_payload.get("target_class_config_id"),
        current_signature.get("target_class_config_id"),
    )
    blockers: list[str] = []
    if (
        baseline_relationship_key is not None
        and current_relationship_key is not None
        and baseline_relationship_key != current_relationship_key
    ):
        blockers.append(
            "relationship_identity_change_requires_replacement:relationship_key"
        )
    if (
        baseline_target_class_config_id is not None
        and current_target_class_config_id is not None
        and baseline_target_class_config_id != current_target_class_config_id
    ):
        blockers.append(
            "relationship_identity_change_requires_replacement:"
            "target_class_config_id"
        )
    return tuple(blockers)


def _relationship_source_semantic_key(*, semantic_key: str) -> str | None:
    if "/relationship:" in semantic_key:
        return semantic_key.split("/relationship:", 1)[0]
    graph_key, separator, node_key = semantic_key.partition("/node:")
    if not separator:
        return None
    source_fqn = node_key.split(":", 1)[0].strip()
    if not source_fqn:
        return None
    return f"{graph_key}/node:{source_fqn}"


def _relationship_key_from_semantic_key(value: str) -> str | None:
    if "/relationship:" in value:
        return optional_text(value.rsplit("/relationship:", 1)[-1])
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    parts = node_key.split(":")
    if len(parts) < 4:
        return None
    return optional_text(parts[1])


def _relationship_type_from_semantic_key(value: str) -> str | None:
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    parts = node_key.split(":")
    if len(parts) < 4:
        return None
    return optional_text(parts[2])


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


__all__ = [
    "CLASS_CONFIG_CREATE_RELATIONSHIP_FUNCTION_REF",
    "CLASS_CONFIG_RELATIONSHIP_CREATE_ASSOCIATION_FUNCTION_REF",
    "CLASS_CONFIG_RELATIONSHIP_CREATE_ATTRIBUTE_FUNCTION_REF",
    "CLASS_CONFIG_REMOVE_RELATIONSHIP_CONFIG_FUNCTION_REF",
    "CLASS_CONFIG_RELATIONSHIP_UPDATE_CONFIG_FUNCTION_REF",
    "HANDLER_KEY",
    "plan_relationship_operation",
]
