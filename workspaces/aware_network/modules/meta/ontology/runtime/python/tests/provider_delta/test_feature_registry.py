from __future__ import annotations

from aware_meta.materialization.deltas.feature_registry import (
    generated_materialization_feature_results_from_typed_operation,
    ontology_operation_registrations,
    registered_feature_providers,
    typed_operation_dirty_entry_planner_registrations,
)
from aware_meta.materialization.deltas.code_dto import (
    CodeGeneratedMaterializationDeltaMode,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaGeneratedMaterializationContext,
)
from aware_meta.materialization.deltas.ontology_execution.registry import (
    registered_operation_families,
    registered_operation_handler_specs,
)
from aware_meta.graph.projection.deltas.generated_materialization import (
    OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_REASON,
)
from aware_meta.graph.projection.deltas.typed_operations import (
    object_projection_graph_binding_create_typed_operation,
    object_projection_graph_declaration_create_typed_operation,
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
    assert providers[1].ontology_subject_kinds == (
        "object_config_graph",
        "object_config_graph_identity",
    )
    assert providers[1].source_projection_builder is None
    assert providers[2].ontology_subject_kinds == (
        "object_projection_graph",
        "object_projection_graph_node",
        "object_projection_graph_edge",
        "object_projection_graph_constructor",
        "object_projection_graph_relationship",
        "object_instance_graph",
        "object_projection_graph_declaration",
        "object_projection_graph_binding",
    )
    assert providers[2].source_projection_builder is None
    assert providers[2].generated_materialization_builder is not None
    assert providers[3].ontology_subject_kinds == ("class",)
    assert providers[3].source_projection_builder is not None
    assert providers[3].generated_materialization_builder is not None
    assert providers[4].ontology_subject_kinds == ("enum", "enum_option")
    assert providers[4].source_projection_builder is not None
    assert providers[4].generated_materialization_builder is not None
    assert providers[5].ontology_subject_kinds == ("relationship",)
    assert providers[5].source_projection_builder is not None
    assert providers[5].generated_materialization_builder is not None
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
        "object_config_graph_identity.function_calls",
        "object_config_graph.function_calls",
        "object_projection_graph.function_calls",
        "object_projection_graph.function_calls",
        "object_projection_graph.function_calls",
        "object_projection_graph.function_calls",
        "object_projection_graph.function_calls",
        "object_projection_graph.function_calls",
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
    assert registrations[1].registration_keys() == (
        ("object_config_graph_identity", "create"),
    )
    assert registrations[2].registration_keys() == (("object_config_graph", "create"),)
    assert registrations[3].registration_keys() == (
        ("object_projection_graph", "create"),
    )
    assert registrations[4].registration_keys() == (
        ("object_projection_graph_node", "create"),
    )
    assert registrations[5].registration_keys() == (
        ("object_projection_graph_edge", "create"),
    )
    assert registrations[6].registration_keys() == (
        ("object_projection_graph_constructor", "create"),
    )
    assert registrations[7].registration_keys() == (
        ("object_projection_graph_relationship", "create"),
    )
    assert registrations[8].registration_keys() == (
        ("object_instance_graph", "create"),
    )
    assert registrations[9].registration_keys() == (
        ("object_projection_graph_declaration", "create"),
    )
    assert registrations[10].registration_keys() == (
        ("object_projection_graph_binding", "create"),
    )
    assert registrations[11].registration_keys() == (
        ("class", "create"),
        ("class", "update"),
        ("class", "delete"),
    )
    assert registrations[12].registration_keys() == (
        ("enum", "create"),
        ("enum", "update"),
        ("enum", "delete"),
    )
    assert registrations[13].registration_keys() == (
        ("enum_option", "create"),
        ("enum_option", "update"),
        ("enum_option", "delete"),
    )
    assert registrations[14].registration_keys() == (
        ("relationship", "create"),
        ("relationship", "update"),
        ("relationship", "delete"),
    )
    assert registrations[15].registration_keys() == (
        ("attribute", "create"),
        ("attribute", "update"),
        ("attribute", "delete"),
    )
    assert registrations[16].registration_keys() == (
        ("attribute_membership", "update"),
    )
    assert registrations[17].registration_keys() == (
        ("function", "create"),
        ("function", "update"),
        ("function", "delete"),
    )
    assert registrations[18].registration_keys() == (("function_membership", "update"),)
    assert registrations[19].registration_keys() == (("function_invocation", "create"),)
    assert registrations[20].registration_keys() == (
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
        "class.delete.feature_owned_identity",
        "enum.create.scope_closure",
        "enum.update.scope_closure",
        "enum.delete.scope_closure",
        "enum_option.create.scope_closure",
        "enum_option.update.scope_closure",
        "enum_option.delete.scope_closure",
        "relationship.scope_closure",
        "attribute.update.split_scalar_and_membership",
        "function.create.scope_closure",
        "function.update.scope_closure_and_split_membership",
        "function.delete.scope_closure",
        "function.invocation_plan.create",
    )
    assert registrations[0].registration_keys() == (("class", "create"),)
    assert registrations[1].registration_keys() == (("class", "update"),)
    assert registrations[2].registration_keys() == (("class", "delete"),)
    assert registrations[3].registration_keys() == (("enum", "create"),)
    assert registrations[4].registration_keys() == (("enum", "update"),)
    assert registrations[5].registration_keys() == (("enum", "delete"),)
    assert registrations[6].registration_keys() == (("enum_option", "create"),)
    assert registrations[7].registration_keys() == (("enum_option", "update"),)
    assert registrations[8].registration_keys() == (("enum_option", "delete"),)
    assert registrations[9].registration_keys() == (
        ("relationship", "create"),
        ("relationship", "update"),
        ("relationship", "delete"),
    )
    assert registrations[10].registration_keys() == (("attribute", "update"),)
    assert registrations[11].registration_keys() == (("function", "create"),)
    assert registrations[12].registration_keys() == (("function", "update"),)
    assert registrations[13].registration_keys() == (("function", "delete"),)
    assert registrations[14].registration_keys() == (("function_invocation", "create"),)


def test_opg_projection_declaration_generated_materialization_is_not_required() -> None:
    [result] = generated_materialization_feature_results_from_typed_operation(
        operation=object_projection_graph_declaration_create_typed_operation(
            semantic_key=("ocg:aware_demo/projection_declaration:Runtime"),
            graph_semantic_key="ocg:aware_demo",
            object_config_graph_id="9d65ad6e-36dc-53f4-98a2-cf968714a2d3",
            object_projection_graph_declaration_id=(
                "3d68569d-6bc4-5744-8cf3-3afc3608a730"
            ),
            key="Runtime",
            projection_name="Runtime",
            source_refs=("aware_demo/demo.aware",),
        ),
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="demo-ontology",
            package_root="/tmp/demo",
            sources_root="aware",
            target_language="python",
        ),
    )

    assert result.status == "generated_materialization_skipped"
    assert result.reason == (
        "meta_opg_projection_declaration_generated_materialization_evidence_ready"
    )
    assert result.delta_request is not None
    assert result.delta_request.product_intent == "graph_runtime_projection"
    assert result.delta_request.targets[0].artifact_family == "object_projection_graph"
    assert result.result is not None
    assert result.result.mode is CodeGeneratedMaterializationDeltaMode.not_required
    assert result.result.skipped_targets[0].reason == (
        OPG_PROJECTION_DECLARATION_GENERATED_MATERIALIZATION_REASON
    )


