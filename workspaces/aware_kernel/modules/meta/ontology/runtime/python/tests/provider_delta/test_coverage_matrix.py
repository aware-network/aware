from __future__ import annotations

from typing import cast

from aware_meta.materialization.deltas.coverage_matrix import (
    HOME_PROOF_COVERED,
    LANGUAGE_TARGET_FUNCTION_IMPL,
    LANGUAGE_TARGET_STRUCTURAL,
    LANGUAGE_TARGET_UNION,
    SOURCE_PROJECTION_POLICIES,
    SOURCE_PROJECTION_POLICY_BLOCKED_NO_CODE_SEGMENT,
    SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
    SOURCE_PROJECTION_POLICY_SEGMENT_READY,
    STATUS_READY,
    STATUS_SKIPPED_POLICY,
    WORKSPACE_DELTA_FIRST_MODE_EXPLICIT_FALLBACK_REQUIRED,
    WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY,
    WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY,
    WORKSPACE_DELTA_FIRST_MODE_PUBLIC_SEGMENT_READY,
    WORKSPACE_DELTA_FIRST_MODE_SEMANTIC_CONTRACT_ONLY,
    WORKSPACE_DELTA_FIRST_MODES,
    coverage_matrix_payload,
    matrix_entries_for_registration_key,
    meta_ocg_delta_product_readiness_payload,
    meta_ocg_delta_coverage_matrix,
    source_projection_gap_entries,
    source_projection_policy_entries,
    source_projection_ready_entries,
    workspace_delta_first_mode_counts,
    workspace_delta_first_mode_entries,
    workspace_delta_first_ready_entries,
)
from aware_meta.materialization.deltas.feature_registry import (
    ontology_operation_registrations,
    registered_feature_providers,
    typed_operation_dirty_entry_planner_registrations,
)


def test_meta_ocg_delta_coverage_matrix_covers_registered_ontology_handlers() -> None:
    registered_keys = {
        (registration.ontology_subject_kind, operation_family)
        for registration in ontology_operation_registrations()
        for operation_family in registration.operation_families
    }

    matrix_keys = {entry.registration_key for entry in meta_ocg_delta_coverage_matrix()}

    assert registered_keys <= matrix_keys


def test_meta_ocg_delta_coverage_matrix_covers_feature_subjects() -> None:
    provider_subjects = {
        (provider.feature_key, subject_kind)
        for provider in registered_feature_providers()
        for subject_kind in provider.ontology_subject_kinds
    }
    matrix_subjects = {
        (entry.feature_key, entry.ontology_subject_kind)
        for entry in meta_ocg_delta_coverage_matrix()
    }

    assert provider_subjects <= matrix_subjects


def test_meta_ocg_delta_coverage_matrix_covers_typed_operation_splits() -> None:
    split_keys = {
        (registration.ontology_subject_kind, operation_family)
        for registration in typed_operation_dirty_entry_planner_registrations()
        for operation_family in registration.operation_families
    }

    for ontology_subject_kind, operation_family in split_keys:
        assert matrix_entries_for_registration_key(
            ontology_subject_kind=ontology_subject_kind,
            operation_family=operation_family,
        )


def test_meta_ocg_delta_coverage_matrix_marks_projected_code_segments() -> None:
    ready_entries = source_projection_ready_entries()

    assert {
        (entry.case_key, entry.code_section_type, entry.code_segment_name)
        for entry in ready_entries
    } == {
        ("attribute.update.default_value", "attribute", "default_value"),
        ("attribute.update.primitive_type", "attribute", "type"),
        ("class.update.metadata", "class", "description_comment"),
        ("enum.update", "enum", "description_comment"),
        ("enum_option.delete", "enum", "option_line"),
        ("enum_option.update", "enum", "option_line"),
        ("function.update.description", "function", "description_comment"),
        ("function.update.signature_shape", "function", "signature"),
        ("function_impl.create", "function", "body"),
        ("function_impl.update.body", "function", "body"),
        ("function_impl.delete.stale_instruction", "function", "body"),
        ("relationship.update.metadata", "annotation", "args"),
    }
    assert all(
        entry.source_projection_status == STATUS_READY for entry in ready_entries
    )
    assert all(entry.code_section_type is not None for entry in ready_entries)
    assert all(entry.code_segment_name is not None for entry in ready_entries)
    assert all(
        entry.source_projection_policy == SOURCE_PROJECTION_POLICY_SEGMENT_READY
        for entry in ready_entries
    )


