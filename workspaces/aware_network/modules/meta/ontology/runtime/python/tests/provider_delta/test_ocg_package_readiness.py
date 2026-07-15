from __future__ import annotations

from typing import cast

from aware_meta.materialization.deltas.coverage_matrix import (
    WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY,
    WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY,
    WORKSPACE_DELTA_FIRST_MODE_PUBLIC_SEGMENT_READY,
)
from aware_meta.materialization.deltas.ocg_package_readiness import (
    ANNOTATION_DERIVED_RELATIONSHIP_CAPABILITY_KEY,
    ANNOTATION_SEMANTICS_CAPABILITY_KEY,
    BINDING_MIRROR_CAPABILITY_KEY,
    DERIVED_RELATIONSHIP_CAPABILITY_KEY,
    META_OCG_PACKAGE_READINESS_CONTRACT_VERSION,
    META_OCG_PACKAGE_READINESS_PROOF_CONTRACT_VERSION,
    NAMESPACE_LAYOUT_CAPABILITY_KEY,
    PACKAGE_SPINE_STEP_KEYS,
    PUBLIC_COMPOSITION_FALLBACK_ASSERTIONS,
    PUBLIC_COMPOSITION_LIFECYCLE_STEP_KEYS,
    RELATIONSHIP_CONFIG_CAPABILITY_KEY,
    STEP_STATUS_READY,
    blocked_package_readiness_steps,
    meta_ocg_package_delta_first_readiness_proof_payload,
    meta_ocg_package_readiness_payload,
    meta_ocg_package_readiness_steps,
    meta_ocg_public_composition_lifecycle_payload,
    meta_ocg_public_composition_lifecycle_steps,
    ready_package_spine_steps,
)
from aware_meta.semantic_contract import (
    META_MATERIALIZATION_DELTA_ADAPTER_METADATA,
    META_OCG_PACKAGE_DELTA_FIRST_READINESS_PROOF_KEY,
)


def test_meta_ocg_package_readiness_orders_package_graph_class_function() -> None:
    steps = meta_ocg_package_readiness_steps()

    assert tuple(step.step_key for step in steps) == (
        "object_config_graph_package",
        "object_config_graph",
        "class_config",
        "function_config",
        "update_family",
    )
    assert tuple(step.order for step in steps) == (1, 2, 3, 4, 5)
    assert steps[0].depends_on == ()
    assert steps[1].depends_on == ("object_config_graph_package",)
    assert steps[2].depends_on == ("object_config_graph",)
    assert steps[3].depends_on == ("class_config",)
    assert steps[4].depends_on == ("function_config",)


def test_meta_ocg_package_readiness_locks_valid_meta_ontology_spine() -> None:
    step_by_key = {step.step_key: step for step in meta_ocg_package_readiness_steps()}

    assert step_by_key["object_config_graph_package"].required_ontology_functions == (
        "ObjectConfigGraphPackage.build",
        "ObjectConfigGraphPackage.attach_object_config_graph",
    )
    assert step_by_key["object_config_graph"].required_ontology_functions == (
        "ObjectConfigGraph.build",
    )
    assert step_by_key["class_config"].required_ontology_functions == (
        "ObjectConfigGraph.create_node",
        "ObjectConfigGraphNode.create_class",
    )
    assert step_by_key["function_config"].required_ontology_functions == (
        "ClassConfig.create_function_config",
        "ClassConfigFunctionConfig.update_config",
    )


def test_meta_ocg_package_readiness_payload_marks_package_delta_first_ready() -> None:
    payload = meta_ocg_package_readiness_payload()

    assert payload["contract_version"] == (META_OCG_PACKAGE_READINESS_CONTRACT_VERSION)
    assert payload["readiness_kind"] == "meta_ocg_package_delta_first_readiness"
    assert payload["status"] == "complete_delta_first_ready"
    assert payload["package_spine_ready"] is True
    assert payload["complete_delta_first_ready"] is True
    assert payload["full_genesis_required"] is False
    assert payload["builder_fallback_allowed"] is False
    assert payload["package_spine_step_keys"] == PACKAGE_SPINE_STEP_KEYS
    assert payload["ready_step_count"] == 5
    assert payload["blocked_step_count"] == 0
    assert payload["next_blocked_step"] is None
    assert payload["public_composition_lifecycle_ready"] is True
    assert payload["public_composition_lifecycle_step_keys"] == (
        PUBLIC_COMPOSITION_LIFECYCLE_STEP_KEYS
    )


