from __future__ import annotations

from aware_meta.materialization.deltas.capability_matrix import (
    build_provider_delta_functioncall_capability_matrix,
)
from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_FUNCTIONCALL_CAPABILITY_MATRIX_CONTRACT_VERSION,
    META_PROVIDER_DELTA_ONTOLOGY_EXECUTION_PLAN_CONTRACT_VERSION,
    META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION,
    META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION,
    MetaProviderDeltaCapabilityMatrixReceipt,
    MetaProviderDeltaOntologyExecutionPlan,
    MetaProviderDeltaTypedOperation,
    MetaProviderDeltaTypedOperationPlan,
)
from aware_meta.materialization.deltas.ontology_execution.receiver_resolution import (
    semantic_object_anchors_from_plan,
    typed_operations_from_plan,
)


def test_meta_typed_operation_contract_round_trips_public_payload() -> None:
    payload = {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "contract_version": META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION,
        "operation_key": "meta_ocg_provider_delta:update:attribute:home.Device/name",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.attribute.update",
        "semantic_key": "home.Device/name",
        "semantic_subject_type": "attribute_config",
        "ontology_subject_kind": "attribute",
        "source_entry_key": "dirty:home.Device/name",
        "source_delta_key": "delta:home.Device/name",
        "source_refs": ["aware/home/device.aware"],
        "baseline": {"object_id": "baseline-attribute-id"},
        "current": {
            "attribute_name": "name",
            "attribute_signature": {"type_descriptor": {"kind": "primitive"}},
        },
        "ocg_operation": {"operation": "ensure_attribute_config"},
        "source_semantic_change": None,
        "semantic_change_projection": {"change_key": "aware_meta.attribute.update"},
        "function_call_plan": None,
        "blocked": False,
        "blocked_reason": None,
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }

    operation = MetaProviderDeltaTypedOperation.from_payload(payload)

    assert operation is not None
    assert operation.operation_family == "update"
    assert operation.ontology_subject_kind == "attribute"
    assert operation.source_refs == ("aware/home/device.aware",)
    assert operation.evidence_payload() == {
        **payload,
        "source_refs": ("aware/home/device.aware",),
    }


def test_meta_typed_operation_plan_contract_normalizes_operations() -> None:
    payload = {
        "plan_kind": "meta_ocg_provider_delta_typed_operation_plan",
        "contract_version": META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION,
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operations": (
            {
                "operation_kind": "meta_ocg_provider_delta_typed_operation",
                "operation_key": "op:create:attribute",
                "operation_family": "create",
                "provider_operation_type": "meta_ocg.attribute.create",
                "semantic_key": "home.Device/state",
                "ontology_subject_kind": "attribute",
                "baseline": {},
                "current": {"attribute_name": "state"},
                "source_refs": ("aware/home/device.aware",),
            },
        ),
        "semantic_object_anchors": (
            {
                "operation_kind": "meta_ocg_provider_delta_semantic_object_anchor",
                "operation_key": "op:anchor:class",
                "operation_family": "anchor",
                "provider_operation_type": "meta_ocg.class.anchor",
                "semantic_key": "home.Device",
                "ontology_subject_kind": "class",
                "baseline": {"object_id": "class-id"},
                "current": {"entity_name": "Device"},
            },
        ),
        "blocked_operations": (),
    }

    plan = MetaProviderDeltaTypedOperationPlan.from_payload(payload)

    assert plan.status == "typed_operation_plan_ready"
    assert len(plan.typed_operations) == 1
    assert len(plan.semantic_object_anchors) == 1
    assert plan.typed_operations[0].semantic_key == "home.Device/state"
    assert plan.evidence_payload()["typed_operations"] == (
        plan.typed_operations[0].evidence_payload(),
    )


def test_ontology_receiver_resolution_consumes_typed_plan_contract() -> None:
    provider_delta_typed_operation_plan = {
        "status": "typed_operation_plan_ready",
        "typed_operations": (
            {
                "operation_kind": "meta_ocg_provider_delta_typed_operation",
                "operation_key": "op:update:attribute",
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.attribute.update",
                "semantic_key": "home.Device/name",
                "ontology_subject_kind": "attribute",
                "baseline": {"object_id": "attribute-id"},
                "current": {"attribute_name": "name"},
                "source_refs": "aware/home/device.aware",
            },
        ),
        "semantic_object_anchors": (
            {
                "operation_kind": "meta_ocg_provider_delta_semantic_object_anchor",
                "operation_key": "op:anchor:function",
                "operation_family": "anchor",
                "provider_operation_type": "meta_ocg.function.anchor",
                "semantic_key": "home.Device.rename",
                "ontology_subject_kind": "function",
                "baseline": {"object_id": "function-id"},
                "current": {"function_name": "rename"},
            },
        ),
    }

    operations = typed_operations_from_plan(
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan
    )
    anchors = semantic_object_anchors_from_plan(
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan
    )

    assert len(operations) == 1
    assert operations[0].semantic_key == "home.Device/name"
    assert operations[0].source_refs == ("aware/home/device.aware",)
    assert operations[0].baseline == {"object_id": "attribute-id"}
    assert len(anchors) == 1
    assert anchors[0].ontology_subject_kind == "function"


def test_ontology_and_capability_stage_receipts_are_typed_views() -> None:
    ontology_payload = {
        "plan_kind": "meta_ocg_provider_delta_ontology_execution_plan",
        "contract_version": META_PROVIDER_DELTA_ONTOLOGY_EXECUTION_PLAN_CONTRACT_VERSION,
        "status": "ontology_execution_plan_ready",
        "reason": "meta_ocg_ontology_execution_plan_ready",
        "invocation_intent_count": "2",
    }
    ontology_plan = MetaProviderDeltaOntologyExecutionPlan.from_payload(
        ontology_payload
    )

    assert ontology_plan.status == "ontology_execution_plan_ready"
    assert ontology_plan.invocation_intent_count == 2
    assert ontology_plan.evidence_payload() == ontology_payload

    matrix = build_provider_delta_functioncall_capability_matrix(
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "typed_operations": (),
            "blocked_operations": (),
        },
        provider_delta_ontology_execution_plan={
            "status": "ontology_execution_plan_empty",
            "reason": "meta_ocg_ontology_execution_no_typed_operations",
        },
    )
    receipt = MetaProviderDeltaCapabilityMatrixReceipt.from_payload(matrix)

    assert receipt.evidence_payload()["contract_version"] == (
        META_PROVIDER_DELTA_FUNCTIONCALL_CAPABILITY_MATRIX_CONTRACT_VERSION
    )
    assert receipt.execution_allowed is False
