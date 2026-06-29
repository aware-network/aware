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
from aware_meta.materialization.semantic_function_call_resolution import (
    META_OCG_CREATE_NODE_FUNCTION_REF,
    META_OCG_DELETE_NODE_FUNCTION_REF,
)


HANDLER_KEY = "class.object_config_graph_node_function_calls"
CLASS_CREATE_NODE_INVOCATION_ORDER = 30
CLASS_CREATE_CLASS_INVOCATION_ORDER = 31
CLASS_DELETE_NODE_INVOCATION_ORDER = 30
CLASS_UPDATE_INVOCATION_ORDER = 30
OBJECT_CONFIG_GRAPH_PROJECTION_NAME = "ObjectConfigGraph"
OBJECT_CONFIG_GRAPH_NODE_CREATE_CLASS_FUNCTION_REF = (
    "aware_meta_ontology.graph.config.object_config_graph_node."
    "ObjectConfigGraphNode.create_class"
)
CLASS_CONFIG_UPDATE_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.class_.class_config.ClassConfig.update_config"
)


def plan_class_operation(
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    if operation.ontology_subject_kind != "class":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_ontology_handler_subject_mismatch",
            blockers=(f"unsupported_subject:{operation.ontology_subject_kind}",),
        )
    if operation.operation_family == "create":
        return _plan_class_create_operation(operation=operation, context=context)
    if operation.operation_family == "delete":
        return _plan_class_delete_operation(operation=operation, context=context)
    if operation.operation_family == "update":
        return _plan_class_update_operation(operation=operation)
    return blocked_handler_result(
        operation=operation,
        handler_key=HANDLER_KEY,
        reason="meta_ocg_class_delta_requires_supported_operation",
        blockers=(f"unsupported_operation_family:{operation.operation_family}",),
    )


def _plan_class_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    graph_semantic_key = _class_graph_semantic_key(operation=operation)
    graph_object_id = _graph_receiver_object_id(
        graph_semantic_key=graph_semantic_key,
        context=context,
    )
    node_id = _class_node_id(operation=operation)
    class_config_id = _class_object_id(operation=operation)
    node_key = _class_node_key(operation=operation)
    class_fqn = _class_fqn(operation=operation)
    class_name = _class_name(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("graph_semantic_key", graph_semantic_key),
            ("graph_object_id", graph_object_id),
            ("object_config_graph_node_id", node_id),
            ("class_config_id", class_config_id),
            ("node_key", node_key),
            ("class_fqn", class_fqn),
            ("name", class_name),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_class_create_requires_graph_and_signature",
            blockers=tuple(f"missing_class_create_{field}" for field in missing),
        )

    assert graph_semantic_key is not None
    assert graph_object_id is not None
    assert node_id is not None
    assert class_config_id is not None
    assert node_key is not None
    assert class_fqn is not None
    assert class_name is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_class_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_node",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=CLASS_CREATE_NODE_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="ObjectConfigGraph",
                function_name="create_node",
                function_ref=META_OCG_CREATE_NODE_FUNCTION_REF,
                target_object_id=graph_object_id,
                receiver_semantic_key=graph_semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=node_id,
                kwargs={"type": "class", "node_key": node_key},
                reason="meta_ocg_class_create_node_function_call_ready",
            ),
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_class",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=CLASS_CREATE_CLASS_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="ObjectConfigGraphNode",
                function_name="create_class",
                function_ref=OBJECT_CONFIG_GRAPH_NODE_CREATE_CLASS_FUNCTION_REF,
                target_object_id=node_id,
                receiver_semantic_key=operation.semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=class_config_id,
                kwargs=_class_create_arguments(
                    operation=operation,
                    class_fqn=class_fqn,
                    class_name=class_name,
                ),
                reason="meta_ocg_class_create_class_function_call_ready",
            ),
        ),
    )


