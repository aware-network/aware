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
    META_OCG_BUILD_FUNCTION_REF,
)


HANDLER_KEY = "object_config_graph.function_calls"
GRAPH_BUILD_INVOCATION_ORDER = 10
OBJECT_CONFIG_GRAPH_PROJECTION_NAME = "ObjectConfigGraph"


def plan_object_config_graph_operation(
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    del context
    if operation.ontology_subject_kind != "object_config_graph":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_ontology_handler_subject_mismatch",
            blockers=(f"unsupported_subject:{operation.ontology_subject_kind}",),
        )
    if operation.operation_family == "create":
        return _plan_graph_create_operation(operation=operation)
    return blocked_handler_result(
        operation=operation,
        handler_key=HANDLER_KEY,
        reason="meta_ocg_graph_delta_requires_create_operation",
        blockers=(f"unsupported_operation_family:{operation.operation_family}",),
    )


def _plan_graph_create_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    graph_id = _graph_id(operation=operation)
    name = _graph_name(operation=operation)
    graph_hash = _graph_hash(operation=operation)
    fqn_prefix = _graph_fqn_prefix(operation=operation)
    language = _graph_language(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("object_config_graph_id", graph_id),
            ("name", name),
            ("hash", graph_hash),
            ("fqn_prefix", fqn_prefix),
            ("language", language),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_graph_create_requires_identity",
            blockers=tuple(f"missing_graph_create_{field}" for field in missing),
        )

    assert graph_id is not None
    assert name is not None
    assert graph_hash is not None
    assert fqn_prefix is not None
    assert language is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_graph_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:build",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=GRAPH_BUILD_INVOCATION_ORDER,
                invocation_mode="constructor",
                owner_class_name="ObjectConfigGraph",
                function_name="build",
                function_ref=META_OCG_BUILD_FUNCTION_REF,
                target_object_id=None,
                receiver_semantic_key=None,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=graph_id,
                result_projection_name=OBJECT_CONFIG_GRAPH_PROJECTION_NAME,
                kwargs=_graph_build_arguments(
                    operation=operation,
                    graph_id=graph_id,
                    name=name,
                    graph_hash=graph_hash,
                    fqn_prefix=fqn_prefix,
                    language=language,
                ),
                reason="meta_ocg_graph_build_function_call_ready",
            ),
        ),
    )


def _graph_build_arguments(
    *,
    operation: OntologyTypedOperation,
    graph_id: str,
    name: str,
    graph_hash: str,
    fqn_prefix: str,
    language: str,
) -> dict[str, object]:
    current = operation.current
    payload = mapping_value(current.get("payload"))
    return {
        "name": name,
        "hash": graph_hash,
        "fqn_prefix": fqn_prefix,
        "language": language,
        "object_config_graph_id": graph_id,
        "object_config_graph_identity_id": _first_text(
            current.get("object_config_graph_identity_id"),
            payload.get("object_config_graph_identity_id"),
        ),
        "description": _first_text(
            current.get("description"),
            payload.get("description"),
        ),
        "layout_hash": _first_text(
            current.get("layout_hash"),
            payload.get("layout_hash"),
        ),
    }


def _graph_id(*, operation: OntologyTypedOperation) -> str | None:
    current = operation.current
    payload = mapping_value(current.get("payload"))
    return _first_text(
        current.get("entity_id"),
        current.get("object_id"),
        payload.get("entity_id"),
        payload.get("object_id"),
    )


def _graph_name(*, operation: OntologyTypedOperation) -> str | None:
    current = operation.current
    payload = mapping_value(current.get("payload"))
    return _first_text(current.get("name"), payload.get("name"))


def _graph_hash(*, operation: OntologyTypedOperation) -> str | None:
    current = operation.current
    payload = mapping_value(current.get("payload"))
    return _first_text(current.get("hash"), payload.get("hash"))


def _graph_fqn_prefix(*, operation: OntologyTypedOperation) -> str | None:
    current = operation.current
    payload = mapping_value(current.get("payload"))
    return _first_text(current.get("fqn_prefix"), payload.get("fqn_prefix"))


def _graph_language(*, operation: OntologyTypedOperation) -> str | None:
    current = operation.current
    payload = mapping_value(current.get("payload"))
    return _first_text(current.get("language"), payload.get("language"), "aware")


def _first_text(*values: object) -> str | None:
    for value in values:
        text = optional_text(value)
        if text is not None:
            return text
    return None


__all__ = [
    "GRAPH_BUILD_INVOCATION_ORDER",
    "HANDLER_KEY",
    "OBJECT_CONFIG_GRAPH_PROJECTION_NAME",
    "plan_object_config_graph_operation",
]
