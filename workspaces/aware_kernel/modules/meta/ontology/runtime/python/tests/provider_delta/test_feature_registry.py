from __future__ import annotations

from aware_meta.materialization.deltas.feature_registry import (
    ontology_operation_registrations,
    registered_feature_providers,
    typed_operation_dirty_entry_planner_registrations,
)
from aware_meta.materialization.deltas.ontology_execution.registry import (
    registered_operation_families,
    registered_operation_handler_specs,
)


def test_meta_provider_delta_feature_registry_exposes_feature_providers() -> None:
    providers = registered_feature_providers()

    assert [provider.feature_key for provider in providers] == [
        "object_config_graph_package",
        "object_config_graph",
        "object_projection_graph",
        "class_config",
        "enum_config",
        "relationship_config",
        "attribute_config",
        "function_config",
        "function_impl",
    ]
    assert providers[0].ontology_subject_kinds == ("object_config_graph_package",)
    assert providers[0].source_projection_builder is None
    assert providers[1].ontology_subject_kinds == ("object_config_graph",)
    assert providers[1].source_projection_builder is None
    assert providers[2].ontology_subject_kinds == (
        "object_projection_graph",
        "object_projection_graph_node",
    )
    assert providers[2].source_projection_builder is None
    assert providers[3].ontology_subject_kinds == ("class",)
    assert providers[3].source_projection_builder is not None
    assert providers[4].ontology_subject_kinds == ("enum", "enum_option")
    assert providers[4].source_projection_builder is None
    assert providers[5].ontology_subject_kinds == ("relationship",)
    assert providers[5].source_projection_builder is not None
    assert providers[6].ontology_subject_kinds == (
        "attribute",
        "attribute_membership",
    )
    assert providers[6].source_projection_builder is not None
    assert providers[6].generated_materialization_builder is not None
    assert providers[7].ontology_subject_kinds == (
        "function",
        "function_membership",
        "function_invocation",
    )
    assert providers[7].source_projection_builder is not None
    assert providers[7].generated_materialization_builder is not None
    assert providers[8].ontology_subject_kinds == ("function_impl",)
    assert providers[8].source_projection_builder is not None


def test_meta_provider_delta_feature_registry_exposes_ontology_execution() -> None:
    registrations = ontology_operation_registrations()

    assert tuple(registration.handler_key for registration in registrations) == (
        "object_config_graph_package.function_calls",
        "object_config_graph.function_calls",
        "object_projection_graph.function_calls",
        "object_projection_graph.function_calls",
        "class.object_config_graph_node_function_calls",
        "enum.object_config_graph_node_function_calls",
        "enum.object_config_graph_node_function_calls",
        "relationship.class_config_function_calls",
        "attribute.scalar_function_calls",
        "attribute_membership.edge_function_calls",
        "function.scalar_function_calls",
        "function_membership.class_config_function_config_calls",
        "function.invocation_plan_function_calls",
        "function_impl.additive_instruction_body",
    )
    assert registrations[0].registration_keys() == (
        ("object_config_graph_package", "create"),
        ("object_config_graph_package", "update"),
    )
    assert registrations[1].registration_keys() == (("object_config_graph", "create"),)
    assert registrations[2].registration_keys() == (
        ("object_projection_graph", "create"),
    )
    assert registrations[3].registration_keys() == (
        ("object_projection_graph_node", "create"),
    )
    assert registrations[4].registration_keys() == (
        ("class", "create"),
        ("class", "update"),
    )
    assert registrations[5].registration_keys() == (
        ("enum", "create"),
        ("enum", "update"),
    )
    assert registrations[6].registration_keys() == (
        ("enum_option", "create"),
        ("enum_option", "update"),
        ("enum_option", "delete"),
    )
    assert registrations[7].registration_keys() == (
        ("relationship", "create"),
        ("relationship", "update"),
        ("relationship", "delete"),
    )
    assert registrations[8].registration_keys() == (
        ("attribute", "create"),
        ("attribute", "update"),
        ("attribute", "delete"),
    )
    assert registrations[9].registration_keys() == (("attribute_membership", "update"),)
    assert registrations[10].registration_keys() == (
        ("function", "create"),
        ("function", "update"),
    )
    assert registrations[11].registration_keys() == (("function_membership", "update"),)
    assert registrations[12].registration_keys() == (("function_invocation", "create"),)
    assert registrations[13].registration_keys() == (
        ("function_impl", "create"),
        ("function_impl", "update"),
        ("function_impl", "delete"),
    )
    assert registered_operation_families()["function_impl"] == (
        "create",
        "delete",
        "update",
    )


def test_meta_provider_delta_ontology_registry_is_feature_backed() -> None:
    feature_specs = tuple(
        registration.evidence_payload()
        for registration in ontology_operation_registrations()
    )

    assert registered_operation_handler_specs() == feature_specs


def test_meta_provider_delta_feature_registry_exposes_dirty_entry_planners() -> None:
    registrations = typed_operation_dirty_entry_planner_registrations()

    assert tuple(registration.handler_key for registration in registrations) == (
        "class.create.feature_owned_identity",
        "class.update.scope_closure",
        "enum.create.scope_closure",
        "enum.update.scope_closure",
        "enum_option.create.scope_closure",
        "enum_option.update.scope_closure",
        "enum_option.delete.scope_closure",
        "relationship.scope_closure",
        "attribute.update.split_scalar_and_membership",
        "function.create.scope_closure",
        "function.update.scope_closure_and_split_membership",
        "function.invocation_plan.create",
    )
    assert registrations[0].registration_keys() == (("class", "create"),)
    assert registrations[1].registration_keys() == (("class", "update"),)
    assert registrations[2].registration_keys() == (("enum", "create"),)
    assert registrations[3].registration_keys() == (("enum", "update"),)
    assert registrations[4].registration_keys() == (("enum_option", "create"),)
    assert registrations[5].registration_keys() == (("enum_option", "update"),)
    assert registrations[6].registration_keys() == (("enum_option", "delete"),)
    assert registrations[7].registration_keys() == (
        ("relationship", "create"),
        ("relationship", "update"),
        ("relationship", "delete"),
    )
    assert registrations[8].registration_keys() == (("attribute", "update"),)
    assert registrations[9].registration_keys() == (("function", "create"),)
    assert registrations[10].registration_keys() == (("function", "update"),)
    assert registrations[11].registration_keys() == (("function_invocation", "create"),)
