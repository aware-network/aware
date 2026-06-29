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
    META_OCG_PACKAGE_ATTACH_GRAPH_FUNCTION_REF,
    META_OCG_PACKAGE_BUILD_FUNCTION_REF,
)


HANDLER_KEY = "object_config_graph_package.function_calls"
PACKAGE_BUILD_INVOCATION_ORDER = 0
PACKAGE_ATTACH_GRAPH_INVOCATION_ORDER = 20
OBJECT_CONFIG_GRAPH_PACKAGE_PROJECTION_NAME = "ObjectConfigGraphPackage"


def plan_object_config_graph_package_operation(
    operation: OntologyTypedOperation,
    context: OntologyExecutionPlanningContext,
) -> OntologyOperationHandlerResult:
    del context
    if operation.ontology_subject_kind != "object_config_graph_package":
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_ontology_handler_subject_mismatch",
            blockers=(f"unsupported_subject:{operation.ontology_subject_kind}",),
        )
    if operation.operation_family == "create":
        return _plan_package_create_operation(operation=operation)
    if operation.operation_family == "update":
        return _plan_package_attach_graph_operation(operation=operation)
    return blocked_handler_result(
        operation=operation,
        handler_key=HANDLER_KEY,
        reason="meta_ocg_package_delta_requires_supported_operation",
        blockers=(f"unsupported_operation_family:{operation.operation_family}",),
    )


def _plan_package_create_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    package_id = _package_id(operation=operation)
    package_name = _package_name(operation=operation)
    fqn_prefix = _package_fqn_prefix(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("object_config_graph_package_id", package_id),
            ("package_name", package_name),
            ("fqn_prefix", fqn_prefix),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_package_create_requires_identity",
            blockers=tuple(f"missing_package_create_{field}" for field in missing),
        )

    assert package_id is not None
    assert package_name is not None
    assert fqn_prefix is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_package_create_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:build",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=PACKAGE_BUILD_INVOCATION_ORDER,
                invocation_mode="constructor",
                owner_class_name="ObjectConfigGraphPackage",
                function_name="build",
                function_ref=META_OCG_PACKAGE_BUILD_FUNCTION_REF,
                target_object_id=None,
                receiver_semantic_key=None,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=package_id,
                result_projection_name=OBJECT_CONFIG_GRAPH_PACKAGE_PROJECTION_NAME,
                kwargs=_package_build_arguments(
                    operation=operation,
                    package_id=package_id,
                    package_name=package_name,
                    fqn_prefix=fqn_prefix,
                ),
                reason="meta_ocg_package_build_function_call_ready",
            ),
        ),
    )


def _plan_package_attach_graph_operation(
    *,
    operation: OntologyTypedOperation,
) -> OntologyOperationHandlerResult:
    package_id = _package_id(operation=operation)
    object_config_graph_id = _object_config_graph_id(operation=operation)
    missing = tuple(
        field_name
        for field_name, value in (
            ("object_config_graph_package_id", package_id),
            ("object_config_graph_id", object_config_graph_id),
        )
        if value is None
    )
    if missing:
        return blocked_handler_result(
            operation=operation,
            handler_key=HANDLER_KEY,
            reason="meta_ocg_package_attach_graph_requires_identity",
            blockers=tuple(
                f"missing_package_attach_graph_{field}" for field in missing
            ),
        )

    assert package_id is not None
    assert object_config_graph_id is not None
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=HANDLER_KEY,
        status="ontology_operation_handler_ready",
        reason="meta_ocg_package_attach_graph_function_call_ready",
        invocation_intents=(
            OntologyInvocationIntent(
                intent_key=f"{operation.operation_key}:attach_object_config_graph",
                operation_key=operation.operation_key,
                semantic_key=operation.semantic_key,
                invocation_order=PACKAGE_ATTACH_GRAPH_INVOCATION_ORDER,
                invocation_mode="instance",
                owner_class_name="ObjectConfigGraphPackage",
                function_name="attach_object_config_graph",
                function_ref=META_OCG_PACKAGE_ATTACH_GRAPH_FUNCTION_REF,
                target_object_id=package_id,
                receiver_semantic_key=operation.semantic_key,
                result_semantic_key=operation.semantic_key,
                expected_result_object_id=package_id,
                target_projection_name=OBJECT_CONFIG_GRAPH_PACKAGE_PROJECTION_NAME,
                kwargs=_package_attach_graph_arguments(
                    operation=operation,
                    object_config_graph_id=object_config_graph_id,
                ),
                reason="meta_ocg_package_attach_graph_function_call_ready",
            ),
        ),
    )