def _plan_class_delete_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    graph_semantic_key = _class_graph_semantic_key(operation=operation)
    graph_object_id = _graph_receiver_object_id(
        graph_semantic_key=graph_semantic_key,
        context=context,
    )
    node_id = _class_delete_node_id(operation=operation)
    node_key = _class_node_key(operation=operation)
    blockers = tuple(
        f"missing_class_delete_{field_name}"
        for field_name, value in (
            ("graph_semantic_key", graph_semantic_key),
            ("graph_object_id", graph_object_id),
            ("object_config_graph_node_id", node_id),
            ("node_key", node_key),
        )
        if value is None
    )
    if blockers:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_class_delete_requires_graph_and_identity",
            blockers=blockers,
        )

    assert graph_semantic_key is not None
    assert graph_object_id is not None
    assert node_id is not None
    assert node_key is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_class_delete_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:delete_node",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=CLASS_DELETE_NODE_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="ObjectConfigGraph",
                function_name="delete_node",
                function_ref=META_OCG_DELETE_NODE_FUNCTION_REF,
                target_object_id=graph_object_id,
                receiver_semantic_key=graph_semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=node_id,
                target_projection_name=OBJECT_CONFIG_GRAPH_PROJECTION_NAME,
                result_projection_name=OBJECT_CONFIG_GRAPH_PROJECTION_NAME,
                commit_required=True,
                kwargs={
                    "type": "class",
                    "node_key": node_key,
                    "object_config_graph_node_id": node_id,
                },
                reason="meta_ocg_class_delete_node_function_call_ready",
            ),
        ),
    )


def _plan_class_update_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    class_config_id = _class_update_object_id(operation=operation)
    if class_config_id is None:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_class_update_requires_existing_class_config",
            blockers=("missing_class_update_class_config_id",),
        )
    identity_blockers = _class_update_identity_blockers(operation=operation)
    if identity_blockers:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_class_update_requires_replacement",
            blockers=identity_blockers,
        )
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_class_update_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:update_config",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=CLASS_UPDATE_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="ClassConfig",
                function_name="update_config",
                function_ref=CLASS_CONFIG_UPDATE_CONFIG_FUNCTION_REF,
                target_object_id=class_config_id,
                receiver_semantic_key=operation.semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=class_config_id,
                kwargs=_class_update_arguments(operation=operation),
                reason="meta_ocg_class_update_config_function_call_ready",
            ),
        ),
    )


def _class_create_arguments(
    *,
    operation: OntologyTypedOperation,
    class_fqn: str,
    class_name: str,
) -> dict[str, object]:
    signature = _class_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return {
        "class_fqn": class_fqn,
        "name": class_name,
        "is_base": _bool_value(
            _first_value(
                operation.current.get("is_base"),
                payload.get("is_base"),
                signature.get("is_base"),
                True,
            )
        ),
        "is_edge": _bool_value(
            _first_value(
                operation.current.get("is_edge"),
                payload.get("is_edge"),
                signature.get("is_edge"),
                False,
            )
        ),
        "description": _first_text(
            operation.current.get("description"),
            payload.get("description"),
            signature.get("description"),
        ),
        "value_mode": _first_text(
            operation.current.get("value_mode"),
            payload.get("value_mode"),
            signature.get("value_mode"),
            "graph_ref",
        ),
    }


