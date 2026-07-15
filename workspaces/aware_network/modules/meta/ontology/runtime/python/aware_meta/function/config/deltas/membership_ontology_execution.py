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
)


HANDLER_KEY = "function_membership.class_config_function_config_calls"
CLASS_CONFIG_FUNCTION_CONFIG_UPDATE_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.class_.class_config_function_config."
    "ClassConfigFunctionConfig.update_config"
)


def plan_function_membership_operation(
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    del context
    if operation.ontology_subject_kind != "function_membership":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_ontology_handler_subject_mismatch",
            blockers=(f"unsupported_subject:{operation.ontology_subject_kind}",),
        )
    if operation.operation_family != "update":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_function_membership_delta_requires_update_operation",
            blockers=(f"unsupported_operation_family:{operation.operation_family}",),
        )
    return _plan_function_membership_update_operation(operation=operation)


def _plan_function_membership_update_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    edge_id = _function_membership_update_object_id(operation=operation)
    blockers = (
        ("missing_function_membership_update_edge_id",)
        if edge_id is None
        else ()
    )
    blockers += _function_membership_identity_update_blockers(operation=operation)
    if blockers:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason=(
                "meta_ocg_function_membership_update_requires_existing_edge"
            ),
            blockers=blockers,
        )

    assert edge_id is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_function_membership_update_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:update_function_membership",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=0,
                invocation_mode="instance",
                owner_class_name="ClassConfigFunctionConfig",
                function_name="update_config",
                function_ref=(
                    CLASS_CONFIG_FUNCTION_CONFIG_UPDATE_CONFIG_FUNCTION_REF
                ),
                target_object_id=edge_id,
                receiver_semantic_key=operation.semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=edge_id,
                kwargs=_function_membership_update_arguments(
                    operation=operation,
                ),
                reason=(
                    "meta_ocg_function_membership_update_mutable_config_ready"
                ),
            ),
        ),
    )


def _function_membership_update_arguments(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    signature = _function_membership_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return {
        "is_public": _bool_value(
            _first_value(
                operation.current.get("is_public"),
                payload.get("is_public"),
                signature.get("is_public"),
                True,
            )
        ),
        "is_constructor": _bool_value(
            _first_value(
                operation.current.get("is_constructor"),
                payload.get("is_constructor"),
                signature.get("is_constructor"),
                False,
            )
        ),
        "position": _int_value(
            _first_value(
                operation.current.get("position"),
                payload.get("position"),
                signature.get("position"),
                0,
            )
        ),
    }


def _function_membership_update_object_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    return _first_text(
        operation.baseline.get("object_id"),
        baseline_object.get("object_id"),
        baseline_object.get("class_config_function_config_id"),
        operation.current.get("object_id"),
        operation.current.get("class_config_function_config_id"),
        operation.current.get("entity_id"),
        payload.get("object_id"),
        payload.get("class_config_function_config_id"),
        payload.get("entity_id"),
    )


def _function_membership_identity_update_blockers(
    *,
    operation: OntologyTypedOperation,
) -> tuple[str, ...]:
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_signature = _function_membership_baseline_signature(
        operation=operation,
    )
    current_signature = _function_membership_signature(operation=operation)
    current_payload = mapping_value(operation.current.get("payload"))
    baseline_class_config_id = _first_text(
        operation.baseline.get("class_config_id"),
        baseline_object.get("class_config_id"),
        baseline_signature.get("class_config_id"),
    )
    current_class_config_id = _first_text(
        operation.current.get("class_config_id"),
        current_payload.get("class_config_id"),
        current_signature.get("class_config_id"),
    )
    baseline_function_config_id = _first_text(
        operation.baseline.get("function_config_id"),
        baseline_object.get("function_config_id"),
        baseline_signature.get("function_config_id"),
    )
    current_function_config_id = _first_text(
        operation.current.get("function_config_id"),
        current_payload.get("function_config_id"),
        current_signature.get("function_config_id"),
    )

    blockers: list[str] = []
    if (
        baseline_class_config_id is not None
        and current_class_config_id is not None
        and baseline_class_config_id != current_class_config_id
    ):
        blockers.append(
            "function_membership_identity_change_requires_replacement:"
            "class_config_id"
        )
    if (
        baseline_function_config_id is not None
        and current_function_config_id is not None
        and baseline_function_config_id != current_function_config_id
    ):
        blockers.append(
            "function_membership_identity_change_requires_replacement:"
            "function_config_id"
        )
    return tuple(blockers)


def _function_membership_signature(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    return mapping_value(
        operation.current.get("function_membership_signature")
        or payload.get("function_membership_signature")
    )


def _function_membership_baseline_signature(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    baseline_object = mapping_value(operation.baseline.get("object"))
    return mapping_value(
        operation.baseline.get("function_membership_signature")
        or baseline_object.get("function_membership_signature")
    )


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