def _package_build_arguments(
    *,
    operation: OntologyTypedOperation,
    package_id: str,
    package_name: str,
    fqn_prefix: str,
) -> dict[str, object]:
    current = operation.current
    payload = mapping_value(current.get("payload"))
    arguments: dict[str, object] = {
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "object_config_graph_package_id": package_id,
        "source_code_package_id": _first_text(
            current.get("source_code_package_id"),
            payload.get("source_code_package_id"),
        ),
        "object_config_graph_id": _object_config_graph_id(operation=operation),
        "object_config_graph_object_instance_graph_commit_id": _first_text(
            current.get("object_config_graph_object_instance_graph_commit_id"),
            payload.get("object_config_graph_object_instance_graph_commit_id"),
        ),
        "title": _first_text(current.get("title"), payload.get("title")),
        "description": _first_text(
            current.get("description"),
            payload.get("description"),
        ),
    }
    for key in (
        "function_impl_ownership",
        "function_impl_parity_policy",
        "implementation_policy_source",
    ):
        value = _first_text(current.get(key), payload.get(key))
        if value is not None:
            arguments[key] = value
    return arguments


def _package_attach_graph_arguments(
    *,
    operation: OntologyTypedOperation,
    object_config_graph_id: str,
) -> dict[str, object]:
    current = operation.current
    payload = mapping_value(current.get("payload"))
    return {
        "object_config_graph_id": object_config_graph_id,
        "object_config_graph_object_instance_graph_commit_id": _first_text(
            current.get("object_config_graph_object_instance_graph_commit_id"),
            payload.get("object_config_graph_object_instance_graph_commit_id"),
        ),
        "title": _first_text(current.get("title"), payload.get("title")),
        "description": _first_text(
            current.get("description"),
            payload.get("description"),
        ),
    }


def _package_id(*, operation: OntologyTypedOperation) -> str | None:
    current = operation.current
    payload = mapping_value(current.get("payload"))
    baseline = operation.baseline
    return _first_text(
        current.get("entity_id"),
        current.get("object_id"),
        payload.get("entity_id"),
        payload.get("object_id"),
        baseline.get("object_id"),
    )


def _package_name(*, operation: OntologyTypedOperation) -> str | None:
    current = operation.current
    payload = mapping_value(current.get("payload"))
    return _first_text(current.get("package_name"), payload.get("package_name"))


def _package_fqn_prefix(*, operation: OntologyTypedOperation) -> str | None:
    current = operation.current
    payload = mapping_value(current.get("payload"))
    return _first_text(current.get("fqn_prefix"), payload.get("fqn_prefix"))


def _object_config_graph_id(*, operation: OntologyTypedOperation) -> str | None:
    current = operation.current
    payload = mapping_value(current.get("payload"))
    return _first_text(
        current.get("object_config_graph_id"),
        payload.get("object_config_graph_id"),
    )


def _first_text(*values: object) -> str | None:
    for value in values:
        text = optional_text(value)
        if text is not None:
            return text
    return None


__all__ = [
    "HANDLER_KEY",
    "OBJECT_CONFIG_GRAPH_PACKAGE_PROJECTION_NAME",
    "PACKAGE_ATTACH_GRAPH_INVOCATION_ORDER",
    "PACKAGE_BUILD_INVOCATION_ORDER",
    "plan_object_config_graph_package_operation",
]
