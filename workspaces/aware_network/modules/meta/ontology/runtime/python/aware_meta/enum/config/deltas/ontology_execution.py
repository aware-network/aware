from __future__ import annotations

from uuid import UUID

from aware_meta.graph.config.stable_ids import (
    stable_enum_config_id,
    stable_object_config_graph_node_id,
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
from aware_meta.materialization.semantic_function_call_resolution import (
    META_OCG_CREATE_NODE_FUNCTION_REF,
    META_OCG_DELETE_NODE_FUNCTION_REF,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)


HANDLER_KEY = "enum.object_config_graph_node_function_calls"
ENUM_CREATE_NODE_INVOCATION_ORDER = 30
ENUM_CREATE_ENUM_INVOCATION_ORDER = 31
ENUM_DELETE_NODE_INVOCATION_ORDER = 30
ENUM_UPDATE_INVOCATION_ORDER = 30
ENUM_OPTION_CREATE_INVOCATION_ORDER = 40
ENUM_OPTION_UPDATE_INVOCATION_ORDER = 40
ENUM_OPTION_DELETE_INVOCATION_ORDER = 40
OBJECT_CONFIG_GRAPH_PROJECTION_NAME = "ObjectConfigGraph"
OBJECT_CONFIG_GRAPH_NODE_CREATE_ENUM_FUNCTION_REF = (
    "aware_meta_ontology.graph.config.object_config_graph_node."
    "ObjectConfigGraphNode.create_enum"
)
ENUM_CONFIG_UPDATE_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.enum.enum_config.EnumConfig.update_config"
)
ENUM_CONFIG_CREATE_ENUM_OPTION_FUNCTION_REF = (
    "aware_meta_ontology.enum.enum_config.EnumConfig.create_enum_option"
)
ENUM_CONFIG_DELETE_ENUM_OPTION_FUNCTION_REF = (
    "aware_meta_ontology.enum.enum_config.EnumConfig.delete_enum_option"
)
ENUM_OPTION_UPDATE_CONFIG_FUNCTION_REF = (
    "aware_meta_ontology.enum.enum_option.EnumOption.update_config"
)


def plan_enum_operation(
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    if operation.ontology_subject_kind == "enum_option":
        return _plan_enum_option_operation(operation=operation)
    if operation.ontology_subject_kind != "enum":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_ontology_handler_subject_mismatch",
            blockers=(f"unsupported_subject:{operation.ontology_subject_kind}",),
        )
    if operation.operation_family == "create":
        return _plan_enum_create_operation(operation=operation, context=context)
    if operation.operation_family == "update":
        return _plan_enum_update_operation(operation=operation)
    if operation.operation_family == "delete":
        return _plan_enum_delete_operation(operation=operation, context=context)
    return blocked_handler_result(
        operation=operation,
        handler_key=HANDLER_KEY,
        reason="meta_ocg_enum_delta_requires_supported_operation",
        blockers=(f"unsupported_operation_family:{operation.operation_family}",),
    )


def _plan_enum_option_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    if operation.operation_family == "create":
        return _plan_enum_option_create_operation(operation=operation)
    if operation.operation_family == "update":
        return _plan_enum_option_update_operation(operation=operation)
    if operation.operation_family == "delete":
        return _plan_enum_option_delete_operation(operation=operation)
    return blocked_handler_result(
        operation=operation,
        handler_key=HANDLER_KEY,
        reason="meta_ocg_enum_option_delta_requires_supported_operation",
        blockers=(f"unsupported_operation_family:{operation.operation_family}",),
    )


