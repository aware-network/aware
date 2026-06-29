from __future__ import annotations

from aware_meta.graph.projection.deltas.typed_operations import (
    OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND,
    OBJECT_PROJECTION_GRAPH_SUBJECT_KIND,
)
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


HANDLER_KEY = "object_projection_graph.function_calls"
OPG_CREATE_ROOT_INVOCATION_ORDER = 50
OPG_CREATE_NODE_INVOCATION_ORDER = 51
OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION_REF = (
    "aware_meta_ontology.graph.projection.object_projection_graph."
    "ObjectProjectionGraph.build_via_object_config_graph"
)
OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION_REF = (
    "aware_meta_ontology.graph.projection.object_projection_graph."
    "ObjectProjectionGraph.create_node"
)


def plan_object_projection_graph_operation(
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    if operation.ontology_subject_kind == OBJECT_PROJECTION_GRAPH_SUBJECT_KIND:
        if operation.operation_family == "create":
            return _plan_opg_create_operation(
                operation=operation,
                context=context,
            )
        return _unsupported_family(operation=operation)
    if operation.ontology_subject_kind == OBJECT_PROJECTION_GRAPH_NODE_SUBJECT_KIND:
        if operation.operation_family == "create":
            return _plan_opg_node_create_operation(
                operation=operation,
                context=context,
            )
        return _unsupported_family(operation=operation)
    return blocked_handler_result(
        operation=operation,
        handler_key=HANDLER_KEY,
        reason="meta_opg_ontology_handler_subject_mismatch",
        blockers=(f"unsupported_subject:{operation.ontology_subject_kind}",),
    )


def _plan_opg_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    graph_semantic_key = _graph_semantic_key(operation=operation)
    graph_object_id = _graph_receiver_object_id(
        graph_semantic_key=graph_semantic_key,
        operation=operation,
        context=context,
    )
    opg_id = _opg_id(operation=operation)
    name = _opg_name(operation=operation)
    projection_hash = _opg_projection_hash(operation=operation)
    language = _opg_language(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("graph_semantic_key", graph_semantic_key),
            ("graph_object_id", graph_object_id),
            ("object_projection_graph_id", opg_id),
            ("name", name),
            ("projection_hash", projection_hash),
            ("language", language),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_opg_create_requires_graph_and_signature",
            blockers=tuple(f"missing_opg_create_{field}" for field in missing),
        )

    assert graph_semantic_key is not None
    assert graph_object_id is not None
    assert opg_id is not None
    assert name is not None
    assert projection_hash is not None
    assert language is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_opg_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:build_via_object_config_graph",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=OPG_CREATE_ROOT_INVOCATION_ORDER,
                invocation_mode="constructor",
                owner_class_name="ObjectProjectionGraph",
                function_name="build_via_object_config_graph",
                function_ref=OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION_REF,
                target_object_id=None,
                receiver_semantic_key=graph_semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=opg_id,
                result_projection_name="ObjectProjectionGraph",
                lane_state_role="created_in_plan",
                commit_required=True,
                kwargs={
                    "object_config_graph_id": graph_object_id,
                    "name": name,
                    "projection_hash": projection_hash,
                    "language": language,
                    "description": _opg_description(operation=operation),
                    "supports_virtual_build": _opg_supports_virtual_build(
                        operation=operation,
                    ),
                },
                reason="meta_opg_create_function_call_ready",
            ),
        ),
    )


def _plan_opg_node_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    opg_semantic_key = _opg_semantic_key(operation=operation)
    opg_object_id = _opg_receiver_object_id(
        opg_semantic_key=opg_semantic_key,
        operation=operation,
        context=context,
    )
    node_id = _opg_node_id(operation=operation)
    class_config_id = _opg_node_class_config_id(operation=operation)
    selection = _opg_node_selection(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("object_projection_graph_semantic_key", opg_semantic_key),
            ("object_projection_graph_id", opg_object_id),
            ("object_projection_graph_node_id", node_id),
            ("class_config_id", class_config_id),
            ("selection", selection),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_opg_node_create_requires_projection_and_class",
            blockers=tuple(
                f"missing_opg_node_create_{field}" for field in missing
            ),
        )

    assert opg_semantic_key is not None
    assert opg_object_id is not None
    assert node_id is not None
    assert class_config_id is not None
    assert selection is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_opg_node_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_node",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=OPG_CREATE_NODE_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="ObjectProjectionGraph",
                function_name="create_node",
                function_ref=OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION_REF,
                target_object_id=opg_object_id,
                receiver_semantic_key=opg_semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=node_id,
                target_projection_name="ObjectProjectionGraph",
                lane_state_role="created_in_plan_member",
                commit_required=True,
                kwargs={
                    "class_config_id": class_config_id,
                    "is_root": _opg_node_is_root(operation=operation),
                    "required_for_validity": (
                        _opg_node_required_for_validity(operation=operation)
                    ),
                    "selection": selection,
                    "top_n": _opg_node_top_n(operation=operation),
                    "selector_condition_id": (
                        _opg_node_selector_condition_id(operation=operation)
                    ),
                    "policy_refs": list(_opg_node_policy_refs(operation=operation)),
                },
                reason="meta_opg_node_create_function_call_ready",
            ),
        ),
    )