def test_meta_ocg_package_readiness_marks_graph_only_roots_without_source_apply() -> (
    None
):
    payload = meta_ocg_package_readiness_payload()
    steps = cast(tuple[dict[str, object], ...], payload["steps"])
    step_by_key = {str(step["step_key"]): step for step in steps}

    for step_key in ("object_config_graph_package", "object_config_graph"):
        step = step_by_key[step_key]
        case_evidence = cast(tuple[dict[str, object], ...], step["case_evidence"])
        assert step["status"] == STEP_STATUS_READY
        assert step["readiness_mode"] == "graph_only"
        assert case_evidence[0]["workspace_delta_first_mode"] == (
            WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY
        )
        assert case_evidence[0]["workspace_delta_first_ready"] is True


def test_meta_ocg_package_readiness_tracks_structural_and_update_modes() -> None:
    payload = meta_ocg_package_readiness_payload()
    steps = cast(tuple[dict[str, object], ...], payload["steps"])
    step_by_key = {str(step["step_key"]): step for step in steps}

    class_cases = cast(
        tuple[dict[str, object], ...],
        step_by_key["class_config"]["case_evidence"],
    )
    function_cases = cast(
        tuple[dict[str, object], ...],
        step_by_key["function_config"]["case_evidence"],
    )
    update_cases = cast(
        tuple[dict[str, object], ...],
        step_by_key["update_family"]["case_evidence"],
    )

    assert class_cases[0]["workspace_delta_first_mode"] == (
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY
    )
    assert {case["workspace_delta_first_mode"] for case in function_cases} == {
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GENERATED_APPLY_READY,
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_GRAPH_ONLY_READY,
    }
    assert {case["workspace_delta_first_mode"] for case in update_cases} == {
        WORKSPACE_DELTA_FIRST_MODE_PUBLIC_SEGMENT_READY,
    }
    assert {case["provider_operation_type"] for case in update_cases} >= {
        "meta_ocg.class.update",
        "meta_ocg.function.update",
        "meta_ocg.function_impl.update",
        "meta_ocg.attribute.update",
        "meta_ocg.relationship.update",
    }


def test_meta_ocg_package_readiness_update_family_consumes_relationship_config_only() -> (
    None
):
    blocked_steps = blocked_package_readiness_steps()
    step_by_key = {step.step_key: step for step in meta_ocg_package_readiness_steps()}
    payload = step_by_key["update_family"].evidence_payload()

    assert tuple(step.step_key for step in ready_package_spine_steps()) == (
        "object_config_graph_package",
        "object_config_graph",
        "class_config",
        "function_config",
    )
    assert blocked_steps == ()
    assert payload["status"] == STEP_STATUS_READY
    assert payload["required_capability_keys"] == (
        "ocg.class.create_update",
        "ocg.function.contract",
        "ocg.function_impl.graph",
        "ocg.attribute.contract",
        "ocg.relationship.config_contract",
    )
    blocker_reasons = cast(tuple[str, ...], payload["blocker_reasons"])
    assert blocker_reasons == ()


def test_meta_ocg_package_delta_first_readiness_proof_is_consumer_ready() -> None:
    payload = meta_ocg_package_delta_first_readiness_proof_payload()
    sequence = cast(tuple[dict[str, object], ...], payload["ordered_package_sequence"])

    assert payload["contract_version"] == (
        META_OCG_PACKAGE_READINESS_PROOF_CONTRACT_VERSION
    )
    assert payload["readiness_contract_version"] == (
        META_OCG_PACKAGE_READINESS_CONTRACT_VERSION
    )
    assert payload["proof_kind"] == "meta_ocg_package_delta_first_readiness_proof"
    assert payload["status"] == "complete_delta_first_ready"
    assert payload["package_delta_first_ready"] is True
    assert payload["complete_delta_first_ready"] is True
    assert payload["full_genesis_required"] is False
    assert payload["builder_fallback_allowed"] is False
    assert payload["public_composition_lifecycle_ready"] is True
    assert payload["next_action"] == "materialize_delta_first_without_full_genesis"
    assert payload["ordered_step_keys"] == (
        "object_config_graph_package",
        "object_config_graph",
        "class_config",
        "function_config",
        "update_family",
    )
    assert tuple(step["step_key"] for step in sequence) == payload["ordered_step_keys"]
    assert tuple(step["status"] for step in sequence) == (
        STEP_STATUS_READY,
        STEP_STATUS_READY,
        STEP_STATUS_READY,
        STEP_STATUS_READY,
        STEP_STATUS_READY,
    )