def _plan_enum_create_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    graph_semantic_key = _enum_graph_semantic_key(operation=operation)
    graph_object_id = _graph_receiver_object_id(
        graph_semantic_key=graph_semantic_key,
        context=context,
    )
    node_key = _enum_node_key(operation=operation)
    enum_fqn = _enum_fqn(operation=operation)
    enum_name = _enum_name(operation=operation)
    node_id = _first_text(
        _enum_node_id(operation=operation),
        _derived_enum_node_id(
            graph_object_id=graph_object_id,
            node_key=node_key,
        ),
    )
    enum_config_id = _first_text(
        _enum_object_id(operation=operation),
        _derived_enum_config_id(
            node_id=node_id,
            enum_fqn=enum_fqn,
        ),
    )
    missing = tuple(
        field_name
        for field_name, value in (
            ("graph_semantic_key", graph_semantic_key),
            ("graph_object_id", graph_object_id),
            ("object_config_graph_node_id", node_id),
            ("enum_config_id", enum_config_id),
            ("node_key", node_key),
            ("enum_fqn", enum_fqn),
            ("name", enum_name),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_enum_create_requires_graph_and_signature",
            blockers=tuple(f"missing_enum_create_{field}" for field in missing),
        )

    assert graph_semantic_key is not None
    assert graph_object_id is not None
    assert node_id is not None
    assert enum_config_id is not None
    assert node_key is not None
    assert enum_fqn is not None
    assert enum_name is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_enum_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_node",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=ENUM_CREATE_NODE_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="ObjectConfigGraph",
                function_name="create_node",
                function_ref=META_OCG_CREATE_NODE_FUNCTION_REF,
                target_object_id=graph_object_id,
                receiver_semantic_key=graph_semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=node_id,
                target_projection_name=OBJECT_CONFIG_GRAPH_PROJECTION_NAME,
                result_projection_name=OBJECT_CONFIG_GRAPH_PROJECTION_NAME,
                kwargs={"type": "enum", "node_key": node_key},
                reason="meta_ocg_enum_create_node_function_call_ready",
            ),
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_enum",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=ENUM_CREATE_ENUM_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="ObjectConfigGraphNode",
                function_name="create_enum",
                function_ref=OBJECT_CONFIG_GRAPH_NODE_CREATE_ENUM_FUNCTION_REF,
                target_object_id=node_id,
                receiver_semantic_key=operation.semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=enum_config_id,
                target_projection_name=OBJECT_CONFIG_GRAPH_PROJECTION_NAME,
                result_projection_name=OBJECT_CONFIG_GRAPH_PROJECTION_NAME,
                kwargs=_enum_create_arguments(
                    operation=operation,
                    enum_fqn=enum_fqn,
                    enum_name=enum_name,
                ),
                reason="meta_ocg_enum_create_enum_function_call_ready",
            ),
        ),
    )


def _plan_enum_update_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    enum_config_id = _enum_update_object_id(operation=operation)
    identity_blockers = _enum_update_identity_blockers(operation=operation)
    blockers = ("missing_enum_update_enum_config_id",) if enum_config_id is None else ()
    blockers += identity_blockers
    if blockers:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_enum_update_requires_existing_enum_config",
            blockers=blockers,
        )
    assert enum_config_id is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_enum_update_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:update_config",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=ENUM_UPDATE_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="EnumConfig",
                function_name="update_config",
                function_ref=ENUM_CONFIG_UPDATE_CONFIG_FUNCTION_REF,
                target_object_id=enum_config_id,
                receiver_semantic_key=operation.semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=enum_config_id,
                target_projection_name=OBJECT_CONFIG_GRAPH_PROJECTION_NAME,
                kwargs=_enum_update_arguments(operation=operation),
                reason="meta_ocg_enum_update_config_function_call_ready",
            ),
        ),
    )


def _plan_enum_delete_operation(
    *,
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    graph_semantic_key = _enum_graph_semantic_key(operation=operation)
    graph_object_id = _graph_receiver_object_id(
        graph_semantic_key=graph_semantic_key,
        context=context,
    )
    node_id = _enum_delete_node_id(operation=operation)
    node_key = _enum_node_key(operation=operation)
    blockers = tuple(
        f"missing_enum_delete_{field_name}"
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
            reason="meta_ocg_enum_delete_requires_graph_and_identity",
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
        reason="meta_ocg_enum_delete_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:delete_node",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=ENUM_DELETE_NODE_INVOCATION_ORDER,
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
                    "type": "enum",
                    "node_key": node_key,
                    "object_config_graph_node_id": node_id,
                },
                reason="meta_ocg_enum_delete_node_function_call_ready",
            ),
        ),
    )