def _unsupported_family(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    return blocked_handler_result(
        operation=operation,
        handler_key=HANDLER_KEY,
        reason="meta_opg_delta_requires_create_operation",
        blockers=(f"unsupported_operation_family:{operation.operation_family}",),
    )


def _graph_receiver_object_id(
    *,
    graph_semantic_key: str | None,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> str | None:
    if graph_semantic_key is not None:
        graph_operation = context.operation_by_semantic_key.get(graph_semantic_key)
        if graph_operation is not None:
            graph_payload = mapping_value(graph_operation.current.get("payload"))
            return _first_text(
                graph_operation.current.get("entity_id"),
                graph_payload.get("entity_id"),
                graph_operation.current.get("object_id"),
                graph_payload.get("object_id"),
            )
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("object_config_graph_id"),
        payload.get("object_config_graph_id"),
    )


def _opg_receiver_object_id(
    *,
    opg_semantic_key: str | None,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> str | None:
    if opg_semantic_key is not None:
        opg_operation = context.operation_by_semantic_key.get(opg_semantic_key)
        if opg_operation is not None:
            opg_payload = mapping_value(opg_operation.current.get("payload"))
            return _first_text(
                opg_operation.current.get("entity_id"),
                opg_payload.get("entity_id"),
                opg_operation.current.get("object_projection_graph_id"),
                opg_payload.get("object_projection_graph_id"),
            )
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("object_projection_graph_id"),
        payload.get("object_projection_graph_id"),
    )


def _graph_semantic_key(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("graph_semantic_key"),
        payload.get("graph_semantic_key"),
        _graph_semantic_key_from_opg_semantic_key(operation.semantic_key),
    )


def _opg_semantic_key(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("object_projection_graph_semantic_key"),
        payload.get("object_projection_graph_semantic_key"),
        _opg_semantic_key_from_node_semantic_key(operation.semantic_key),
    )


def _opg_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("entity_id"),
        payload.get("entity_id"),
        operation.current.get("object_projection_graph_id"),
        payload.get("object_projection_graph_id"),
    )


def _opg_node_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("entity_id"),
        payload.get("entity_id"),
        operation.current.get("object_projection_graph_node_id"),
        payload.get("object_projection_graph_node_id"),
    )


def _opg_node_class_config_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("class_config_id"),
        payload.get("class_config_id"),
    )


def _opg_name(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(operation.current.get("name"), payload.get("name"))


def _opg_projection_hash(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("projection_hash"),
        payload.get("projection_hash"),
        "",
    )


def _opg_language(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("language"),
        payload.get("language"),
        "aware",
    )


def _opg_description(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("description"),
        payload.get("description"),
    )


def _opg_supports_virtual_build(*, operation: OntologyTypedOperation) -> bool:
    payload = mapping_value(operation.current.get("payload"))
    return _bool_value(
        _first_value(
            operation.current.get("supports_virtual_build"),
            payload.get("supports_virtual_build"),
            True,
        )
    )


def _opg_node_is_root(*, operation: OntologyTypedOperation) -> bool:
    payload = mapping_value(operation.current.get("payload"))
    return _bool_value(
        _first_value(operation.current.get("is_root"), payload.get("is_root"), False)
    )


def _opg_node_required_for_validity(*, operation: OntologyTypedOperation) -> bool:
    payload = mapping_value(operation.current.get("payload"))
    return _bool_value(
        _first_value(
            operation.current.get("required_for_validity"),
            payload.get("required_for_validity"),
            False,
        )
    )


def _opg_node_selection(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("selection"),
        payload.get("selection"),
        "all",
    )


def _opg_node_top_n(*, operation: OntologyTypedOperation) -> int | None:
    payload = mapping_value(operation.current.get("payload"))
    value = _first_value(operation.current.get("top_n"), payload.get("top_n"))
    if isinstance(value, int):
        return value
    text = optional_text(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _opg_node_selector_condition_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("selector_condition_id"),
        payload.get("selector_condition_id"),
    )


def _opg_node_policy_refs(
    *,
    operation: OntologyTypedOperation,
) -> tuple[str, ...]:
    payload = mapping_value(operation.current.get("payload"))
    value = _first_value(operation.current.get("policy_refs"), payload.get("policy_refs"))
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        text
        for text in (optional_text(item) for item in value)
        if text is not None
    )


def _graph_semantic_key_from_opg_semantic_key(value: str) -> str | None:
    graph_key, separator, _ = value.partition("/projection:")
    if not separator:
        return None
    return optional_text(graph_key)


def _opg_semantic_key_from_node_semantic_key(value: str) -> str | None:
    opg_key, separator, _ = value.partition("/node:")
    if not separator:
        return None
    return optional_text(opg_key)


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
    "HANDLER_KEY",
    "OBJECT_PROJECTION_GRAPH_BUILD_FUNCTION_REF",
    "OBJECT_PROJECTION_GRAPH_CREATE_NODE_FUNCTION_REF",
    "OPG_CREATE_NODE_INVOCATION_ORDER",
    "OPG_CREATE_ROOT_INVOCATION_ORDER",
    "plan_object_projection_graph_operation",
]
