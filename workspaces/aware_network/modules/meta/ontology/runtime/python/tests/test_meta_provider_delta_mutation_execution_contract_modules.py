from __future__ import annotations

from typing import Any

from aware_meta.materialization.deltas import (
    contracts,
    execution_receipt_contracts,
    mutation_contracts,
)
from aware_meta.materialization.deltas.constants import (
    META_PROVIDER_DELTA_FUNCTIONCALL_CAPABILITY_MATRIX_CONTRACT_VERSION,
    META_PROVIDER_DELTA_HEAD_MOVE_APPLIED_RECEIPT_CONTRACT_VERSION,
    META_PROVIDER_DELTA_MUTATION_PLAN_CONTRACT_VERSION,
    META_PROVIDER_DELTA_MUTATION_STEP_CONTRACT_VERSION,
    META_PROVIDER_DELTA_OIG_COMMIT_RECEIPT_CONTRACT_VERSION,
    META_PROVIDER_DELTA_ONTOLOGY_EXECUTION_PLAN_CONTRACT_VERSION,
    META_PROVIDER_DELTA_OUTPUT_MATERIALIZATION_RECEIPT_CONTRACT_VERSION,
    META_PROVIDER_DELTA_RUNTIME_PACKAGE_INDEX_PATCH_CONTRACT_VERSION,
)


def test_mutation_contract_module_is_reexported_by_aggregate_contracts() -> None:
    assert contracts.MetaProviderDeltaMutationStep is (
        mutation_contracts.MetaProviderDeltaMutationStep
    )
    assert contracts.MetaProviderDeltaMutationPlan is (
        mutation_contracts.MetaProviderDeltaMutationPlan
    )
    assert contracts.mutation_steps_from_payloads is (
        mutation_contracts.mutation_steps_from_payloads
    )

    plan_payload = {
        "status": "mutation_plan_ready",
        "contract_version": META_PROVIDER_DELTA_MUTATION_PLAN_CONTRACT_VERSION,
        "step_contract_version": META_PROVIDER_DELTA_MUTATION_STEP_CONTRACT_VERSION,
        "mutation_step_count": "1",
        "blocked_mutation_step_count": 0,
        "mutation_step_operation_counts": {"meta_ocg.attribute.update": "1"},
        "mutation_steps": (
            {
                "status": "mutation_step_ready",
                "step_key": "step:update:attribute:name",
                "semantic_key": "home.Device/name",
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.attribute.update",
                "ontology_subject_kind": "attribute",
                "function_ref": "aware_meta.attribute_config.update_primitive",
                "receiver_entity_kind": "attribute_config",
                "receiver_entity_id": "attribute-1",
                "arguments": {"primitive_base_type": "Text"},
                "dependencies": ("home.Device",),
            },
        ),
        "blocked_mutation_steps": (),
    }

    from_focused = mutation_contracts.MetaProviderDeltaMutationPlan.from_payload(
        plan_payload
    )
    from_facade = contracts.MetaProviderDeltaMutationPlan.from_payload(plan_payload)

    assert from_focused.ready is True
    assert from_focused.mutation_step_count == 1
    assert from_focused.steps_for_subject("attribute")[0].receiver_entity_id == (
        "attribute-1"
    )
    assert from_focused.evidence_payload() == from_facade.evidence_payload()