def _plan_enum_option_create_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    enum_config_id = _enum_option_enum_config_id(operation=operation)
    enum_option_id = _enum_option_object_id(operation=operation)
    value = _enum_option_value(operation=operation)
    missing = tuple(
        field_name
        for field_name, field_value in (
            ("enum_config_id", enum_config_id),
            ("enum_option_id", enum_option_id),
            ("value", value),
        )
        if field_value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_enum_option_create_requires_parent_and_signature",
            blockers=tuple(f"missing_enum_option_create_{field}" for field in missing),
        )
    assert enum_config_id is not None
    assert enum_option_id is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_enum_option_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:create_enum_option",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=ENUM_OPTION_CREATE_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="EnumConfig",
                function_name="create_enum_option",
                function_ref=ENUM_CONFIG_CREATE_ENUM_OPTION_FUNCTION_REF,
                target_object_id=enum_config_id,
                receiver_semantic_key=_enum_option_parent_semantic_key(
                    operation=operation,
                ),
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=enum_option_id,
                target_projection_name=OBJECT_CONFIG_GRAPH_PROJECTION_NAME,
                result_projection_name=OBJECT_CONFIG_GRAPH_PROJECTION_NAME,
                kwargs=_enum_option_create_arguments(operation=operation),
                reason="meta_ocg_enum_option_create_function_call_ready",
            ),
        ),
    )


def _plan_enum_option_update_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    enum_option_id = _enum_option_update_object_id(operation=operation)
    identity_blockers = _enum_option_update_identity_blockers(operation=operation)
    blockers = (
        ("missing_enum_option_update_enum_option_id",) if enum_option_id is None else ()
    )
    blockers += identity_blockers
    if blockers:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_enum_option_update_requires_existing_enum_option",
            blockers=blockers,
        )
    assert enum_option_id is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_enum_option_update_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:update_config",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=ENUM_OPTION_UPDATE_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="EnumOption",
                function_name="update_config",
                function_ref=ENUM_OPTION_UPDATE_CONFIG_FUNCTION_REF,
                target_object_id=enum_option_id,
                receiver_semantic_key=operation.semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=enum_option_id,
                target_projection_name=OBJECT_CONFIG_GRAPH_PROJECTION_NAME,
                kwargs=_enum_option_update_arguments(operation=operation),
                reason="meta_ocg_enum_option_update_config_function_call_ready",
            ),
        ),
    )


def _plan_enum_option_delete_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    enum_config_id = _enum_option_enum_config_id(operation=operation)
    enum_option_id = _enum_option_delete_source_object_id(operation=operation)
    value = _enum_option_value(operation=operation)
    missing = tuple(
        field_name
        for field_name, field_value in (
            ("enum_config_id", enum_config_id),
            ("enum_option_id", enum_option_id),
            ("value", value),
        )
        if field_value is None
    )
    identity_blockers = _enum_option_update_identity_blockers(operation=operation)
    blockers = tuple(f"missing_enum_option_delete_{field}" for field in missing)
    blockers += identity_blockers
    if blockers:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_enum_option_delete_requires_parent_and_identity",
            blockers=blockers,
        )
    assert enum_config_id is not None
    assert enum_option_id is not None
    assert value is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_enum_option_delete_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:delete_enum_option",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=ENUM_OPTION_DELETE_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="EnumConfig",
                function_name="delete_enum_option",
                function_ref=ENUM_CONFIG_DELETE_ENUM_OPTION_FUNCTION_REF,
                target_object_id=enum_config_id,
                receiver_semantic_key=_enum_option_parent_semantic_key(
                    operation=operation,
                ),
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=enum_option_id,
                target_projection_name=OBJECT_CONFIG_GRAPH_PROJECTION_NAME,
                commit_required=True,
                kwargs=_enum_option_delete_arguments(
                    operation=operation,
                    enum_option_id=enum_option_id,
                    value=value,
                ),
                reason="meta_ocg_enum_option_delete_function_call_ready",
            ),
        ),
    )