def _class_update_arguments(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    signature = _class_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return {
        "description": _first_text(
            operation.current.get("description"),
            payload.get("description"),
            signature.get("description"),
        ),
        "is_base": _bool_value(
            _first_value(
                operation.current.get("is_base"),
                payload.get("is_base"),
                signature.get("is_base"),
                True,
            )
        ),
        "is_edge": _bool_value(
            _first_value(
                operation.current.get("is_edge"),
                payload.get("is_edge"),
                signature.get("is_edge"),
                False,
            )
        ),
        "value_mode": _first_text(
            operation.current.get("value_mode"),
            payload.get("value_mode"),
            signature.get("value_mode"),
            "graph_ref",
        ),
        "identity_mode": _first_text(
            operation.current.get("identity_mode"),
            payload.get("identity_mode"),
            signature.get("identity_mode"),
            "contained",
        ),
    }


def _class_update_identity_blockers(
    *,
    operation: OntologyTypedOperation,
) -> tuple[str, ...]:
    blockers: list[str] = []
    baseline_signature = _baseline_class_signature(operation=operation)
    current_signature = _class_signature(operation=operation)
    current_payload = mapping_value(operation.current.get("payload"))
    baseline_payload = mapping_value(operation.baseline.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    for field_name in ("class_fqn", "name"):
        baseline_value = _first_text(
            operation.baseline.get(field_name),
            baseline_payload.get(field_name),
            baseline_object.get(field_name),
            baseline_signature.get(field_name),
        )
        current_value = _first_text(
            operation.current.get(field_name),
            current_payload.get(field_name),
            current_signature.get(field_name),
        )
        if (
            baseline_value is not None
            and current_value is not None
            and baseline_value != current_value
        ):
            blockers.append(
                f"class_identity_change_requires_replacement:{field_name}"
            )
    return tuple(blockers)


def _graph_receiver_object_id(
    *,
    graph_semantic_key: str | None,
    context: OntologyExecutionPlanningContext,
) -> str | None:
    if graph_semantic_key is None:
        return None
    graph_operation = context.operation_by_semantic_key.get(graph_semantic_key)
    if graph_operation is None:
        return None
    graph_payload = mapping_value(graph_operation.current.get("payload"))
    graph_baseline_object = mapping_value(graph_operation.baseline.get("object"))
    return _first_text(
        graph_operation.current.get("entity_id"),
        graph_payload.get("entity_id"),
        graph_operation.current.get("object_id"),
        graph_payload.get("object_id"),
        graph_operation.baseline.get("object_id"),
        graph_baseline_object.get("object_id"),
        graph_baseline_object.get("entity_id"),
    )


def _class_graph_semantic_key(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("graph_semantic_key"),
        payload.get("graph_semantic_key"),
        _graph_semantic_key_from_class_semantic_key(operation.semantic_key),
    )


def _class_node_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("node_id"),
        payload.get("node_id"),
        operation.current.get("object_config_graph_node_id"),
        payload.get("object_config_graph_node_id"),
    )


def _class_delete_node_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        operation.current.get("object_config_graph_node_id"),
        operation.current.get("node_id"),
        payload.get("object_config_graph_node_id"),
        payload.get("node_id"),
        baseline_object.get("object_config_graph_node_id"),
        baseline_object.get("node_id"),
        baseline_payload.get("object_config_graph_node_id"),
        baseline_payload.get("node_id"),
    )


def _class_object_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("entity_id"),
        payload.get("entity_id"),
        operation.current.get("class_config_id"),
        payload.get("class_config_id"),
    )


def _class_update_object_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        operation.current.get("entity_id"),
        payload.get("entity_id"),
        operation.current.get("class_config_id"),
        payload.get("class_config_id"),
        baseline_object.get("entity_id"),
        baseline_payload.get("entity_id"),
        baseline_object.get("class_config_id"),
        baseline_payload.get("class_config_id"),
        operation.baseline.get("entity_id"),
        operation.baseline.get("class_config_id"),
    )


def _class_node_key(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("node_key"),
        payload.get("node_key"),
        _class_node_key_from_semantic_key(operation.semantic_key),
    )


def _class_fqn(*, operation: OntologyTypedOperation) -> str | None:
    signature = _class_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("class_fqn"),
        payload.get("class_fqn"),
        signature.get("class_fqn"),
        _class_node_key(operation=operation),
    )


def _class_name(*, operation: OntologyTypedOperation) -> str | None:
    signature = _class_signature(operation=operation)
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("entity_name"),
        operation.current.get("name"),
        payload.get("entity_name"),
        payload.get("name"),
        signature.get("name"),
        _class_name_from_node_key(_class_node_key(operation=operation)),
    )


def _class_signature(*, operation: OntologyTypedOperation) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    return mapping_value(
        operation.current.get("class_signature")
        or payload.get("class_signature")
    )


def _baseline_class_signature(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    payload = mapping_value(operation.baseline.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    return mapping_value(
        operation.baseline.get("class_signature")
        or payload.get("class_signature")
        or baseline_object.get("class_signature")
    )


def _graph_semantic_key_from_class_semantic_key(value: str) -> str | None:
    graph_key, separator, _ = value.partition("/node:")
    if not separator:
        return None
    return optional_text(graph_key)


def _class_node_key_from_semantic_key(value: str) -> str | None:
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    return optional_text(node_key.split("/", 1)[0])


def _class_name_from_node_key(value: str | None) -> str | None:
    if value is None:
        return None
    return optional_text(value.rsplit(".", 1)[-1])


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
    "CLASS_CONFIG_UPDATE_CONFIG_FUNCTION_REF",
    "HANDLER_KEY",
    "OBJECT_CONFIG_GRAPH_NODE_CREATE_CLASS_FUNCTION_REF",
    "OBJECT_CONFIG_GRAPH_PROJECTION_NAME",
    "plan_class_operation",
]