def test_execution_receipt_module_is_reexported_by_aggregate_contracts() -> None:
    assert contracts.MetaProviderDeltaOntologyExecutionPlan is (
        execution_receipt_contracts.MetaProviderDeltaOntologyExecutionPlan
    )
    assert contracts.MetaProviderDeltaCapabilityMatrixReceipt is (
        execution_receipt_contracts.MetaProviderDeltaCapabilityMatrixReceipt
    )
    assert contracts.MetaProviderDeltaOigCommitReceipt is (
        execution_receipt_contracts.MetaProviderDeltaOigCommitReceipt
    )
    assert contracts.MetaProviderDeltaHeadMoveAppliedReceipt is (
        execution_receipt_contracts.MetaProviderDeltaHeadMoveAppliedReceipt
    )
    assert contracts.MetaProviderDeltaRuntimePackageIndexPatchReceipt is (
        execution_receipt_contracts.MetaProviderDeltaRuntimePackageIndexPatchReceipt
    )
    assert contracts.MetaProviderDeltaOutputMaterializationReceipt is (
        execution_receipt_contracts.MetaProviderDeltaOutputMaterializationReceipt
    )

    _assert_same_receipt_payload(
        execution_receipt_contracts.MetaProviderDeltaOntologyExecutionPlan,
        contracts.MetaProviderDeltaOntologyExecutionPlan,
        {
            "status": "ontology_execution_plan_ready",
            "contract_version": (
                META_PROVIDER_DELTA_ONTOLOGY_EXECUTION_PLAN_CONTRACT_VERSION
            ),
            "invocation_intent_count": "2",
        },
    )
    _assert_same_receipt_payload(
        execution_receipt_contracts.MetaProviderDeltaCapabilityMatrixReceipt,
        contracts.MetaProviderDeltaCapabilityMatrixReceipt,
        {
            "coverage_status": "functioncall_capability_executable",
            "contract_version": (
                META_PROVIDER_DELTA_FUNCTIONCALL_CAPABILITY_MATRIX_CONTRACT_VERSION
            ),
            "execution_allowed": True,
        },
    )
    oig_focused, oig_facade = _assert_same_receipt_payload(
        execution_receipt_contracts.MetaProviderDeltaOigCommitReceipt,
        contracts.MetaProviderDeltaOigCommitReceipt,
        {
            "status": "execute_flag_commit_applied",
            "contract_version": META_PROVIDER_DELTA_OIG_COMMIT_RECEIPT_CONTRACT_VERSION,
            "commit_id": "commit-1",
            "object_instance_graph_commit_id": "oig-commit-1",
            "ontology_function_call_execution_applied_invocation_count": "2",
        },
    )
    head_focused, _head_facade = _assert_same_receipt_payload(
        execution_receipt_contracts.MetaProviderDeltaHeadMoveAppliedReceipt,
        contracts.MetaProviderDeltaHeadMoveAppliedReceipt,
        {
            "status": "head_move_applied_receipt_ready",
            "contract_version": (
                META_PROVIDER_DELTA_HEAD_MOVE_APPLIED_RECEIPT_CONTRACT_VERSION
            ),
            "head_refs": {
                "head_ref_status": "head_refs_available",
                "semantic_package_commit_id": "semantic-package-commit-1",
                "semantic_object_instance_graph_commit_id": "oig-commit-1",
            },
        },
    )
    index_focused, _index_facade = _assert_same_receipt_payload(
        execution_receipt_contracts.MetaProviderDeltaRuntimePackageIndexPatchReceipt,
        contracts.MetaProviderDeltaRuntimePackageIndexPatchReceipt,
        {
            "status": "runtime_package_index_patch_applied",
            "contract_version": (
                META_PROVIDER_DELTA_RUNTIME_PACKAGE_INDEX_PATCH_CONTRACT_VERSION
            ),
            "semantic_object_upsert_count": "3",
            "semantic_object_delete_count": 1,
            "package_index_semantic_object_count": "12",
        },
    )
    output_focused, _output_facade = _assert_same_receipt_payload(
        execution_receipt_contracts.MetaProviderDeltaOutputMaterializationReceipt,
        contracts.MetaProviderDeltaOutputMaterializationReceipt,
        {
            "status": "provider_delta_output_materialization_ready",
            "contract_version": (
                META_PROVIDER_DELTA_OUTPUT_MATERIALIZATION_RECEIPT_CONTRACT_VERSION
            ),
            "target_count": "2",
            "artifact_ownership_receipt_count": "4",
        },
    )

    assert oig_focused.applied is True
    assert oig_facade.applied is True
    assert oig_focused.applied_invocation_count == 2
    assert head_focused.semantic_package_commit_id == "semantic-package-commit-1"
    assert index_focused.semantic_object_upsert_count == 3
    assert output_focused.ready is True


def _assert_same_receipt_payload(
    focused_cls: Any,
    facade_cls: Any,
    payload: dict[str, object],
) -> tuple[Any, Any]:
    focused = focused_cls.from_payload(payload)
    facade = facade_cls.from_payload(payload)

    assert focused.evidence_payload() == facade.evidence_payload()
    return focused, facade