def _enum_create_arguments(
    *,
    operation: OntologyTypedOperation,
    enum_fqn: str,
    enum_name: str,
) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    return {
        "enum_fqn": enum_fqn,
        "name": enum_name,
        "description": _first_text(
            operation.current.get("description"),
            payload.get("description"),
        ),
        "values": list(
            _tuple_text(
                _first_value(
                    operation.current.get("values"),
                    payload.get("values"),
                    (),
                )
            )
        ),
    }


def _enum_update_arguments(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    return {
        "description": _first_text(
            operation.current.get("description"),
            payload.get("description"),
        ),
    }


def _enum_option_create_arguments(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    return {
        "value": _enum_option_value(operation=operation),
        "label": _first_text(operation.current.get("label"), payload.get("label")),
        "description": _first_text(
            operation.current.get("description"),
            payload.get("description"),
        ),
        "position": _int_value(
            _first_value(operation.current.get("position"), payload.get("position"), 0)
        ),
    }


def _enum_option_update_arguments(
    *,
    operation: OntologyTypedOperation,
) -> dict[str, object]:
    payload = mapping_value(operation.current.get("payload"))
    return {
        "label": _first_text(operation.current.get("label"), payload.get("label")),
        "description": _first_text(
            operation.current.get("description"),
            payload.get("description"),
        ),
        "position": _int_value(
            _first_value(operation.current.get("position"), payload.get("position"), 0)
        ),
    }


def _enum_option_delete_arguments(
    *,
    operation: OntologyTypedOperation,
    enum_option_id: str,
    value: str,
) -> dict[str, object]:
    return {
        "value": value,
        "enum_option_id": enum_option_id,
    }


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


def _derived_enum_node_id(
    *,
    graph_object_id: str | None,
    node_key: str | None,
) -> str | None:
    if graph_object_id is None or node_key is None:
        return None
    try:
        return str(
            stable_object_config_graph_node_id(
                object_config_graph_id=UUID(graph_object_id),
                type=ObjectConfigGraphNodeType.enum.value,
                node_key=node_key,
            )
        )
    except (TypeError, ValueError):
        return None


def _derived_enum_config_id(
    *,
    node_id: str | None,
    enum_fqn: str | None,
) -> str | None:
    if node_id is None or enum_fqn is None:
        return None
    try:
        return str(
            stable_enum_config_id(
                object_config_graph_node_id=UUID(node_id),
                enum_fqn=enum_fqn,
            )
        )
    except (TypeError, ValueError):
        return None


def _enum_update_object_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        operation.current.get("enum_config_id"),
        operation.current.get("entity_id"),
        payload.get("enum_config_id"),
        payload.get("entity_id"),
        operation.baseline.get("object_id"),
        baseline_object.get("enum_config_id"),
        baseline_object.get("entity_id"),
        baseline_payload.get("enum_config_id"),
        baseline_payload.get("entity_id"),
    )


def _enum_update_identity_blockers(
    *,
    operation: OntologyTypedOperation,
) -> tuple[str, ...]:
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    payload = mapping_value(operation.current.get("payload"))
    blockers: list[str] = []
    baseline_enum_fqn = _first_text(
        baseline_object.get("enum_fqn"),
        baseline_payload.get("enum_fqn"),
    )
    current_enum_fqn = _first_text(
        operation.current.get("enum_fqn"),
        payload.get("enum_fqn"),
    )
    if (
        baseline_enum_fqn is not None
        and current_enum_fqn is not None
        and baseline_enum_fqn != current_enum_fqn
    ):
        blockers.append("enum_update_enum_fqn_identity_changed")
    baseline_name = _first_text(
        baseline_object.get("name"),
        baseline_object.get("entity_name"),
        baseline_payload.get("name"),
        baseline_payload.get("entity_name"),
    )
    current_name = _first_text(
        operation.current.get("name"),
        operation.current.get("entity_name"),
        payload.get("name"),
        payload.get("entity_name"),
    )
    if (
        baseline_name is not None
        and current_name is not None
        and baseline_name != current_name
    ):
        blockers.append("enum_update_name_identity_changed")
    return tuple(blockers)


def _enum_graph_semantic_key(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        operation.current.get("graph_semantic_key"),
        payload.get("graph_semantic_key"),
        baseline_object.get("graph_semantic_key"),
        baseline_payload.get("graph_semantic_key"),
        _graph_semantic_key_from_enum_semantic_key(operation.semantic_key),
    )


def _enum_node_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        operation.current.get("node_id"),
        payload.get("node_id"),
        operation.current.get("object_config_graph_node_id"),
        payload.get("object_config_graph_node_id"),
        baseline_object.get("node_id"),
        baseline_payload.get("node_id"),
        baseline_object.get("object_config_graph_node_id"),
        baseline_payload.get("object_config_graph_node_id"),
    )


