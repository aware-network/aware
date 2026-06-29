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
    STATUS_BLOCKED,
    STATUS_BUILDER_ONLY,
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
        "ocg.relationship.contract",
        "ocg.annotation_semantics",
        "ocg.domain_schema_layout",
        "opg.projection_declaration",
        "opg.root_node_genesis",
        "opg.runtime_materialization",
        "ocg.binding_mirror_event",
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
        "ocg.relationship.contract",
        "ocg.annotation_semantics",
        "opg.projection_declaration",
        "opg.root_node_genesis",
        "opg.runtime_materialization",
    } == blocker_keys


def test_meta_ocg_opg_readiness_matrix_separates_ocg_and_opg() -> None:
    group_counts = {
        GROUP_OCG_IDENTITY: 3,
        GROUP_OCG_NODE: 3,
        GROUP_OCG_MEMBER: 3,
        GROUP_OCG_RELATIONSHIP: 1,
        GROUP_OCG_DERIVED: 3,
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
        STATUS_PARTIAL
    )
    assert entry_by_key["ocg.namespace_fqn_resolution"].blockers == (
        "semantic_scope_closure_still_entry_payload_scoped",
        "committed_external_graph_closure_refs_missing",
    )
    assert entry_by_key["ocg.class.create_update"].typed_operation_status == (
        STATUS_READY
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
        STATUS_BUILDER_ONLY
    )
    assert entry_by_key["opg.runtime_materialization"].typed_operation_status == (
        STATUS_BLOCKED
    )


def test_meta_ocg_opg_readiness_matrix_tracks_production_ready_rails() -> None:
    ready_keys = {
        entry.capability_key for entry in provider_delta_production_ready_entries()
    }

    assert ready_keys == {
        "ocg.package_identity_plane",
        "ocg.graph_root",
        "ocg.class.create_update",
        "ocg.enum.create_update",
        "ocg.function.contract",
        "ocg.attribute.contract",
        "ocg.function_impl.graph",
        "opg.root_node_genesis",
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

    assert builder_only_keys == {
        "ocg.annotation_semantics",
        "ocg.domain_schema_layout",
        "opg.projection_declaration",
        "ocg.binding_mirror_event",
    }
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
    assert payload["builder_retirement_ready_count"] == 0
    assert payload["provider_delta_production_ready_count"] == 8
    assert payload["provider_delta_production_ready_keys"] == (
        "ocg.graph_root",
        "ocg.package_identity_plane",
        "ocg.attribute.contract",
        "ocg.function.contract",
        "ocg.class.create_update",
        "ocg.enum.create_update",
        "opg.root_node_genesis",
        "ocg.function_impl.graph",
    )
    assert payload["minimal_ocg_opg_blocker_count"] == 13
    assert retirement_counts == {
        RETIRE_BLOCKED: 8,
        RETIRE_PARTIAL: 8,
    }
    assert typed_counts == {
        STATUS_BLOCKED: 2,
        STATUS_BUILDER_ONLY: 4,
        STATUS_PARTIAL: 2,
        STATUS_READY: 8,
    }
    assert opg_counts[STATUS_BLOCKED] == 2
    assert opg_counts[STATUS_READY] == 1
    assert opg_counts[STATUS_PARTIAL] == 1