def test_meta_ocg_delta_coverage_matrix_locks_structural_projection_policy() -> None:
    structural_entries = source_projection_policy_entries(
        policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
    )
    entry_by_case = {entry.case_key: entry for entry in structural_entries}

    assert set(entry_by_case) == {
        "attribute.create",
        "attribute.delete",
        "attribute.identity.rename",
        "attribute_membership.update",
        "class.create",
        "class.delete",
        "enum.create",
        "enum.delete",
        "enum_option.create",
        "function.create",
        "function.delete",
        "function_invocation.create",
        "function_membership.update",
        "object_config_graph.create",
        "object_config_graph_package.create",
        "object_config_graph_package.update",
        "object_projection_graph.create",
        "object_projection_graph_node.create",
        "relationship.create",
        "relationship.delete",
    }
    assert all(
        entry.source_projection_status != STATUS_READY for entry in structural_entries
    )
    assert {
        entry.case_key
        for entry in structural_entries
        if entry.code_segment_name is not None
    } == {"attribute.identity.rename"}
    assert entry_by_case["attribute.identity.rename"].code_segment_name == "name"
    assert entry_by_case["attribute.identity.rename"].ontology_execution_status == (
        STATUS_READY
    )
    assert entry_by_case["attribute.identity.rename"].source_projection_status == (
        STATUS_SKIPPED_POLICY
    )
    assert "ordered attribute.delete + attribute.create" in (
        entry_by_case["attribute.identity.rename"].source_projection_reason
    )
    enum_entries = matrix_entries_for_registration_key(
        ontology_subject_kind="enum",
        operation_family="update",
    )
    assert len(enum_entries) == 1
    assert enum_entries[0].source_projection_status == STATUS_READY
    assert "generated Python enum docstring deltas" in enum_entries[0].notes
    function_delete = entry_by_case["function.delete"]
    assert function_delete.typed_operation_status == STATUS_READY
    assert function_delete.ontology_execution_status == STATUS_READY
    assert function_delete.source_projection_status == STATUS_SKIPPED_POLICY
    assert function_delete.source_projection_reason == (
        "meta_source_projection_function_config_delete_requires_renderer_segment_policy"
    )
    assert "ClassConfig.remove_function_config" in function_delete.notes


def test_meta_ocg_delta_coverage_matrix_locks_missing_segment_blocks() -> None:
    blocked_entries = source_projection_policy_entries(
        policy=SOURCE_PROJECTION_POLICY_BLOCKED_NO_CODE_SEGMENT,
    )

    assert blocked_entries == ()
    assert all(entry.code_segment_name is None for entry in blocked_entries)


def test_meta_ocg_delta_coverage_matrix_exposes_next_source_projection_gaps() -> None:
    p0_gaps = source_projection_gap_entries(priority="P0")

    assert p0_gaps == ()


def test_meta_ocg_delta_coverage_matrix_locks_workspace_delta_first_modes() -> None:
    assert workspace_delta_first_mode_counts() == {
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_SEGMENT_READY: 12,
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY: 13,
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY: 7,
        WORKSPACE_DELTA_FIRST_MODE_SEMANTIC_CONTRACT_ONLY: 0,
        WORKSPACE_DELTA_FIRST_MODE_EXPLICIT_FALLBACK_REQUIRED: 0,
    }
    assert {
        entry.case_key
        for entry in workspace_delta_first_mode_entries(
            mode=WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY,
        )
    } == {
        "attribute.create",
        "attribute.delete",
        "attribute.identity.rename",
        "class.create",
        "class.delete",
        "enum.create",
        "enum.delete",
        "enum_option.create",
        "function.create",
        "function.delete",
        "function_invocation.create",
        "relationship.create",
        "relationship.delete",
    }
    assert {
        entry.case_key
        for entry in workspace_delta_first_mode_entries(
            mode=WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY,
        )
    } == {
        "attribute_membership.update",
        "function_membership.update",
        "object_config_graph.create",
        "object_config_graph_package.create",
        "object_config_graph_package.update",
        "object_projection_graph.create",
        "object_projection_graph_node.create",
    }
    assert {
        entry.case_key
        for entry in workspace_delta_first_mode_entries(
            mode=WORKSPACE_DELTA_FIRST_MODE_SEMANTIC_CONTRACT_ONLY,
        )
    } == set()
    assert {
        entry.case_key
        for entry in workspace_delta_first_mode_entries(
            mode=WORKSPACE_DELTA_FIRST_MODE_EXPLICIT_FALLBACK_REQUIRED,
        )
    } == set()
    assert len(workspace_delta_first_ready_entries()) == 32
    assert all(entry.workspace_delta_first_ready for entry in workspace_delta_first_ready_entries())