def _enum_delete_node_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        baseline_object.get("object_config_graph_node_id"),
        baseline_object.get("node_id"),
        baseline_payload.get("object_config_graph_node_id"),
        baseline_payload.get("node_id"),
        operation.baseline.get("semantic_source_object_id"),
        baseline_object.get("semantic_source_object_id"),
        baseline_payload.get("semantic_source_object_id"),
        operation.current.get("object_config_graph_node_id"),
        operation.current.get("node_id"),
        payload.get("object_config_graph_node_id"),
        payload.get("node_id"),
        _enum_node_id(operation=operation),
    )


def _enum_object_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("entity_id"),
        payload.get("entity_id"),
        operation.current.get("enum_config_id"),
        payload.get("enum_config_id"),
    )


def _enum_option_enum_config_id(*, operation: OntologyTypedOperation) -> str | None:
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
        operation.current.get("enum_config_id"),
        payload.get("enum_config_id"),
        baseline_object.get("enum_config_id"),
        baseline_payload.get("enum_config_id"),
    )


def _enum_option_object_id(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("enum_option_id"),
        operation.current.get("entity_id"),
        payload.get("enum_option_id"),
        payload.get("entity_id"),
    )


def _enum_option_update_object_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        _enum_option_object_id(operation=operation),
        operation.baseline.get("object_id"),
        baseline_object.get("enum_option_id"),
        baseline_object.get("entity_id"),
        baseline_payload.get("enum_option_id"),
        baseline_payload.get("entity_id"),
    )


def _enum_option_delete_source_object_id(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        baseline_object.get("enum_option_id"),
        baseline_object.get("entity_id"),
        baseline_payload.get("enum_option_id"),
        baseline_payload.get("entity_id"),
        operation.baseline.get("semantic_source_object_id"),
        baseline_object.get("semantic_source_object_id"),
        baseline_payload.get("semantic_source_object_id"),
        operation.current.get("semantic_source_object_id"),
        payload.get("semantic_source_object_id"),
        _enum_option_object_id(operation=operation),
        operation.baseline.get("object_id"),
    )


def _enum_option_value(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        operation.current.get("value"),
        operation.current.get("option_value"),
        operation.current.get("entity_name"),
        payload.get("value"),
        payload.get("option_value"),
        payload.get("entity_name"),
        baseline_object.get("value"),
        baseline_object.get("option_value"),
        baseline_object.get("entity_name"),
        baseline_payload.get("value"),
        baseline_payload.get("option_value"),
        baseline_payload.get("entity_name"),
        _enum_option_value_from_semantic_key(operation.semantic_key),
    )


