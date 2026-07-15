from __future__ import annotations

from typing import cast

from aware_meta.materialization.deltas.ocg_opg_readiness_matrix import (
    GROUP_OCG_DERIVED,
    GROUP_OCG_IDENTITY,
    GROUP_OCG_MEMBER,
    GROUP_OCG_NODE,
    GROUP_OCG_RELATIONSHIP,
    GROUP_OPG_DECLARATION,
    GROUP_OPG_MATERIALIZATION,
    RETIRE_BLOCKED,
    RETIRE_PARTIAL,
    RETIRE_READY,
    STATUS_BLOCKED,
    STATUS_BUILDER_ONLY,
    STATUS_NOT_APPLICABLE,
    STATUS_PARTIAL,
    STATUS_READY,
    builder_retirement_blocked_entries,
    entries_for_capability_group,
    meta_ocg_opg_readiness_matrix,
    minimal_ocg_opg_blocker_entries,
    ocg_opg_readiness_payload,
    provider_delta_production_ready_entries,
)


def test_meta_ocg_opg_readiness_matrix_names_builder_authority_surface() -> None:
    entry_by_key = {
        entry.capability_key: entry for entry in meta_ocg_opg_readiness_matrix()
    }

    assert {
        "ocg.package_identity_plane",
        "ocg.graph_root",
        "ocg.namespace_fqn_resolution",
        "ocg.class.create_update",
        "ocg.class.inheritance_augment",
        "ocg.enum.create_update",
        "ocg.attribute.contract",
        "ocg.function.contract",
        "ocg.function_impl.graph",
        "ocg.relationship.config_contract",
        "ocg.relationship.derived_edges",
        "ocg.relationship.annotation_derived_edges",
        "ocg.annotation_semantics",
        "ocg.namespace_layout",
        "opg.projection_declaration",
        "opg.root_node_genesis",
        "opg.runtime_materialization",
        "ocg.binding_mirror",
    } == set(entry_by_key)
    assert all(
        entry.builder_authority_refs for entry in meta_ocg_opg_readiness_matrix()
    )
    assert entry_by_key["ocg.graph_root"].builder_retirement_status == (RETIRE_PARTIAL)
    assert entry_by_key["ocg.attribute.contract"].builder_retirement_status == (
        RETIRE_PARTIAL
    )


def test_meta_ocg_opg_readiness_matrix_tracks_minimal_p0_blockers() -> None:
    blocker_keys = {entry.capability_key for entry in minimal_ocg_opg_blocker_entries()}

    assert {
        "ocg.package_identity_plane",
        "ocg.graph_root",
        "ocg.namespace_fqn_resolution",
        "ocg.class.create_update",
        "ocg.class.inheritance_augment",
        "ocg.enum.create_update",
        "ocg.attribute.contract",
        "ocg.function.contract",
        "ocg.relationship.annotation_derived_edges",
        "ocg.annotation_semantics",
        "opg.root_node_genesis",
    } == blocker_keys


def test_meta_ocg_opg_readiness_matrix_separates_ocg_and_opg() -> None:
    group_counts = {
        GROUP_OCG_IDENTITY: 3,
        GROUP_OCG_NODE: 3,
        GROUP_OCG_MEMBER: 3,
        GROUP_OCG_RELATIONSHIP: 2,
        GROUP_OCG_DERIVED: 4,
        GROUP_OPG_DECLARATION: 1,
        GROUP_OPG_MATERIALIZATION: 2,
    }

    for group, expected_count in group_counts.items():
        assert len(entries_for_capability_group(capability_group=group)) == (
            expected_count
        )