def test_meta_ocg_delta_coverage_matrix_records_home_latest_baseline_rows() -> None:
    home_cases = {
        entry.case_key
        for entry in meta_ocg_delta_coverage_matrix()
        if entry.home_proof_status == HOME_PROOF_COVERED
    }

    assert {
        "attribute.create",
        "attribute.delete",
        "attribute.update.default_value",
        "attribute.update.primitive_type",
        "class.create",
        "class.delete",
        "class.update.metadata",
        "enum.create",
        "enum.delete",
        "enum.update",
        "enum_option.create",
        "enum_option.delete",
        "enum_option.update",
        "function.create",
        "function.delete",
        "function_invocation.create",
        "function_membership.update",
        "function.update.description",
        "function.update.signature_shape",
        "function_impl.create",
        "function_impl.delete.stale_instruction",
        "function_impl.update.body",
        "object_config_graph.create",
        "object_config_graph_package.create",
        "object_config_graph_package.update",
        "object_projection_graph.create",
        "object_projection_graph_node.create",
        "relationship.create",
        "relationship.delete",
        "relationship.update.metadata",
    } <= home_cases

    assert all(
        entry.home_proof_refs
        for entry in meta_ocg_delta_coverage_matrix()
        if entry.home_proof_status == HOME_PROOF_COVERED
    )


def test_meta_ocg_delta_coverage_matrix_names_current_language_target_policies() -> (
    None
):
    policy_by_case = {
        entry.case_key: entry.language_target_impact_policy
        for entry in meta_ocg_delta_coverage_matrix()
    }

    assert policy_by_case["function_impl.update.body"] == (
        LANGUAGE_TARGET_FUNCTION_IMPL
    )
    assert policy_by_case["attribute.update.primitive_type"] == (
        LANGUAGE_TARGET_STRUCTURAL
    )
    assert policy_by_case["relationship.update.metadata"] == (
        LANGUAGE_TARGET_STRUCTURAL
    )
    assert policy_by_case["function.update.description"] == (LANGUAGE_TARGET_STRUCTURAL)
    assert policy_by_case["function.update.signature_shape"] == LANGUAGE_TARGET_UNION
    assert policy_by_case["function_membership.update"] == (LANGUAGE_TARGET_STRUCTURAL)


def test_meta_ocg_delta_coverage_matrix_payload_is_stable() -> None:
    payload = coverage_matrix_payload()
    gap_count = payload["source_projection_gap_count"]
    policy_counts = cast(
        dict[str, int],
        payload["source_projection_policy_counts"],
    )

    assert payload["contract_version"] == "aware.meta.ocg-delta-coverage-matrix.v1"
    assert payload["entry_count"] == len(meta_ocg_delta_coverage_matrix())
    assert payload["source_projection_ready_count"] == 12
    assert set(policy_counts) == set(SOURCE_PROJECTION_POLICIES)
    assert policy_counts == {
        SOURCE_PROJECTION_POLICY_BLOCKED_NO_CODE_SEGMENT: 0,
        SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED: 20,
        SOURCE_PROJECTION_POLICY_SEGMENT_READY: 12,
    }
    assert isinstance(gap_count, int)
    assert gap_count == 0
    assert payload["workspace_delta_first_mode_counts"] == {
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_SEGMENT_READY: 12,
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY: 13,
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY: 7,
        WORKSPACE_DELTA_FIRST_MODE_SEMANTIC_CONTRACT_ONLY: 0,
        WORKSPACE_DELTA_FIRST_MODE_EXPLICIT_FALLBACK_REQUIRED: 0,
    }