def test_opg_projection_binding_generated_materialization_is_not_required() -> None:
    [result] = generated_materialization_feature_results_from_typed_operation(
        operation=object_projection_graph_binding_create_typed_operation(
            semantic_key=(
                "ocg:aware_demo/projection_declaration:Runtime/"
                "binding:aware_demo.Task"
            ),
            object_projection_graph_declaration_semantic_key=(
                "ocg:aware_demo/projection_declaration:Runtime"
            ),
            object_projection_graph_declaration_id=(
                "3d68569d-6bc4-5744-8cf3-3afc3608a730"
            ),
            object_projection_graph_binding_id=("928d7f0d-9a3f-5e1e-acf7-df88c1a745f0"),
            fqn_prefix="aware_demo",
            namespace="default",
            class_name="Task",
            source_refs=("aware_demo/demo.aware",),
        ),
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="demo-ontology",
            package_root="/tmp/demo",
            sources_root="aware",
            target_language="python",
        ),
    )

    assert result.status == "generated_materialization_skipped"
    assert result.result is not None
    assert result.result.mode is CodeGeneratedMaterializationDeltaMode.not_required
    assert result.result.skipped_targets[0].target is not None
    assert result.result.skipped_targets[0].target.artifact_role == (
        "object_projection_graph_binding"
    )
