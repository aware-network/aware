from __future__ import annotations

from aware_meta.materialization.deltas import (
    contracts,
    dirty_diff_contracts,
    typed_operation_contracts,
)
from aware_meta.materialization.deltas.constants import (
    META_PROVIDER_DELTA_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION,
    META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION,
    META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION,
)


def test_dirty_diff_contract_module_is_reexported_by_aggregate_contracts() -> None:
    assert contracts.MetaProviderDeltaDirtyEntry is (
        dirty_diff_contracts.MetaProviderDeltaDirtyEntry
    )
    assert contracts.MetaProviderDeltaSemanticDirtyDiff is (
        dirty_diff_contracts.MetaProviderDeltaSemanticDirtyDiff
    )
    assert contracts.dirty_entries_from_payloads is (
        dirty_diff_contracts.dirty_entries_from_payloads
    )

    payload = {
        "status": "semantic_dirty_diff_ready",
        "contract_version": META_PROVIDER_DELTA_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION,
        "available": True,
        "dirty_entry_count": "1",
        "semantic_delta_count": 1,
        "baseline_index_compare_available": True,
        "semantic_dirty_entries": (
            {
                "entry_key": "dirty:home.Device/name",
                "semantic_key": "home.Device/name",
                "dirty_operation": "meta_ocg_attribute_update",
                "baseline_compare_operation": "update",
                "source_refs": "aware/home/device.aware",
                "baseline": {"attribute_name": "name"},
                "current": {"attribute_name": "name"},
            },
        ),
    }

    from_focused = dirty_diff_contracts.MetaProviderDeltaSemanticDirtyDiff.from_payload(
        payload
    )
    from_facade = contracts.MetaProviderDeltaSemanticDirtyDiff.from_payload(payload)

    assert from_focused.ready is True
    assert from_focused.dirty_entry_count == 1
    assert from_focused.entries_for_operation("update")[0].source_refs == (
        "aware/home/device.aware",
    )
    assert from_focused.evidence_payload() == from_facade.evidence_payload()


def test_typed_operation_contract_module_is_reexported_by_aggregate_contracts() -> None:
    assert contracts.MetaProviderDeltaTypedOperation is (
        typed_operation_contracts.MetaProviderDeltaTypedOperation
    )
    assert contracts.MetaProviderDeltaTypedOperationPlan is (
        typed_operation_contracts.MetaProviderDeltaTypedOperationPlan
    )
    assert contracts.typed_operations_from_payloads is (
        typed_operation_contracts.typed_operations_from_payloads
    )

    operation_payload = {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "contract_version": META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION,
        "operation_key": "op:update:attribute:name",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.attribute.update",
        "semantic_key": "home.Device/name",
        "ontology_subject_kind": "attribute",
        "source_refs": ["aware/home/device.aware"],
        "baseline": {"attribute_name": "name"},
        "current": {"attribute_name": "display_name"},
    }
    plan_payload = {
        "status": "typed_operation_plan_ready",
        "contract_version": (META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION),
        "typed_operations": (operation_payload,),
        "semantic_object_anchors": (),
        "blocked_operations": (),
    }

    from_focused = (
        typed_operation_contracts.MetaProviderDeltaTypedOperationPlan.from_payload(
            plan_payload
        )
    )
    from_facade = contracts.MetaProviderDeltaTypedOperationPlan.from_payload(
        plan_payload
    )

    assert len(from_focused.typed_operations) == 1
    assert from_focused.typed_operations[0].contract_version == (
        META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION
    )
    assert from_focused.typed_operations[0].source_refs == ("aware/home/device.aware",)
    assert from_focused.evidence_payload() == from_facade.evidence_payload()