def test_meta_ocg_delta_product_readiness_payload_is_stable() -> None:
    payload = meta_ocg_delta_product_readiness_payload()
    ready_operations = cast(tuple[dict[str, object], ...], payload["ready_operations"])
    render_all_required = cast(
        tuple[dict[str, object], ...],
        payload["render_all_required_operations"],
    )
    workspace_ready = cast(
        tuple[dict[str, object], ...],
        payload["workspace_delta_first_ready_operations"],
    )
    workspace_generated = cast(
        tuple[dict[str, object], ...],
        payload["workspace_generated_apply_ready_operations"],
    )
    workspace_graph_only = cast(
        tuple[dict[str, object], ...],
        payload["workspace_graph_only_ready_operations"],
    )
    workspace_contract_only = cast(
        tuple[dict[str, object], ...],
        payload["workspace_semantic_contract_only_operations"],
    )
    workspace_explicit_fallback = cast(
        tuple[dict[str, object], ...],
        payload["workspace_explicit_fallback_required_operations"],
    )

    assert payload["readiness_kind"] == "meta_ocg_delta_product_readiness"
    assert payload["contract_version"] == (
        "aware.code.semantic-materialization." "provider-delta-product-readiness.v1"
    )
    assert payload["provider_contract_version"] == (
        "aware.meta.ocg-delta-coverage-matrix.v1"
    )
    assert payload["provider_key"] == "aware_meta"
    assert payload["status"] == "ready"
    assert payload["default_policy"] == "ready_operations_only"
    assert payload["fallback_policy"] == "explicit_fallback_required"
    assert payload["operation_count"] == len(meta_ocg_delta_coverage_matrix())
    assert payload["ready_operation_count"] == 12
    assert payload["render_all_required_operation_count"] == 20
    assert payload["blocked_operation_count"] == 0
    assert payload["workspace_delta_first_default_policy"] == (
        "public_lifecycle_ready_operations_only"
    )
    assert payload["workspace_delta_first_ready_operation_count"] == 32
    assert payload["workspace_delta_first_mode_counts"] == {
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_SEGMENT_READY: 12,
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY: 13,
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY: 7,
        WORKSPACE_DELTA_FIRST_MODE_SEMANTIC_CONTRACT_ONLY: 0,
        WORKSPACE_DELTA_FIRST_MODE_EXPLICIT_FALLBACK_REQUIRED: 0,
    }
    assert {entry["case_key"] for entry in ready_operations} == {
        entry.case_key for entry in source_projection_ready_entries()
    }
    assert all(
        "public_lifecycle_status" in entry
        and "public_lifecycle_refs" in entry
        for entry in (*ready_operations, *render_all_required)
    )
    function_delete = next(
        entry
        for entry in render_all_required
        if entry["case_key"] == "function.delete"
    )
    assert function_delete["public_lifecycle_status"] == HOME_PROOF_COVERED
    assert function_delete["public_lifecycle_refs"] == (
        "workspaces/aware_kernel/docs/proofs/tests/"
        "test_workspace_sdk_kernel_meta_function_config_delete_public_lifecycle_servicehost.py",
    )
    function_impl_create = next(
        entry for entry in ready_operations if entry["case_key"] == "function_impl.create"
    )
    assert function_impl_create["public_lifecycle_status"] == HOME_PROOF_COVERED
    assert function_impl_create["public_lifecycle_refs"] == (
        "workspaces/aware_kernel/docs/proofs/tests/"
        "test_workspace_sdk_kernel_meta_function_impl_create_public_lifecycle_servicehost.py",
    )
    function_invocation_create = next(
        entry
        for entry in render_all_required
        if entry["case_key"] == "function_invocation.create"
    )
    assert function_invocation_create["public_lifecycle_status"] == HOME_PROOF_COVERED
    assert function_invocation_create["public_lifecycle_refs"] == (
        "workspaces/aware_kernel/docs/proofs/tests/"
        "test_workspace_sdk_kernel_meta_function_invocation_create_public_lifecycle_servicehost.py",
    )
    function_membership_update = next(
        entry
        for entry in render_all_required
        if entry["case_key"] == "function_membership.update"
    )
    assert function_membership_update["public_lifecycle_status"] == HOME_PROOF_COVERED
    assert function_membership_update["public_lifecycle_refs"] == (
        "workspaces/aware_kernel/docs/proofs/tests/"
        "test_workspace_sdk_kernel_meta_function_membership_update_public_lifecycle_servicehost.py",
    )
    assert {entry["case_key"] for entry in render_all_required} == {
        entry.case_key
        for entry in source_projection_policy_entries(
            policy=SOURCE_PROJECTION_POLICY_RENDER_ALL_REQUIRED,
        )
    }
    assert {entry["case_key"] for entry in workspace_ready} == {
        entry.case_key for entry in workspace_delta_first_ready_entries()
    }
    assert {entry["workspace_delta_first_mode"] for entry in workspace_ready} == {
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_SEGMENT_READY,
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY,
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY,
    }
    assert all(entry["workspace_delta_first_ready"] for entry in workspace_ready)
    assert {entry["case_key"] for entry in workspace_generated} == {
        entry.case_key
        for entry in workspace_delta_first_mode_entries(
            mode=WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY,
        )
    }
    assert {entry["case_key"] for entry in workspace_graph_only} == {
        "attribute_membership.update",
        "function_membership.update",
        "object_config_graph.create",
        "object_config_graph_package.create",
        "object_config_graph_package.update",
        "object_projection_graph.create",
        "object_projection_graph_node.create",
    }
    assert workspace_contract_only == ()
    assert workspace_explicit_fallback == ()
    assert set(cast(dict[str, int], payload["workspace_delta_first_mode_counts"])) == (
        set(WORKSPACE_DELTA_FIRST_MODES)
    )