def test_meta_ocg_opg_readiness_matrix_locks_current_ready_typed_ops() -> None:
    entry_by_key = {
        entry.capability_key: entry for entry in meta_ocg_opg_readiness_matrix()
    }

    assert entry_by_key["ocg.package_identity_plane"].typed_operation_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.graph_root"].typed_operation_status == STATUS_READY
    assert entry_by_key["ocg.namespace_fqn_resolution"].typed_operation_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.namespace_fqn_resolution"].blockers == ()
    assert entry_by_key["ocg.namespace_fqn_resolution"].builder_retirement_status == (
        RETIRE_PARTIAL
    )
    assert entry_by_key["ocg.class.create_update"].typed_operation_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.class.create_update"].source_generated_delta_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.class.create_update"].blockers == (
        "class_genesis_depends_on_ocg_root_and_namespace_closure",
    )
    assert entry_by_key["ocg.class.inheritance_augment"].typed_operation_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.class.inheritance_augment"].ontology_function_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.class.inheritance_augment"].handler_status == STATUS_READY
    assert (
        entry_by_key["ocg.class.inheritance_augment"].functioncall_execution_status
        == STATUS_READY
    )
    assert entry_by_key["ocg.class.inheritance_augment"].oig_commit_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.class.inheritance_augment"].package_index_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.class.inheritance_augment"].source_generated_delta_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.class.inheritance_augment"].blockers == (
        "cross_ocg_augment_functioncall_policy_missing",
    )
    assert entry_by_key["ocg.enum.create_update"].typed_operation_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.enum.create_update"].blockers == (
        "enum_source_generated_delta_policy_incomplete",
    )
    assert (
        entry_by_key["ocg.enum.create_update"].functioncall_execution_status
        == STATUS_READY
    )
    assert entry_by_key["ocg.attribute.contract"].typed_operation_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.function_impl.graph"].typed_operation_status == (
        STATUS_READY
    )
    assert entry_by_key["opg.root_node_genesis"].typed_operation_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.function.contract"].typed_operation_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.function.contract"].source_generated_delta_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.relationship.config_contract"].typed_operation_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.relationship.config_contract"].blockers == ()
    assert (
        entry_by_key["ocg.relationship.config_contract"].source_generated_delta_status
        == STATUS_READY
    )
    assert entry_by_key["ocg.relationship.derived_edges"].typed_operation_status == (
        STATUS_READY
    )
    assert entry_by_key["ocg.relationship.derived_edges"].blockers == ()
    assert (
        entry_by_key["ocg.relationship.derived_edges"].source_generated_delta_status
        == STATUS_NOT_APPLICABLE
    )
    assert (
        entry_by_key["ocg.relationship.annotation_derived_edges"].typed_operation_status
        == STATUS_READY
    )
    assert entry_by_key["ocg.relationship.annotation_derived_edges"].blockers == ()
    assert (
        entry_by_key["ocg.relationship.annotation_derived_edges"].builder_retirement_status
        == RETIRE_PARTIAL
    )
    assert entry_by_key["ocg.annotation_semantics"].typed_operation_status == (
        STATUS_PARTIAL
    )
    assert entry_by_key["ocg.annotation_semantics"].handler_status == STATUS_PARTIAL
    assert entry_by_key["ocg.annotation_semantics"].functioncall_execution_status == (
        STATUS_PARTIAL
    )
    assert entry_by_key["ocg.annotation_semantics"].blockers == (
        "annotation_override_effect_typed_operations_missing",
        "annotation_reference_effect_typed_operations_missing",
        "annotation_storage_effect_typed_operations_missing",
        "annotation_identity_effect_typed_operations_missing",
    )
    assert (
        "aware.meta.ocg-annotation-compile-readiness.v0"
        in entry_by_key["ocg.annotation_semantics"].notes
    )
    assert entry_by_key["ocg.function.contract"].blockers == (
        "function_config_delete_public_lifecycle_proof_missing",
    )
    assert "update description" in entry_by_key["ocg.function.contract"].notes
    assert "signature/async changes" in entry_by_key["ocg.function.contract"].notes
    assert (
        "ClassConfig.remove_function_config"
        in entry_by_key["ocg.function.contract"].notes
    )
    assert entry_by_key["opg.projection_declaration"].typed_operation_status == (
        STATUS_READY
    )
    assert entry_by_key["opg.projection_declaration"].ontology_function_status == (
        STATUS_READY
    )
    assert (
        entry_by_key["opg.projection_declaration"].functioncall_execution_status
        == STATUS_READY
    )
    assert entry_by_key["opg.projection_declaration"].package_index_status == (
        STATUS_READY
    )
    assert entry_by_key["opg.projection_declaration"].source_generated_delta_status == (
        STATUS_READY
    )
    assert entry_by_key["opg.projection_declaration"].blockers == ()
    assert entry_by_key["opg.projection_declaration"].builder_retirement_status == (
        RETIRE_READY
    )
    assert entry_by_key["opg.runtime_materialization"].typed_operation_status == (
        STATUS_READY
    )
    assert (
        entry_by_key["opg.runtime_materialization"].functioncall_execution_status
        == STATUS_READY
    )
    assert entry_by_key["opg.runtime_materialization"].oig_commit_status == (
        STATUS_READY
    )
    assert entry_by_key["opg.runtime_materialization"].package_index_status == (
        STATUS_READY
    )
    assert entry_by_key["opg.runtime_materialization"].blockers == ()
    assert entry_by_key["opg.runtime_materialization"].builder_retirement_status == (
        RETIRE_READY
    )
    assert entry_by_key["ocg.namespace_layout"].typed_operation_status == STATUS_READY
    assert entry_by_key["ocg.namespace_layout"].ontology_function_status == (
        STATUS_NOT_APPLICABLE
    )
    assert entry_by_key["ocg.namespace_layout"].package_index_status == STATUS_READY
    assert entry_by_key["ocg.namespace_layout"].blockers == ()
    assert entry_by_key["ocg.namespace_layout"].builder_retirement_status == (
        RETIRE_READY
    )
    assert (
        "deterministic_recompute_from_committed_ocg_topology"
        in entry_by_key["ocg.namespace_layout"].notes
    )
    assert entry_by_key["ocg.binding_mirror"].typed_operation_status == STATUS_PARTIAL
    assert entry_by_key["ocg.binding_mirror"].ontology_function_status == (
        STATUS_PARTIAL
    )
    assert entry_by_key["ocg.binding_mirror"].handler_status == STATUS_PARTIAL
    assert entry_by_key["ocg.binding_mirror"].functioncall_execution_status == (
        STATUS_PARTIAL
    )
    assert entry_by_key["ocg.binding_mirror"].blockers == (
        "mirror_rewrite_typed_operations_missing",
    )
    assert "persisted_meta_graph_state" in entry_by_key["ocg.binding_mirror"].notes
    assert (
        "authored_code_meta_rewrite_directive"
        in entry_by_key["ocg.binding_mirror"].notes
    )