def _enum_option_parent_semantic_key(
    *,
    operation: OntologyTypedOperation,
) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("enum_semantic_key"),
        operation.current.get("parent_semantic_key"),
        payload.get("enum_semantic_key"),
        payload.get("parent_semantic_key"),
        _enum_semantic_key_from_option_semantic_key(operation.semantic_key),
    )


def _enum_option_update_identity_blockers(
    *,
    operation: OntologyTypedOperation,
) -> tuple[str, ...]:
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    payload = mapping_value(operation.current.get("payload"))
    blockers: list[str] = []
    baseline_enum_config_id = _first_text(
        baseline_object.get("enum_config_id"),
        baseline_payload.get("enum_config_id"),
    )
    current_enum_config_id = _first_text(
        operation.current.get("enum_config_id"),
        payload.get("enum_config_id"),
    )
    if (
        baseline_enum_config_id is not None
        and current_enum_config_id is not None
        and baseline_enum_config_id != current_enum_config_id
    ):
        blockers.append("enum_option_update_enum_config_identity_changed")
    baseline_value = _first_text(
        baseline_object.get("value"),
        baseline_object.get("option_value"),
        baseline_payload.get("value"),
        baseline_payload.get("option_value"),
    )
    current_value = _first_text(
        operation.current.get("value"),
        operation.current.get("option_value"),
        payload.get("value"),
        payload.get("option_value"),
    )
    if (
        baseline_value is not None
        and current_value is not None
        and baseline_value != current_value
    ):
        blockers.append("enum_option_update_value_identity_changed")
    return tuple(blockers)


def _enum_node_key(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    baseline_object = mapping_value(operation.baseline.get("object"))
    baseline_payload = mapping_value(baseline_object.get("payload"))
    return _first_text(
        operation.current.get("node_key"),
        payload.get("node_key"),
        baseline_object.get("node_key"),
        baseline_payload.get("node_key"),
        baseline_object.get("enum_fqn"),
        baseline_payload.get("enum_fqn"),
        _enum_node_key_from_semantic_key(operation.semantic_key),
    )


def _enum_fqn(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("enum_fqn"),
        payload.get("enum_fqn"),
        _enum_node_key(operation=operation),
    )


def _enum_name(*, operation: OntologyTypedOperation) -> str | None:
    payload = mapping_value(operation.current.get("payload"))
    return _first_text(
        operation.current.get("entity_name"),
        operation.current.get("name"),
        payload.get("entity_name"),
        payload.get("name"),
        _enum_name_from_node_key(_enum_node_key(operation=operation)),
    )


def _graph_semantic_key_from_enum_semantic_key(value: str) -> str | None:
    graph_key, separator, _ = value.partition("/node:")
    if not separator:
        return None
    return optional_text(graph_key)


def _enum_node_key_from_semantic_key(value: str) -> str | None:
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    return optional_text(node_key.split("/", 1)[0])


def _enum_semantic_key_from_option_semantic_key(value: str) -> str | None:
    enum_key, separator, _ = value.partition("/option:")
    if not separator:
        return None
    return optional_text(enum_key)


def _enum_option_value_from_semantic_key(value: str) -> str | None:
    _, separator, option_key = value.partition("/option:")
    if not separator:
        return None
    return optional_text(option_key)


def _enum_name_from_node_key(value: str | None) -> str | None:
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


def _tuple_text(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return 0
    return 0


__all__ = [
    "ENUM_CONFIG_CREATE_ENUM_OPTION_FUNCTION_REF",
    "ENUM_CONFIG_DELETE_ENUM_OPTION_FUNCTION_REF",
    "ENUM_CONFIG_UPDATE_CONFIG_FUNCTION_REF",
    "ENUM_OPTION_DELETE_INVOCATION_ORDER",
    "ENUM_OPTION_UPDATE_CONFIG_FUNCTION_REF",
    "HANDLER_KEY",
    "OBJECT_CONFIG_GRAPH_NODE_CREATE_ENUM_FUNCTION_REF",
    "plan_enum_operation",
]
