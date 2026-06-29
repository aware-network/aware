from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_ONTOLOGY_EXECUTION_PLAN_CONTRACT_VERSION,
)


ONTOLOGY_EXECUTION_PLAN_CONTRACT_VERSION = (
    META_PROVIDER_DELTA_ONTOLOGY_EXECUTION_PLAN_CONTRACT_VERSION
)
ONTOLOGY_EXECUTION_INTENT_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-ontology-invocation-intent.v1"
)
ONTOLOGY_EXECUTION_HANDLER_RESULT_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-ontology-handler-result.v1"
)


@dataclass(frozen=True, slots=True)
class OntologyTypedOperation:
    operation_key: str
    operation_family: str
    provider_operation_type: str
    semantic_key: str
    ontology_subject_kind: str
    baseline: Mapping[str, object]
    current: Mapping[str, object]
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OntologyExecutionPlanningContext:
    operation_by_semantic_key: Mapping[str, OntologyTypedOperation] = field(
        default_factory=dict,
    )


@dataclass(frozen=True, slots=True)
class OntologyInvocationIntent:
    intent_key: str
    operation_key: str
    semantic_key: str
    invocation_order: int
    invocation_mode: str
    owner_class_name: str
    function_name: str
    function_ref: str
    target_object_id: str | None
    receiver_semantic_key: str | None
    result_semantic_key: str | None
    expected_result_object_id: str | None
    target_projection_name: str | None = None
    target_projection_hash: str | None = None
    result_projection_name: str | None = None
    result_projection_hash: str | None = None
    lane_state_role: str | None = None
    commit_required: bool = False
    kwargs: Mapping[str, object] = field(default_factory=dict)
    reason: str = "ontology_invocation_intent_ready"

    def evidence_payload(self) -> dict[str, object]:
        return {
            "intent_kind": "meta_ocg_provider_delta_ontology_invocation_intent",
            "contract_version": ONTOLOGY_EXECUTION_INTENT_CONTRACT_VERSION,
            "intent_key": self.intent_key,
            "operation_key": self.operation_key,
            "semantic_key": self.semantic_key,
            "invocation_order": self.invocation_order,
            "invocation_mode": self.invocation_mode,
            "owner_class_name": self.owner_class_name,
            "function_name": self.function_name,
            "function_ref": self.function_ref,
            "target_object_id": self.target_object_id,
            "receiver_semantic_key": self.receiver_semantic_key,
            "result_semantic_key": self.result_semantic_key,
            "expected_result_object_id": self.expected_result_object_id,
            "target_projection_name": self.target_projection_name,
            "target_projection_hash": self.target_projection_hash,
            "result_projection_name": self.result_projection_name,
            "result_projection_hash": self.result_projection_hash,
            "lane_state_role": self.lane_state_role,
            "commit_required": self.commit_required,
            "kwargs": dict(self.kwargs),
            "reason": self.reason,
            "execution_wired": False,
            "would_execute": False,
            "did_execute": False,
            "would_persist": False,
            "did_persist": False,
            "production_execution_wired": False,
        }


@dataclass(frozen=True, slots=True)
class OntologyOperationHandlerResult:
    operation_key: str
    semantic_key: str
    handler_key: str
    status: str
    reason: str
    invocation_intents: tuple[OntologyInvocationIntent, ...] = ()
    blockers: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return self.status == "ontology_operation_handler_ready"

    def evidence_payload(self) -> dict[str, object]:
        return {
            "result_kind": "meta_ocg_provider_delta_ontology_handler_result",
            "contract_version": ONTOLOGY_EXECUTION_HANDLER_RESULT_CONTRACT_VERSION,
            "operation_key": self.operation_key,
            "semantic_key": self.semantic_key,
            "handler_key": self.handler_key,
            "status": self.status,
            "reason": self.reason,
            "invocation_intent_count": len(self.invocation_intents),
            "invocation_intents": tuple(
                intent.evidence_payload() for intent in self.invocation_intents
            ),
            "blocker_count": len(self.blockers),
            "blockers": self.blockers,
            "available": self.ready,
            "blocked": not self.ready,
        }


def blocked_handler_result(
    *,
    operation: OntologyTypedOperation,
    handler_key: str,
    reason: str,
    blockers: tuple[str, ...],
) -> OntologyOperationHandlerResult:
    return OntologyOperationHandlerResult(
        operation_key=operation.operation_key,
        semantic_key=operation.semantic_key,
        handler_key=handler_key,
        status="ontology_operation_handler_blocked",
        reason=reason,
        blockers=blockers,
    )


__all__ = [
    "ONTOLOGY_EXECUTION_HANDLER_RESULT_CONTRACT_VERSION",
    "ONTOLOGY_EXECUTION_INTENT_CONTRACT_VERSION",
    "ONTOLOGY_EXECUTION_PLAN_CONTRACT_VERSION",
    "OntologyInvocationIntent",
    "OntologyExecutionPlanningContext",
    "OntologyOperationHandlerResult",
    "OntologyTypedOperation",
    "blocked_handler_result",
]
