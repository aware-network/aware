from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from aware_meta.materialization.deltas.coercion import (
    int_value,
    mapping_value,
    optional_text,
    tuple_mappings,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperationPlan,
)


ONTOLOGY_MUTATION_PROOF_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-ontology-mutation-proof.v0"
)


def build_provider_delta_ontology_mutation_proof(
    *,
    provider_delta_typed_operation_plan: Mapping[str, object],
    provider_delta_ontology_execution_plan: Mapping[str, object],
    provider_delta_oig_commit_receipt: Mapping[str, object],
    provider_delta_head_move_applied_receipt: Mapping[str, object],
) -> dict[str, object]:
    typed_plan = MetaProviderDeltaTypedOperationPlan.from_payload(
        provider_delta_typed_operation_plan,
    )
    operations_by_key = {
        operation.operation_key: operation for operation in typed_plan.typed_operations
    }
    handlers_by_operation_key = {
        operation_key: handler
        for handler in tuple_mappings(
            provider_delta_ontology_execution_plan.get(
                "operation_handler_results",
            ),
        )
        for operation_key in (optional_text(handler.get("operation_key")),)
        if operation_key is not None
    }
    invocation_intents = tuple_mappings(
        provider_delta_ontology_execution_plan.get("invocation_intents"),
    )
    ontology_execution_receipt = _ontology_execution_receipt(
        provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
    )
    invocation_receipts_by_intent_key = {
        intent_key: receipt
        for receipt in tuple_mappings(
            ontology_execution_receipt.get("invocation_receipts"),
        )
        for intent_key in (optional_text(receipt.get("intent_key")),)
        if intent_key is not None
    }
    entries = tuple(
        _proof_entry(
            intent=intent,
            operation=operations_by_key.get(
                optional_text(intent.get("operation_key")) or "",
            ),
            handler=handlers_by_operation_key.get(
                optional_text(intent.get("operation_key")) or "",
                {},
            ),
            invocation_receipt=invocation_receipts_by_intent_key.get(
                optional_text(intent.get("intent_key")) or "",
                {},
            ),
        )
        for intent in invocation_intents
    )
    blockers = _proof_blockers(
        typed_plan_status=typed_plan.status,
        typed_operation_count=len(typed_plan.typed_operations),
        ontology_execution_plan=provider_delta_ontology_execution_plan,
        provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
        provider_delta_head_move_applied_receipt=(
            provider_delta_head_move_applied_receipt
        ),
        entries=entries,
    )
    status = _proof_status(
        typed_operation_count=len(typed_plan.typed_operations),
        invocation_intent_count=len(invocation_intents),
        commit_status=optional_text(provider_delta_oig_commit_receipt.get("status")),
        blockers=blockers,
    )
    head_refs = mapping_value(
        provider_delta_head_move_applied_receipt.get("head_refs"),
    )
    return {
        "proof_kind": "meta_ocg_provider_delta_ontology_mutation_proof",
        "contract_version": ONTOLOGY_MUTATION_PROOF_CONTRACT_VERSION,
        "status": status,
        "reason": _proof_reason(status=status),
        "ready": status == "ontology_mutation_proof_ready",
        "available": status == "ontology_mutation_proof_ready",
        "blocked": status == "ontology_mutation_proof_blocked",
        "blocker_count": len(blockers),
        "blockers": blockers,
        "typed_operation_plan_status": typed_plan.status,
        "typed_operation_count": len(typed_plan.typed_operations),
        "ontology_execution_plan_status": optional_text(
            provider_delta_ontology_execution_plan.get("status"),
        ),
        "ontology_invocation_intent_count": len(invocation_intents),
        "ontology_invocation_receipt_count": len(invocation_receipts_by_intent_key),
        "ontology_applied_invocation_count": int_value(
            ontology_execution_receipt.get("applied_invocation_count"),
        ),
        "provider_delta_oig_commit_receipt_status": optional_text(
            provider_delta_oig_commit_receipt.get("status"),
        ),
        "provider_delta_oig_commit_id": optional_text(
            provider_delta_oig_commit_receipt.get("commit_id"),
        ),
        "provider_delta_domain_commit_id": optional_text(
            provider_delta_oig_commit_receipt.get("domain_commit_id"),
        ),
        "provider_delta_object_instance_graph_commit_id": optional_text(
            provider_delta_oig_commit_receipt.get(
                "object_instance_graph_commit_id",
            ),
        ),
        "provider_delta_branch_id": optional_text(
            provider_delta_oig_commit_receipt.get("branch_id"),
        ),
        "provider_delta_projection_hash": optional_text(
            provider_delta_oig_commit_receipt.get("projection_hash"),
        ),
        "provider_delta_head_move_applied_receipt_status": optional_text(
            provider_delta_head_move_applied_receipt.get("status"),
        ),
        "provider_delta_head_ref_status": optional_text(
            head_refs.get("head_ref_status"),
        ),
        "head_refs": dict(head_refs),
        "mutation_entry_count": len(entries),
        "satisfied_mutation_entry_count": sum(
            1 for entry in entries if entry["mutation_satisfied"] is True
        ),
        "entries": entries,
        "execution_wired": status == "ontology_mutation_proof_ready",
        "production_execution_wired": status == "ontology_mutation_proof_ready",
    }