def test_meta_ocg_public_composition_lifecycle_payload_is_consumer_ready() -> None:
    payload = meta_ocg_public_composition_lifecycle_payload()
    steps = cast(tuple[dict[str, object], ...], payload["ordered_steps"])

    assert (
        tuple(step.step_key for step in meta_ocg_public_composition_lifecycle_steps())
        == PUBLIC_COMPOSITION_LIFECYCLE_STEP_KEYS
    )
    assert payload["lifecycle_kind"] == "meta_ocg_public_composition_lifecycle"
    assert payload["status"] == "public_lifecycle_ready"
    assert payload["public_lifecycle_ready"] is True
    assert payload["ordered_step_keys"] == PUBLIC_COMPOSITION_LIFECYCLE_STEP_KEYS
    assert tuple(step["status"] for step in steps) == (
        STEP_STATUS_READY,
        STEP_STATUS_READY,
        STEP_STATUS_READY,
        STEP_STATUS_READY,
    )
    assert tuple(step["public_lifecycle_ready"] for step in steps) == (
        True,
        True,
        True,
        True,
    )
    assert payload["fallback_assertions"] == PUBLIC_COMPOSITION_FALLBACK_ASSERTIONS
    assert payload["blocker_reasons"] == ()
    assert payload["next_action"] == ("run_workspace_delta_first_composition_lifecycle")


def test_meta_ocg_public_composition_lifecycle_locks_operation_surface() -> None:
    payload = meta_ocg_public_composition_lifecycle_payload()

    assert payload["required_case_keys"] == (
        "object_config_graph_package.create",
        "object_config_graph_identity.create",
        "object_config_graph.create",
        "object_config_graph_package.update",
        "class.create",
        "function.create",
        "function_membership.update",
        "attribute.create",
        "relationship.create",
        "attribute.update.primitive_type",
        "relationship.update.metadata",
        "function.update.signature_shape",
        "function.delete",
        "relationship.delete",
        "attribute.delete",
    )
    assert payload["required_provider_operation_types"] == (
        "meta_ocg.object_config_graph_package.create",
        "meta_ocg.object_config_graph_identity.create",
        "meta_ocg.object_config_graph.create",
        "meta_ocg.object_config_graph_package.update",
        "meta_ocg.class.create",
        "meta_ocg.function.create",
        "meta_ocg.function_membership.update",
        "meta_ocg.attribute.create",
        "meta_ocg.relationship.create",
        "meta_ocg.attribute.update",
        "meta_ocg.relationship.update",
        "meta_ocg.function.update",
        "meta_ocg.function.delete",
        "meta_ocg.relationship.delete",
        "meta_ocg.attribute.delete",
    )
    assert payload["public_lifecycle_refs"] == (
        "workspaces/aware_kernel/docs/proofs/tests/"
        "test_workspace_sdk_kernel_meta_ocg_package_class_function_delta_chain_"
        "public_lifecycle_servicehost.py",
        "workspaces/aware_kernel/docs/proofs/tests/"
        "test_workspace_sdk_kernel_meta_ocg_package_attribute_relationship_delta_chain_"
        "public_lifecycle_servicehost.py",
        "workspaces/aware_kernel/docs/proofs/tests/"
        "test_workspace_sdk_kernel_meta_ocg_post_create_update_delta_chain_"
        "public_lifecycle_servicehost.py",
        "workspaces/aware_kernel/docs/proofs/tests/"
        "test_workspace_sdk_kernel_meta_ocg_post_update_delete_delta_chain_"
        "public_lifecycle_servicehost.py",
    )


def test_meta_ocg_package_delta_first_readiness_proof_exposes_public_chain() -> None:
    payload = meta_ocg_package_delta_first_readiness_proof_payload()
    public_chain = cast(
        dict[str, object],
        payload["public_composition_lifecycle"],
    )

    assert public_chain["public_lifecycle_ready"] is True
    assert public_chain["ordered_step_keys"] == PUBLIC_COMPOSITION_LIFECYCLE_STEP_KEYS
    assert public_chain["fallback_assertions"] == (
        PUBLIC_COMPOSITION_FALLBACK_ASSERTIONS
    )


def test_meta_ocg_package_delta_first_readiness_proof_locks_operation_surface() -> None:
    payload = meta_ocg_package_delta_first_readiness_proof_payload()

    assert payload["required_provider_operation_types"] == (
        "meta_ocg.object_config_graph_package.create",
        "meta_ocg.object_config_graph.create",
        "meta_ocg.class.create",
        "meta_ocg.function.create",
        "meta_ocg.function_membership.update",
        "meta_ocg.class.update",
        "meta_ocg.function.update",
        "meta_ocg.function_impl.update",
        "meta_ocg.attribute.update",
        "meta_ocg.relationship.update",
    )
    assert payload["required_ontology_functions"] == (
        "ObjectConfigGraphPackage.build",
        "ObjectConfigGraphPackage.attach_object_config_graph",
        "ObjectConfigGraph.build",
        "ObjectConfigGraph.create_node",
        "ObjectConfigGraphNode.create_class",
        "ClassConfig.create_function_config",
        "ClassConfigFunctionConfig.update_config",
        "ClassConfig.update_config",
        "FunctionConfig.update_config",
        "FunctionImpl.create_instruction",
        "AttributeConfig.update_primitive",
        "ClassConfigRelationship.update_config",
    )