def test_meta_ocg_opg_readiness_matrix_tracks_production_ready_rails() -> None:
    ready_keys = {
        entry.capability_key for entry in provider_delta_production_ready_entries()
    }

    assert ready_keys == {
        "ocg.package_identity_plane",
        "ocg.graph_root",
        "ocg.class.create_update",
        "ocg.class.inheritance_augment",
        "ocg.enum.create_update",
        "ocg.function.contract",
        "ocg.attribute.contract",
        "ocg.function_impl.graph",
        "ocg.relationship.config_contract",
        "ocg.relationship.derived_edges",
        "ocg.relationship.annotation_derived_edges",
        "opg.projection_declaration",
        "opg.root_node_genesis",
        "opg.runtime_materialization",
    }
    assert all(
        entry.provider_delta_production_ready
        for entry in provider_delta_production_ready_entries()
    )


def test_meta_ocg_opg_readiness_matrix_uses_construct_function_names() -> None:
    entry_by_key = {
        entry.capability_key: entry for entry in meta_ocg_opg_readiness_matrix()
    }
    package_functions = entry_by_key[
        "ocg.package_identity_plane"
    ].required_ontology_functions
    graph_functions = entry_by_key["ocg.graph_root"].required_ontology_functions
    opg_functions = entry_by_key["opg.root_node_genesis"].required_ontology_functions

    assert package_functions == (
        "ObjectConfigGraphPackage.build",
        "ObjectConfigGraphPackage.attach_object_config_graph",
    )
    assert graph_functions == ("ObjectConfigGraph.build",)
    assert "ObjectConfigGraph.create" not in graph_functions
    assert opg_functions == (
        "ObjectProjectionGraph.build_via_object_config_graph",
        "ObjectProjectionGraph.create_node",
    )


def test_meta_ocg_opg_readiness_matrix_shows_builder_only_debt() -> None:
    builder_only_keys = {
        entry.capability_key
        for entry in meta_ocg_opg_readiness_matrix()
        if entry.typed_operation_status == STATUS_BUILDER_ONLY
    }

    assert builder_only_keys == set()
    assert all(
        entry.builder_retirement_status == RETIRE_BLOCKED
        for entry in builder_retirement_blocked_entries()
        if entry.typed_operation_status == STATUS_BUILDER_ONLY
    )


def test_meta_ocg_opg_readiness_matrix_payload_is_stable() -> None:
    payload = ocg_opg_readiness_payload()
    retirement_counts = cast(
        dict[str, int],
        payload["builder_retirement_status_counts"],
    )
    typed_counts = cast(dict[str, int], payload["typed_operation_status_counts"])
    opg_counts = cast(dict[str, int], payload["opg_materialization_status_counts"])

    assert payload["contract_version"] == (
        "aware.meta.ocg-opg-typed-operation-readiness-matrix.v0"
    )
    assert payload["entry_count"] == len(meta_ocg_opg_readiness_matrix())
    assert payload["builder_retirement_ready_count"] == 3
    assert payload["provider_delta_production_ready_count"] == 14
    assert payload["provider_delta_production_ready_keys"] == (
        "ocg.relationship.annotation_derived_edges",
        "ocg.graph_root",
        "ocg.package_identity_plane",
        "ocg.attribute.contract",
        "ocg.function.contract",
        "ocg.class.create_update",
        "ocg.class.inheritance_augment",
        "ocg.enum.create_update",
        "opg.projection_declaration",
        "opg.root_node_genesis",
        "opg.runtime_materialization",
        "ocg.function_impl.graph",
        "ocg.relationship.config_contract",
        "ocg.relationship.derived_edges",
    )
    assert payload["minimal_ocg_opg_blocker_count"] == 11
    assert retirement_counts == {
        RETIRE_BLOCKED: 3,
        RETIRE_PARTIAL: 12,
        RETIRE_READY: 3,
    }
    assert typed_counts == {
        STATUS_PARTIAL: 2,
        STATUS_READY: 16,
    }
    assert opg_counts.get(STATUS_BLOCKED, 0) == 0
    assert opg_counts[STATUS_READY] == 3
    assert opg_counts[STATUS_PARTIAL] == 1