def _proof_entry(
    *,
    intent: Mapping[str, object],
    operation: object,
    handler: Mapping[str, object],
    invocation_receipt: Mapping[str, object],
) -> dict[str, object]:
    evidence_payload = getattr(operation, "evidence_payload", None)
    operation_payload = mapping_value(
        cast(object, evidence_payload()) if callable(evidence_payload) else {},
    )
    receipt_status = optional_text(invocation_receipt.get("status"))
    commit_required = intent.get("commit_required") is True
    commit_id = optional_text(invocation_receipt.get("commit_id"))
    mutation_satisfied = (
        bool(invocation_receipt)
        and receipt_status == "succeeded"
        and (not commit_required or commit_id is not None)
    )
    return {
        "entry_kind": "meta_ocg_provider_delta_ontology_mutation_proof_entry",
        "contract_version": ONTOLOGY_MUTATION_PROOF_CONTRACT_VERSION,
        "operation_key": optional_text(intent.get("operation_key")),
        "semantic_key": optional_text(intent.get("semantic_key")),
        "operation_family": optional_text(operation_payload.get("operation_family")),
        "provider_operation_type": optional_text(
            operation_payload.get("provider_operation_type"),
        ),
        "ontology_subject_kind": optional_text(
            operation_payload.get("ontology_subject_kind"),
        ),
        "handler_key": optional_text(handler.get("handler_key")),
        "handler_status": optional_text(handler.get("status")),
        "handler_reason": optional_text(handler.get("reason")),
        "intent_key": optional_text(intent.get("intent_key")),
        "invocation_order": int_value(intent.get("invocation_order")),
        "invocation_mode": optional_text(intent.get("invocation_mode")),
        "owner_class_name": optional_text(intent.get("owner_class_name")),
        "function_name": optional_text(intent.get("function_name")),
        "function_ref": optional_text(intent.get("function_ref")),
        "target_object_id": optional_text(intent.get("target_object_id")),
        "receiver_semantic_key": optional_text(
            intent.get("receiver_semantic_key"),
        ),
        "result_semantic_key": optional_text(intent.get("result_semantic_key")),
        "expected_result_object_id": optional_text(
            intent.get("expected_result_object_id"),
        ),
        "target_projection_name": optional_text(
            intent.get("target_projection_name"),
        ),
        "target_projection_hash": optional_text(
            intent.get("target_projection_hash"),
        ),
        "result_projection_name": optional_text(
            intent.get("result_projection_name"),
        ),
        "result_projection_hash": optional_text(
            intent.get("result_projection_hash"),
        ),
        "lane_state_role": optional_text(intent.get("lane_state_role")),
        "commit_required": commit_required,
        "invocation_receipt_available": bool(invocation_receipt),
        "invocation_receipt_status": receipt_status,
        "function_call_id": optional_text(
            invocation_receipt.get("function_call_id"),
        ),
        "function_call_response_id": optional_text(
            invocation_receipt.get("function_call_response_id"),
        ),
        "branch_id": optional_text(invocation_receipt.get("branch_id")),
        "projection_hash": optional_text(invocation_receipt.get("projection_hash")),
        "commit_id": commit_id,
        "object_instance_graph_commit_id": optional_text(
            invocation_receipt.get("object_instance_graph_commit_id"),
        ),
        "root_object_id": optional_text(invocation_receipt.get("root_object_id")),
        "graph_hash_pre": optional_text(invocation_receipt.get("graph_hash_pre")),
        "graph_hash_post": optional_text(invocation_receipt.get("graph_hash_post")),
        "error": optional_text(invocation_receipt.get("error")),
        "mutation_satisfied": mutation_satisfied,
        "mutation_blockers": _entry_blockers(
            invocation_receipt=invocation_receipt,
            receipt_status=receipt_status,
            commit_required=commit_required,
            commit_id=commit_id,
        ),
    }