def test_meta_ocg_package_delta_first_readiness_proof_keeps_derived_debt_separate() -> (
    None
):
    payload = meta_ocg_package_delta_first_readiness_proof_payload()
    relationship_config = cast(
        dict[str, object],
        payload["relationship_config_capability"],
    )
    derived_relationship = cast(
        dict[str, object],
        payload["derived_relationship_edge_capability"],
    )
    annotation_derived_relationship = cast(
        dict[str, object],
        payload["relationship_annotation_effect_capability"],
    )
    namespace_layout = cast(
        dict[str, object],
        payload["namespace_layout_recompute_capability"],
    )
    binding_mirror = cast(
        dict[str, object],
        payload["binding_mirror_capability"],
    )
    binding_mirror_contract = cast(
        dict[str, object],
        payload["binding_mirror_contract"],
    )
    annotation_semantics = cast(
        dict[str, object],
        payload["annotation_semantics_capability"],
    )
    annotation_compile_contract = cast(
        dict[str, object],
        payload["annotation_compile_contract"],
    )
    blockers = cast(
        tuple[dict[str, object], ...],
        payload["remaining_builder_retirement_blockers"],
    )

    assert relationship_config["capability_key"] == RELATIONSHIP_CONFIG_CAPABILITY_KEY
    assert relationship_config["provider_delta_production_ready"] is True
    assert relationship_config["blockers"] == ()
    assert derived_relationship["capability_key"] == (
        DERIVED_RELATIONSHIP_CAPABILITY_KEY
    )
    assert derived_relationship["provider_delta_production_ready"] is True
    assert derived_relationship["blockers"] == ()
    assert annotation_derived_relationship["capability_key"] == (
        ANNOTATION_DERIVED_RELATIONSHIP_CAPABILITY_KEY
    )
    assert annotation_derived_relationship["provider_delta_production_ready"] is True
    assert annotation_derived_relationship["blockers"] == ()
    assert ANNOTATION_DERIVED_RELATIONSHIP_CAPABILITY_KEY not in {
        str(blocker["capability_key"]) for blocker in blockers
    }
    assert namespace_layout["capability_key"] == NAMESPACE_LAYOUT_CAPABILITY_KEY
    assert namespace_layout["blockers"] == ()
    assert namespace_layout["builder_retirement_status"] == ("builder_retirement_ready")
    assert NAMESPACE_LAYOUT_CAPABILITY_KEY not in {
        str(blocker["capability_key"]) for blocker in blockers
    }
    assert binding_mirror["capability_key"] == BINDING_MIRROR_CAPABILITY_KEY
    assert binding_mirror["blockers"] == ("mirror_rewrite_typed_operations_missing",)
    assert binding_mirror["typed_operation_status"] == "partial"
    assert binding_mirror_contract["status"] == "partial"
    assert binding_mirror_contract["blockers"] == (
        "mirror_rewrite_typed_operations_missing",
    )
    assert BINDING_MIRROR_CAPABILITY_KEY in {
        str(blocker["capability_key"]) for blocker in blockers
    }
    assert annotation_semantics["capability_key"] == (
        ANNOTATION_SEMANTICS_CAPABILITY_KEY
    )
    assert annotation_semantics["typed_operation_status"] == "partial"
    assert annotation_semantics["blockers"] == (
        "annotation_override_effect_typed_operations_missing",
        "annotation_reference_effect_typed_operations_missing",
        "annotation_storage_effect_typed_operations_missing",
        "annotation_identity_effect_typed_operations_missing",
    )
    assert annotation_compile_contract["status"] == "partial"
    assert annotation_compile_contract["blocked_surface_keys"] == (
        "relationship_override_effect",
        "reference_storage_effects",
    )
    assert "ocg.annotation_semantics" in {
        str(blocker["capability_key"]) for blocker in blockers
    }


def test_meta_semantic_contract_exposes_ocg_package_delta_first_proof() -> None:
    payload = cast(
        dict[str, object],
        META_MATERIALIZATION_DELTA_ADAPTER_METADATA[
            META_OCG_PACKAGE_DELTA_FIRST_READINESS_PROOF_KEY
        ],
    )

    assert payload["proof_kind"] == "meta_ocg_package_delta_first_readiness_proof"
    assert payload["package_delta_first_ready"] is True
    assert payload["full_genesis_required"] is False
    assert payload["builder_fallback_allowed"] is False
    assert payload["next_action"] == "materialize_delta_first_without_full_genesis"
    public_chain = cast(
        dict[str, object],
        payload["public_composition_lifecycle"],
    )
    assert public_chain["ordered_step_keys"] == PUBLIC_COMPOSITION_LIFECYCLE_STEP_KEYS
