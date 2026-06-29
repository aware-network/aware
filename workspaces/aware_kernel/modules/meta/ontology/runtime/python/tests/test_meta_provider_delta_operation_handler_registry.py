from __future__ import annotations

from aware_meta.materialization.deltas.ontology_execution.contracts import (
    OntologyTypedOperation,
)
from aware_meta.materialization.deltas.ontology_execution.registry import (
    plan_operation,
    registered_operation_families,
    registered_operation_handler_keys,
    registered_operation_handler_specs,
)


def test_operation_handler_registry_exposes_registered_subject_families() -> None:
    assert registered_operation_handler_keys() == (
        "attribute.scalar_function_calls",
        "attribute_membership.edge_function_calls",
        "class.object_config_graph_node_function_calls",
        "function.scalar_function_calls",
        "function_impl.additive_instruction_body",
        "function_membership.class_config_function_config_calls",
        "relationship.class_config_function_calls",
    )
    assert registered_operation_families() == {
        "attribute": ("create", "delete", "update"),
        "attribute_membership": ("update",),
        "class": ("create", "update"),
        "function": ("update",),
        "function_impl": ("create", "delete", "update"),
        "function_membership": ("update",),
        "relationship": ("create", "delete", "update"),
    }
    assert registered_operation_handler_specs() == (
        {
            "handler_key": "class.object_config_graph_node_function_calls",
            "ontology_subject_kind": "class",
            "operation_families": ("create", "update"),
        },
        {
            "handler_key": "relationship.class_config_function_calls",
            "ontology_subject_kind": "relationship",
            "operation_families": ("create", "update", "delete"),
        },
        {
            "handler_key": "attribute.scalar_function_calls",
            "ontology_subject_kind": "attribute",
            "operation_families": ("create", "update", "delete"),
        },
        {
            "handler_key": "attribute_membership.edge_function_calls",
            "ontology_subject_kind": "attribute_membership",
            "operation_families": ("update",),
        },
        {
            "handler_key": "function.scalar_function_calls",
            "ontology_subject_kind": "function",
            "operation_families": ("update",),
        },
        {
            "handler_key": "function_membership.class_config_function_config_calls",
            "ontology_subject_kind": "function_membership",
            "operation_families": ("update",),
        },
        {
            "handler_key": "function_impl.additive_instruction_body",
            "ontology_subject_kind": "function_impl",
            "operation_families": ("create", "update", "delete"),
        },
    )


def test_operation_handler_registry_routes_known_family_to_handler() -> None:
    result = plan_operation(
        _operation(
            ontology_subject_kind="relationship",
            operation_family="update",
            provider_operation_type="meta_ocg.relationship.update",
        )
    )

    assert result.handler_key == "relationship.class_config_function_calls"
    assert result.status == "ontology_operation_handler_blocked"
    assert result.reason == (
        "meta_ocg_relationship_update_requires_existing_relationship"
    )
    assert result.blockers == (
        "missing_relationship_update_relationship_object_id",
        "missing_relationship_update_relationship_type",
    )


def test_operation_handler_registry_preserves_handler_specific_blockers() -> None:
    result = plan_operation(
        _operation(
            ontology_subject_kind="function_impl",
            operation_family="delete",
            provider_operation_type="meta_ocg.function_impl.delete",
        )
    )

    assert result.handler_key == "function_impl.additive_instruction_body"
    assert result.status == "ontology_operation_handler_blocked"
    assert result.reason == (
        "meta_ocg_function_impl_delta_requires_additive_create_or_update"
    )
    assert result.blockers == ("unsupported_operation_family:delete",)


def test_operation_handler_registry_fails_closed_for_unregistered_family() -> None:
    result = plan_operation(
        _operation(
            ontology_subject_kind="class",
            operation_family="create",
            provider_operation_type="meta_ocg.class.create",
        )
    )

    assert result.handler_key == "class.object_config_graph_node_function_calls"
    assert result.status == "ontology_operation_handler_blocked"
    assert result.reason == "meta_ocg_class_create_requires_graph_and_signature"
    assert result.blockers == (
        "missing_class_create_graph_semantic_key",
        "missing_class_create_graph_object_id",
        "missing_class_create_object_config_graph_node_id",
        "missing_class_create_class_config_id",
        "missing_class_create_node_key",
        "missing_class_create_class_fqn",
        "missing_class_create_name",
    )


def _operation(
    *,
    ontology_subject_kind: str,
    operation_family: str,
    provider_operation_type: str,
) -> OntologyTypedOperation:
    semantic_key = f"home.Device/{ontology_subject_kind}:{operation_family}"
    return OntologyTypedOperation(
        operation_key=f"op:{ontology_subject_kind}:{operation_family}",
        operation_family=operation_family,
        provider_operation_type=provider_operation_type,
        semantic_key=semantic_key,
        ontology_subject_kind=ontology_subject_kind,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "payload": {},
        },
    )