def _entry_blockers(
    *,
    invocation_receipt: Mapping[str, object],
    receipt_status: str | None,
    commit_required: bool,
    commit_id: str | None,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if not invocation_receipt:
        blockers.append("invocation_receipt_missing")
    elif receipt_status != "succeeded":
        blockers.append(f"invocation_receipt_not_succeeded:{receipt_status}")
    if commit_required and commit_id is None:
        blockers.append("commit_required_but_commit_id_missing")
    return tuple(blockers)


def _proof_blockers(
    *,
    typed_plan_status: str | None,
    typed_operation_count: int,
    ontology_execution_plan: Mapping[str, object],
    provider_delta_oig_commit_receipt: Mapping[str, object],
    provider_delta_head_move_applied_receipt: Mapping[str, object],
    entries: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    if typed_operation_count == 0 and not entries:
        return ()
    blockers: list[str] = []
    ontology_status = optional_text(ontology_execution_plan.get("status"))
    commit_status = optional_text(provider_delta_oig_commit_receipt.get("status"))
    head_status = optional_text(provider_delta_head_move_applied_receipt.get("status"))
    if typed_plan_status != "typed_operation_plan_ready":
        blockers.append(f"typed_operation_plan_not_ready:{typed_plan_status}")
    if ontology_status != "ontology_execution_plan_ready":
        blockers.append(f"ontology_execution_plan_not_ready:{ontology_status}")
    if commit_status == "execute_flag_commit_not_requested":
        return tuple(dict.fromkeys(blockers))
    if commit_status not in {
        "execute_flag_commit_applied",
        "execute_flag_commit_noop",
    }:
        blockers.append(f"oig_commit_not_applied:{commit_status}")
    if head_status != "head_move_applied_receipt_ready":
        blockers.append(f"head_move_not_ready:{head_status}")
    for entry in entries:
        entry_key = optional_text(entry.get("intent_key")) or "unknown"
        for blocker in _tuple_text(entry.get("mutation_blockers")):
            blockers.append(f"{entry_key}:{blocker}")
    return tuple(dict.fromkeys(blockers))


def _proof_status(
    *,
    typed_operation_count: int,
    invocation_intent_count: int,
    commit_status: str | None,
    blockers: tuple[str, ...],
) -> str:
    if typed_operation_count == 0 and invocation_intent_count == 0:
        return "ontology_mutation_proof_not_required"
    if commit_status == "execute_flag_commit_not_requested":
        return "ontology_mutation_proof_planned"
    if blockers:
        return "ontology_mutation_proof_blocked"
    return "ontology_mutation_proof_ready"


def _proof_reason(*, status: str) -> str:
    return {
        "ontology_mutation_proof_ready": (
            "meta_ocg_provider_delta_ontology_mutation_proof_ready"
        ),
        "ontology_mutation_proof_planned": (
            "meta_ocg_provider_delta_ontology_mutation_proof_execution_not_requested"
        ),
        "ontology_mutation_proof_not_required": (
            "meta_ocg_provider_delta_ontology_mutation_proof_not_required"
        ),
        "ontology_mutation_proof_blocked": (
            "meta_ocg_provider_delta_ontology_mutation_proof_blocked"
        ),
    }.get(status, "meta_ocg_provider_delta_ontology_mutation_proof_unknown")


def _ontology_execution_receipt(
    *,
    provider_delta_oig_commit_receipt: Mapping[str, object],
) -> dict[str, object]:
    return mapping_value(
        provider_delta_oig_commit_receipt.get(
            "ontology_function_call_execution_receipt",
        )
        or provider_delta_oig_commit_receipt.get(
            "ontology_invocation_execution_receipt",
        ),
    )


def _tuple_text(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        text for item in value for text in (optional_text(item),) if text is not None
    )


__all__ = [
    "ONTOLOGY_MUTATION_PROOF_CONTRACT_VERSION",
    "build_provider_delta_ontology_mutation_proof",
]
