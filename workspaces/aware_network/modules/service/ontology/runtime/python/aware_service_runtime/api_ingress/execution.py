from __future__ import annotations

import asyncio
import inspect
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from time import perf_counter
from typing import cast
from uuid import UUID

from aware_api_ontology.api.api_call import ApiCall
from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus
from aware_api_runtime.invocation.materialization import (
    ApiCallOutcomeMaterializationResult,
    materialize_api_call_outcome,
)
from aware_api_runtime.invocation.materialization.telemetry import (
    collect_api_invocation_trace_timings,
)
from aware_code.types import JsonObject, JsonValue
from aware_environment_service_dto.environment.environment import (
    EnvironmentOperationContext,
)
from aware_meta.materialization.contracts import MaterializationLaneContext
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_orm.session.session import Session
from aware_utils.pydantic.class_config_registry import (
    iter_registered_class_config_payloads,
    register_pydantic_package_class_configs,
)
from aware_service_ontology.service.service_enums import (
    ServiceOperationFulfillmentKind,
    ServiceOperationSettlementPolicy,
    ServiceOperationStatus,
)
from aware_service_ontology.service.service_contract_config_operation_grant import (
    ServiceContractConfigOperationGrant,
)
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.service.service_operation_config_role_requirement import (
    ServiceOperationConfigRoleRequirement,
)
from aware_service_runtime.api_ingress.access import (
    ServiceAccessDecisionReason,
    ServiceAccessEvidence,
    ServiceContractOperationPolicySummary,
    build_service_contract_operation_policy_summary,
    resolve_service_contract_operation_access_evidence,
)
from aware_service_runtime.api_ingress.admission_context import (
    ServiceOperationAdmissionContext,
    normalize_service_operation_admission_context,
    service_operation_admission_context_payload,
    service_participant_admission_blocking_reasons,
    service_participant_admission_payload,
)
from aware_service_runtime.api_ingress.contract_access_context import (
    ServiceContractAccessContextResolution,
    ServiceOperationAccessContext,
    resolve_service_contract_access_context_from_admission,
    service_contract_access_context_resolution_payload,
)
from aware_service_runtime.api_ingress.dispatch import (
    ResolvedServiceApiDispatch,
    ResolvedServiceApiDispatchCandidate,
    require_single_service_api_dispatch_candidate,
    resolve_service_api_dispatch,
)
from aware_service_runtime.api_ingress.economy_settlement import (
    ServiceOperationEconomySettlementAdapter,
    build_service_operation_economy_settlement_coordinator,
)
from aware_service_runtime.duplex import dump_service_duplex_payload
from aware_service_runtime.api_ingress.execution_context import (
    ServiceApiExecutionBackend,
    ServiceApiExecutionBackendMode,
    LegacyServiceApiExecutionCallback,
    build_service_api_execution_backend,
)
from aware_service_runtime.api_ingress.host_context import (
    ServiceApiMaterializationContext,
    ServiceEnvironmentCommitReceiptSource,
    service_api_host_context,
)
from aware_service_runtime.api_ingress.ontology_replica_context import (
    ServiceOntologyReplicaQueryProtocol,
)
from aware_service_runtime.api_ingress.ontology_replica_orm_context import (
    ServiceOntologyReplicaOrmSessionProtocol,
)
from aware_service_runtime.api_ingress.graph_execution import (
    ServiceApiGraphExecutionPlan,
    build_service_api_graph_execution_plan,
)
from aware_service_runtime.api_ingress.fulfillment import (
    ValidatedServiceApiFulfillmentContract,
    validate_service_api_fulfillment_contract,
)
from aware_service_runtime.api_ingress.settlement import (
    ServiceOperationMeteringEvidenceV1,
    ServiceOperationMeteringContextV1,
    ServiceOperationSettlementCoordinator,
    ServiceOperationSettlementContext,
    ServiceOperationSettlementFinalization,
    ServiceOperationSettlementPreparation,
    ServiceOperationSettlementReceiptRefs,
    build_service_operation_settlement_context,
    extract_service_operation_metering_receipt,
    normalize_service_operation_metering_evidence,
)
from aware_service_service_dto.comms.models.service import (
    ServiceOperationEconomicReceiptRefsV1,
)
from aware_service_runtime.api_ingress.telemetry import (
    await_with_service_api_trace,
    record_service_api_trace_timing,
    service_api_trace_phase,
)
from aware_service_runtime.ontology.materialization import (
    ServiceOperationMaterializationResult,
    ServiceOperationStatusUpdateResult,
    materialize_service_operation,
    materialize_service_operation_status,
)
from aware_service_runtime.contracts import (
    MetaTemporalGraphRoute,
    RequestStatus,
    ServiceApiDispatchReceipt,
    ServiceGraphGateway,
    ServiceLaneSubscriptionBinding,
    ServiceOperationContext,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
)
from aware_service_runtime.view_provider_routes import (
    ServiceViewProviderRouteDescriptor,
)

from aware_api_runtime.service_protocol import ApiServiceDispatchPlan


class ServiceApiDispatchReceiptPolicy(str, Enum):
    committed = "committed"
    read_model = "read_model"


async def _estimate_service_operation_metering(
    *,
    handler: object,
    endpoint_ref: str,
    request_object: object,
) -> ServiceOperationMeteringEvidenceV1 | None:
    estimator = getattr(handler, "estimate_service_operation_metering", None)
    if not callable(estimator):
        return None
    value = estimator(endpoint_ref=endpoint_ref, request=request_object)
    if inspect.isawaitable(value):
        value = await value
    return normalize_service_operation_metering_evidence(
        value,
        expected_phase="upper_bound",
    )


async def _resolve_service_operation_metering_context(
    *,
    coordinator: ServiceOperationSettlementCoordinator,
    session: Session,
    settlement_context: ServiceOperationSettlementContext,
) -> ServiceOperationMeteringContextV1 | None:
    resolver = getattr(coordinator, "resolve_metering_context", None)
    if not callable(resolver):
        return None
    value = resolver(
        session=session,
        preparation=ServiceOperationSettlementPreparation(
            context=settlement_context,
        ),
    )
    if inspect.isawaitable(value):
        value = await value
    if value is None or isinstance(value, ServiceOperationMeteringContextV1):
        return value
    raise TypeError(
        "Service settlement coordinator returned an invalid metering context: "
        f"{type(value)!r}"
    )


_SUPPORTED_SERVICE_OPERATION_ADMISSION_MODES = {
    "contract_and_permit_required",
    "contract_required",
    "identity_required",
    "metered_settlement_required",
    "public_read",
}


def _record_api_call_outcome_trace_timings_for_servicehost(
    *,
    timings: Mapping[str, float],
) -> None:
    for key, duration_s in sorted(timings.items()):
        phase = key[:-2] if key.endswith("_s") else key
        record_service_api_trace_timing(
            phase=f"dispatch.materialize_api_call_outcome.{phase}",
            duration_s=duration_s,
        )


def _record_dispatch_execute_unattributed(
    *,
    started_at: float,
    child_duration_s: float,
    phase: str,
) -> None:
    total_s = perf_counter() - started_at
    record_service_api_trace_timing(
        phase=f"{phase}.child_tracked",
        duration_s=child_duration_s,
    )
    record_service_api_trace_timing(
        phase=f"{phase}.unattributed",
        duration_s=max(total_s - child_duration_s, 0.0),
    )


@dataclass(frozen=True, slots=True)
class ExecutedServiceApiDispatch:
    resolved_dispatch: ResolvedServiceApiDispatch
    preflight: ServiceApiDispatchPreflightResult
    materialized_operation: ServiceOperationMaterializationResult | None
    updated_operation: ServiceOperationStatusUpdateResult | None
    recorded_api_call_outcome: ApiCallOutcomeMaterializationResult | None
    validated_fulfillment: ValidatedServiceApiFulfillmentContract
    fulfillment_execution_plan: ServiceApiGraphExecutionPlan | None
    execution_object: object | None
    response_object: object | None
    settlement_receipt: ServiceOperationSettlementReceiptRefs | None = None
    receipt_policy: ServiceApiDispatchReceiptPolicy = (
        ServiceApiDispatchReceiptPolicy.committed
    )


@dataclass(frozen=True, slots=True)
class ServiceActorRoleEvidence:
    role_config_id: UUID
    actor_id: UUID | None = None
    access_scope: str = "operation"
    scope_kind: str = "operation"
    scope_ref: str = "default"
    class_instance_identity_id: UUID | None = None
    role_assignment_binding_id: UUID | None = None
    granted: bool = True


@dataclass(frozen=True, slots=True)
class ServiceOperationPreflightResult:
    service_operation_config_id: UUID
    access_evidence: ServiceAccessEvidence | None
    actor_role_evidence: tuple[ServiceActorRoleEvidence, ...]
    contract_admission: ServiceOperationContractAdmissionReadModel


@dataclass(frozen=True, slots=True)
class ServiceApiDispatchPreflightResult:
    candidate: ResolvedServiceApiDispatchCandidate
    access_evidence: ServiceAccessEvidence | None
    actor_role_evidence: tuple[ServiceActorRoleEvidence, ...]
    contract_admission: ServiceOperationContractAdmissionReadModel
    service_operation_fulfillment_kind: ServiceOperationFulfillmentKind
    required_fulfillment_kind: ServiceOperationFulfillmentKind | None = None


@dataclass(frozen=True, slots=True)
class ServiceActorRoleRequirementReadModel:
    role_config_id: UUID
    access_scope: str
    scope_kind: str
    scope_ref: str
    satisfied: bool
    class_instance_identity_required: bool = False
    role_assignment_binding_required: bool = False


@dataclass(frozen=True, slots=True)
class ServiceOperationAdmissionRequirements:
    admission_mode: str
    contract_context_required: bool
    actor_context_required: bool
    permit_required: bool
    settlement_required: bool


@dataclass(frozen=True, slots=True)
class ServiceOperationContractAdmissionReadModel:
    schema: str
    service_id: UUID
    service_operation_config_id: UUID
    actor_id: UUID | None
    admission_mode: str
    status: str
    allowed: bool
    blocking_reasons: tuple[str, ...]
    next_action: str | None
    contract_context_required: bool = False
    actor_context_required: bool = False
    permit_required: bool = False
    settlement_required: bool = False
    access_evidence: ServiceAccessEvidence | None = None
    actor_role_evidence: tuple[ServiceActorRoleEvidence, ...] = ()
    actor_role_requirements: tuple[ServiceActorRoleRequirementReadModel, ...] = ()
    operation_policy: ServiceContractOperationPolicySummary | None = None
    admission_context: ServiceOperationAdmissionContext | None = None
    contract_access_resolution: ServiceContractAccessContextResolution | None = None


class ServiceOperationAdmissionDenied(PermissionError):
    """Raised when ServiceHost ingress is blocked by operation admission policy."""

    def __init__(
        self,
        *,
        admission: ServiceOperationContractAdmissionReadModel,
        message: str,
    ) -> None:
        super().__init__(message)
        self.admission = admission


def service_operation_contract_admission_payload(
    admission: ServiceOperationContractAdmissionReadModel,
) -> JsonObject:
    """Return the public JSON evidence shape for one contract admission read model."""

    return cast(
        JsonObject,
        {
            "schema": admission.schema,
            "service_id": str(admission.service_id),
            "service_operation_config_id": str(admission.service_operation_config_id),
            "actor_id": str(admission.actor_id) if admission.actor_id else None,
            "admission_mode": admission.admission_mode,
            "status": admission.status,
            "allowed": admission.allowed,
            "blocking_reasons": list(admission.blocking_reasons),
            "next_action": admission.next_action,
            "contract_context_required": admission.contract_context_required,
            "actor_context_required": admission.actor_context_required,
            "permit_required": admission.permit_required,
            "settlement_required": admission.settlement_required,
            "access_evidence": _service_access_evidence_payload(
                admission.access_evidence
            ),
            "actor_role_evidence": [
                dump_service_duplex_payload(evidence)
                for evidence in admission.actor_role_evidence
            ],
            "actor_role_requirements": [
                dump_service_duplex_payload(requirement)
                for requirement in admission.actor_role_requirements
            ],
            "operation_policy": dump_service_duplex_payload(admission.operation_policy),
            "participant_admission": service_participant_admission_payload(
                admission.admission_context.participant_admission
                if admission.admission_context is not None
                else None
            ),
            "admission_context": service_operation_admission_context_payload(
                admission.admission_context
            ),
            "contract_access_resolution": (
                service_contract_access_context_resolution_payload(
                    admission.contract_access_resolution
                )
            ),
        },
    )


def service_operation_admission_blocked_payload(
    *,
    admission: ServiceOperationContractAdmissionReadModel,
    endpoint_ref: str | None = None,
    discriminant: str | None = None,
    network_request_id: UUID | None = None,
) -> JsonObject:
    """Return the product response shape for blocked ServiceHost API ingress."""

    blocker = (
        admission.blocking_reasons[0]
        if admission.blocking_reasons
        else "service_admission_denied"
    )
    return cast(
        JsonObject,
        {
            "schema": "aware.service.admission.blocked_response.v0",
            "status": "blocked",
            "blocker": blocker,
            "blocking_reasons": list(admission.blocking_reasons),
            "missing_requirements": list(admission.blocking_reasons),
            "next_action": admission.next_action,
            "endpoint_ref": endpoint_ref,
            "discriminant": discriminant,
            "network_request_id": (
                str(network_request_id) if network_request_id is not None else None
            ),
            "service_id": str(admission.service_id),
            "service_operation_config_id": str(admission.service_operation_config_id),
            "actor_id": str(admission.actor_id) if admission.actor_id else None,
            "admission_mode": admission.admission_mode,
            "contract_context_required": admission.contract_context_required,
            "actor_context_required": admission.actor_context_required,
            "permit_required": admission.permit_required,
            "settlement_required": admission.settlement_required,
            "participant_admission": service_participant_admission_payload(
                admission.admission_context.participant_admission
                if admission.admission_context is not None
                else None
            ),
            "admission_context": service_operation_admission_context_payload(
                admission.admission_context
            ),
            "contract_access_resolution": (
                service_contract_access_context_resolution_payload(
                    admission.contract_access_resolution
                )
            ),
            "service_admission": service_operation_contract_admission_payload(
                admission
            ),
        },
    )


def service_api_dispatch_response_payload(
    *,
    executed: ExecutedServiceApiDispatch,
) -> JsonValue:
    """Serialize a dispatch response, carrying admission evidence for read models."""

    payload = dump_service_duplex_payload(executed.response_object)
    if executed.receipt_policy is not ServiceApiDispatchReceiptPolicy.read_model:
        return payload
    if not isinstance(payload, dict):
        return payload
    admission_payload = service_operation_contract_admission_payload(
        executed.preflight.contract_admission
    )
    enriched = dict(payload)
    enriched["service_admission"] = admission_payload
    _append_status_result_service_admission_block(
        payload=enriched,
        admission_payload=admission_payload,
    )
    return cast(JsonValue, enriched)


def service_api_dispatch_receipt(
    *,
    executed: ExecutedServiceApiDispatch,
    network_request_id: UUID | None = None,
    status: RequestStatus = RequestStatus.succeeded,
) -> ServiceApiDispatchReceipt:
    """Build transport receipt metadata without changing endpoint response payloads."""

    envelope = executed.resolved_dispatch.dispatch_plan.envelope
    service_operation = executed.updated_operation or executed.materialized_operation
    service_binding = (
        service_operation.binding if service_operation is not None else None
    )
    api_call_outcome_binding = (
        executed.recorded_api_call_outcome.binding
        if executed.recorded_api_call_outcome is not None
        else None
    )
    return ServiceApiDispatchReceipt(
        endpoint_ref=envelope.endpoint_ref,
        discriminant=envelope.discriminant,
        status=status,
        network_request_id=network_request_id,
        api_call_id=envelope.api_call_id,
        api_capability_endpoint_id=envelope.api_capability_endpoint_id,
        call_key=envelope.call_key,
        request_hash=envelope.request_hash,
        request_model_id=envelope.request_model_id,
        api_call_outcome_id=(
            api_call_outcome_binding.api_call_outcome_id
            if api_call_outcome_binding is not None
            else None
        ),
        response_model_id=(
            api_call_outcome_binding.response_model_id
            if api_call_outcome_binding is not None
            else None
        ),
        service_operation_id=(
            service_binding.service_operation_id
            if service_binding is not None
            else None
        ),
        service_operation_config_id=(
            service_binding.service_operation_config_id
            if service_binding is not None
            else None
        ),
        service_operation_config_api_endpoint_id=(
            service_binding.api_endpoint_id if service_binding is not None else None
        ),
        service_operation_commit_id=(
            service_binding.commit_id if service_binding is not None else None
        ),
        service_operation_head_commit_id=(
            service_binding.head_commit_id if service_binding is not None else None
        ),
        service_operation_branch_id=(
            service_binding.branch_id if service_binding is not None else None
        ),
        service_operation_projection_hash=(
            service_binding.projection_hash if service_binding is not None else None
        ),
        api_call_outcome_commit_id=(
            api_call_outcome_binding.commit_id
            if api_call_outcome_binding is not None
            else None
        ),
        api_call_outcome_head_commit_id=(
            api_call_outcome_binding.head_commit_id
            if api_call_outcome_binding is not None
            else None
        ),
        api_call_outcome_branch_id=(
            api_call_outcome_binding.branch_id
            if api_call_outcome_binding is not None
            else None
        ),
        api_call_outcome_projection_hash=(
            api_call_outcome_binding.projection_hash
            if api_call_outcome_binding is not None
            else None
        ),
        economic_receipt=(
            ServiceOperationEconomicReceiptRefsV1(
                service_operation_id=executed.settlement_receipt.service_operation_id,
                service_contract_id=executed.settlement_receipt.service_contract_id,
                permit_id=executed.settlement_receipt.permit_id,
                price_id=executed.settlement_receipt.price_id,
                price_schedule_id=executed.settlement_receipt.price_schedule_id,
                rate_snapshot_id=executed.settlement_receipt.rate_snapshot_id,
                price_reservation_id=executed.settlement_receipt.price_reservation_id,
                smart_contract_reservation_id=(
                    executed.settlement_receipt.smart_contract_reservation_id
                ),
                settlement_id=executed.settlement_receipt.settlement_id,
                transaction_id=executed.settlement_receipt.transaction_id,
                payer_wallet_balance_id=(
                    executed.settlement_receipt.payer_wallet_balance_id
                ),
                receiver_wallet_balance_id=(
                    executed.settlement_receipt.receiver_wallet_balance_id
                ),
                status=executed.settlement_receipt.status,
                idempotent_replay=executed.settlement_receipt.idempotent_replay,
            )
            if executed.settlement_receipt is not None
            else None
        ),
    )


def _service_access_evidence_payload(
    evidence: ServiceAccessEvidence | None,
) -> JsonObject | None:
    if evidence is None:
        return None
    return cast(
        JsonObject,
        {
            "service_id": str(evidence.service_id),
            "consumer_finance_entity_id": str(evidence.consumer_finance_entity_id),
            "access_granted": evidence.access_granted,
            "reason": evidence.reason.value,
            "service_subscription_id": (
                str(evidence.service_subscription_id)
                if evidence.service_subscription_id
                else None
            ),
            "service_plan_id": (
                str(evidence.service_plan_id) if evidence.service_plan_id else None
            ),
            "service_operation_config_id": (
                str(evidence.service_operation_config_id)
                if evidence.service_operation_config_id
                else None
            ),
            "smart_contract_id": (
                str(evidence.smart_contract_id) if evidence.smart_contract_id else None
            ),
            "service_contract_id": (
                str(evidence.service_contract_id)
                if evidence.service_contract_id
                else None
            ),
            "service_contract_config_id": (
                str(evidence.service_contract_config_id)
                if evidence.service_contract_config_id
                else None
            ),
            "service_contract_config_operation_grant_id": (
                str(evidence.service_contract_config_operation_grant_id)
                if evidence.service_contract_config_operation_grant_id
                else None
            ),
            "subscription_status": (
                evidence.subscription_status.value
                if evidence.subscription_status
                else None
            ),
            "service_contract_status": (
                evidence.service_contract_status.value
                if evidence.service_contract_status
                else None
            ),
            "current_period_start": (
                evidence.current_period_start.isoformat()
                if evidence.current_period_start
                else None
            ),
            "current_period_end": (
                evidence.current_period_end.isoformat()
                if evidence.current_period_end
                else None
            ),
            "contract_effective_from": (
                evidence.contract_effective_from.isoformat()
                if evidence.contract_effective_from
                else None
            ),
            "contract_effective_until": (
                evidence.contract_effective_until.isoformat()
                if evidence.contract_effective_until
                else None
            ),
            "cancel_at_period_end": evidence.cancel_at_period_end,
            "external_subscription_handle": evidence.external_subscription_handle,
            "source": evidence.source,
            "commercial_scope": evidence.commercial_scope,
            "pricing_scope": evidence.pricing_scope,
        },
    )


def _append_status_result_service_admission_block(
    *,
    payload: dict[str, object],
    admission_payload: JsonObject,
) -> None:
    result = payload.get("result")
    if not isinstance(result, dict):
        return
    blocks = result.get("blocks")
    if blocks is None:
        existing_blocks: list[object] = []
    elif isinstance(blocks, list):
        existing_blocks = list(blocks)
    else:
        return
    if any(
        isinstance(block, dict) and block.get("name") == "service_admission"
        for block in existing_blocks
    ):
        return
    blocking_reasons = admission_payload.get("blocking_reasons")
    result["blocks"] = [
        *existing_blocks,
        {
            "name": "service_admission",
            "authority_kind": "service_contract_admission",
            "available": bool(admission_payload.get("allowed")),
            "unavailable_reason": (
                ", ".join(str(item) for item in blocking_reasons)
                if isinstance(blocking_reasons, list) and blocking_reasons
                else None
            ),
            "payload": admission_payload,
        },
    ]


ServiceApiOperationAccessContext = ServiceOperationAccessContext
ServiceApiActorRoleEvidence = ServiceActorRoleEvidence


ServiceApiStreamEventSink = Callable[[object], Awaitable[None]]


def _service_operation_context_for_lane(
    *,
    admission_context: ServiceOperationAdmissionContext,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    operation_key: str,
) -> ServiceOperationContext:
    _ = (admission_context, operation_key)
    return ServiceOperationContext(
        actor_id=actor_id,
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )


def _environment_operation_context_for_lane(
    *,
    admission_context: ServiceOperationAdmissionContext,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
) -> EnvironmentOperationContext | None:
    session_scope = admission_context.session_scope
    if session_scope is None or session_scope.environment_id is None:
        return None
    return EnvironmentOperationContext(
        actor_id=actor_id,
        environment_id=session_scope.environment_id,
        process_id=session_scope.process_id,
        thread_id=session_scope.thread_id,
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )


async def execute_service_api_dispatch_plan(
    *,
    runtime: object,
    index: object,
    session: Session,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    api_source_lane: MaterializationLaneContext | None = None,
    execution_target_lane: MaterializationLaneContext | None = None,
    dispatch_plan: ApiServiceDispatchPlan,
    service_id: UUID,
    operation_key: str,
    handler: object,
    status: ServiceOperationStatus = ServiceOperationStatus.queued,
    result_info: str | None = None,
    execution_context: JsonObject | None = None,
    execution_backend: ServiceApiExecutionBackend | None = None,
    execution_backend_mode: ServiceApiExecutionBackendMode = ServiceApiExecutionBackendMode.auto,
    graph_gateway: ServiceGraphGateway | None = None,
    meta_temporal_graph_route: MetaTemporalGraphRoute | None = None,
    workspace_root: Path | None = None,
    service_name: str | None = None,
    service_package_id: UUID | None = None,
    service_package_name: str | None = None,
    lane_subscriptions: tuple[ServiceLaneSubscriptionBinding, ...] = (),
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...] = (),
    service_view_provider_routes: tuple[ServiceViewProviderRouteDescriptor, ...] = (),
    environment_commit_receipt_source: (
        ServiceEnvironmentCommitReceiptSource | None
    ) = None,
    experience_reference_branch_ids_by_experience_name: (
        Mapping[str, UUID] | None
    ) = None,
    invocation_context: JsonObject | None = None,
    ontology_replica_query: ServiceOntologyReplicaQueryProtocol | None = None,
    ontology_replica_orm_session: (
        ServiceOntologyReplicaOrmSessionProtocol | None
    ) = None,
    ontology_authority_package_names: tuple[str, ...] = (),
    ontology_authority_source_kind: str | None = None,
    ontology_authority_root: Path | None = None,
    execution_callback: LegacyServiceApiExecutionCallback | None = None,
    stream_requested: bool = False,
    stream_event_sink: ServiceApiStreamEventSink | None = None,
    settlement_coordinator: ServiceOperationSettlementCoordinator | None = None,
    economy_settlement_adapter: ServiceOperationEconomySettlementAdapter | None = None,
    operation_access_context: ServiceOperationAccessContext | None = None,
    actor_role_evidence: tuple[ServiceActorRoleEvidence, ...] = (),
    commit: bool = True,
    publish: bool = False,
    receipt_policy: ServiceApiDispatchReceiptPolicy = (
        ServiceApiDispatchReceiptPolicy.committed
    ),
) -> ExecutedServiceApiDispatch:
    """Execute one API-owned dispatch plan on the Service rail.

    Host-facing callers should pass an explicit execution backend or backend mode.
    The default auto-selection rail remains a lower-level convenience seam only.
    """
    trace_fields = {
        "endpoint_ref": dispatch_plan.endpoint_ref,
        "service_name": service_name,
        "operation_key": operation_key,
        "service_id": str(service_id),
    }
    execute_started_at = perf_counter()
    execute_child_duration_s = 0.0
    admission_context = normalize_service_operation_admission_context(
        invocation_context=invocation_context,
        legacy_actor_id=actor_id,
    )
    effective_actor_id = admission_context.effective_actor_id or actor_id
    effective_actor_role_evidence = (
        *actor_role_evidence,
        *service_actor_role_evidence_from_invocation_context(
            invocation_context=invocation_context,
        ),
    )
    phase_started_at = perf_counter()
    with service_api_trace_phase(
        "dispatch.resolve_service_api_dispatch",
        **trace_fields,
    ):
        resolved_dispatch = resolve_service_api_dispatch(
            session=session,
            dispatch_plan=dispatch_plan,
        )
    phase_duration_s = perf_counter() - phase_started_at
    execute_child_duration_s += phase_duration_s
    record_service_api_trace_timing(
        phase="dispatch.execute.resolve_service_api_dispatch",
        duration_s=phase_duration_s,
    )
    phase_started_at = perf_counter()
    with service_api_trace_phase(
        "dispatch.validate_service_api_preflight",
        **trace_fields,
    ):
        required_fulfillment_kind = _required_service_operation_fulfillment_kind(
            dispatch_plan=dispatch_plan,
            receipt_policy=receipt_policy,
            stream_requested=stream_requested,
            stream_event_sink=stream_event_sink,
        )
        preflight = validate_service_api_dispatch_preflight(
            session=session,
            resolved_dispatch=resolved_dispatch,
            service_id=service_id,
            actor_id=effective_actor_id,
            operation_access_context=operation_access_context,
            actor_role_evidence=effective_actor_role_evidence,
            admission_context=admission_context,
            operation_key=operation_key,
            request_hash=dispatch_plan.envelope.request_hash,
            required_fulfillment_kind=required_fulfillment_kind,
        )
    phase_duration_s = perf_counter() - phase_started_at
    execute_child_duration_s += phase_duration_s
    record_service_api_trace_timing(
        phase="dispatch.execute.validate_service_api_preflight",
        duration_s=phase_duration_s,
    )
    if receipt_policy is ServiceApiDispatchReceiptPolicy.read_model:
        phase_started_at = perf_counter()
        result = await _execute_service_api_read_model_dispatch_plan(
            runtime=runtime,
            index=index,
            session=session,
            actor_id=effective_actor_id,
            target_lane=target_lane,
            execution_target_lane=execution_target_lane,
            dispatch_plan=dispatch_plan,
            resolved_dispatch=resolved_dispatch,
            preflight=preflight,
            handler=handler,
            execution_backend_mode=execution_backend_mode,
            graph_gateway=graph_gateway,
            meta_temporal_graph_route=meta_temporal_graph_route,
            workspace_root=workspace_root,
            service_name=service_name,
            service_package_id=service_package_id,
            service_package_name=service_package_name,
            lane_subscriptions=lane_subscriptions,
            service_api_dependency_routes=service_api_dependency_routes,
            service_view_provider_routes=service_view_provider_routes,
            environment_commit_receipt_source=environment_commit_receipt_source,
            experience_reference_branch_ids_by_experience_name=(
                experience_reference_branch_ids_by_experience_name
            ),
            invocation_context=invocation_context,
            ontology_replica_query=ontology_replica_query,
            ontology_replica_orm_session=ontology_replica_orm_session,
            ontology_authority_package_names=ontology_authority_package_names,
            ontology_authority_source_kind=ontology_authority_source_kind,
            ontology_authority_root=ontology_authority_root,
            stream_requested=stream_requested,
            stream_event_sink=stream_event_sink,
            trace_fields=trace_fields,
            settlement_coordinator=settlement_coordinator,
            economy_settlement_adapter=economy_settlement_adapter,
        )
        phase_duration_s = perf_counter() - phase_started_at
        execute_child_duration_s += phase_duration_s
        record_service_api_trace_timing(
            phase="dispatch.execute.read_model_dispatch",
            duration_s=phase_duration_s,
        )
        _record_dispatch_execute_unattributed(
            started_at=execute_started_at,
            child_duration_s=execute_child_duration_s,
            phase="dispatch.execute",
        )
        return result
    effective_settlement_coordinator = settlement_coordinator
    if economy_settlement_adapter is not None:
        if settlement_coordinator is not None:
            raise ValueError(
                "execute_service_api_dispatch_plan accepts either settlement_coordinator or "
                "economy_settlement_adapter, not both"
            )
        effective_settlement_coordinator = (
            build_service_operation_economy_settlement_coordinator(
                adapter=economy_settlement_adapter,
                runtime=runtime,
                index=index,
                commit=commit,
                publish=publish,
            )
        )
    api_call_lane = MaterializationLaneContext(
        branch_id=dispatch_plan.envelope.branch_id,
        projection_hash=dispatch_plan.envelope.projection_hash,
    )
    if not _service_api_dispatch_requires_pre_execution_operation(
        dispatch_plan=dispatch_plan,
        stream_requested=stream_requested,
        stream_event_sink=stream_event_sink,
        settlement_coordinator=effective_settlement_coordinator,
    ):
        phase_started_at = perf_counter()
        result = await _execute_service_api_final_receipt_dispatch_plan(
            runtime=runtime,
            index=index,
            session=session,
            actor_id=effective_actor_id,
            target_lane=target_lane,
            api_call_lane=api_call_lane,
            api_source_lane=api_source_lane,
            execution_target_lane=execution_target_lane,
            dispatch_plan=dispatch_plan,
            resolved_dispatch=resolved_dispatch,
            preflight=preflight,
            handler=handler,
            service_id=service_id,
            operation_key=operation_key,
            execution_context=execution_context,
            execution_backend_mode=execution_backend_mode,
            graph_gateway=graph_gateway,
            meta_temporal_graph_route=meta_temporal_graph_route,
            workspace_root=workspace_root,
            service_name=service_name,
            service_package_id=service_package_id,
            service_package_name=service_package_name,
            lane_subscriptions=lane_subscriptions,
            service_api_dependency_routes=service_api_dependency_routes,
            service_view_provider_routes=service_view_provider_routes,
            environment_commit_receipt_source=environment_commit_receipt_source,
            experience_reference_branch_ids_by_experience_name=(
                experience_reference_branch_ids_by_experience_name
            ),
            invocation_context=invocation_context,
            ontology_replica_query=ontology_replica_query,
            ontology_replica_orm_session=ontology_replica_orm_session,
            ontology_authority_package_names=ontology_authority_package_names,
            ontology_authority_source_kind=ontology_authority_source_kind,
            ontology_authority_root=ontology_authority_root,
            trace_fields=trace_fields,
            commit=commit,
            publish=publish,
        )
        phase_duration_s = perf_counter() - phase_started_at
        execute_child_duration_s += phase_duration_s
        record_service_api_trace_timing(
            phase="dispatch.execute.final_receipt_dispatch",
            duration_s=phase_duration_s,
        )
        _record_dispatch_execute_unattributed(
            started_at=execute_started_at,
            child_duration_s=execute_child_duration_s,
            phase="dispatch.execute",
        )
        return result
    materialized_operation = await await_with_service_api_trace(
        materialize_service_operation(
            runtime=runtime,
            index=index,
            actor_id=effective_actor_id,
            target_lane=target_lane,
            resolved_dispatch=resolved_dispatch,
            service_id=service_id,
            operation_key=operation_key,
            status=status,
            result_info=result_info,
            execution_context=execution_context,
            service_config_session=session,
            commit=commit,
            publish=publish,
        ),
        phase="dispatch.materialize_service_operation",
        fields=trace_fields,
        branch_id=str(target_lane.branch_id),
        projection_hash=target_lane.projection_hash,
    )
    with service_api_trace_phase(
        "dispatch.validate_fulfillment_contract",
        **trace_fields,
    ):
        validated_fulfillment = validate_service_api_fulfillment_contract(
            session=session,
            resolved_dispatch=resolved_dispatch,
        )
    with service_api_trace_phase(
        "dispatch.build_graph_execution_plan",
        binding_count=len(validated_fulfillment.bindings),
        **trace_fields,
    ):
        fulfillment_execution_plan = build_service_api_graph_execution_plan(
            dispatch_plan=dispatch_plan,
            materialized_operation_binding=materialized_operation.binding,
            validated_fulfillment=validated_fulfillment,
        )
    with service_api_trace_phase(
        "dispatch.build_settlement_context",
        **trace_fields,
    ):
        settlement_context = build_service_operation_settlement_context(
            session=session,
            index=index,
            actor_id=effective_actor_id,
            service_lane=target_lane,
            api_call_lane=api_call_lane,
            resolved_dispatch=resolved_dispatch,
            service_id=service_id,
            service_operation_id=materialized_operation.binding.service_operation_id,
            service_operation_config_id=materialized_operation.binding.service_operation_config_id,
            service_api_endpoint_binding_id=materialized_operation.binding.api_endpoint_id,
            operation_key=operation_key,
            admission_context=admission_context,
            operation_policy=preflight.contract_admission.operation_policy,
            invocation_context=invocation_context,
        )
    execution_object = None
    prepared_settlement: object | None = None
    settlement_receipt: ServiceOperationSettlementReceiptRefs | None = None
    operation_context = _service_operation_context_for_lane(
        admission_context=admission_context,
        actor_id=effective_actor_id,
        lane=execution_target_lane or target_lane,
        operation_key=operation_key,
    )
    environment_context = _environment_operation_context_for_lane(
        admission_context=admission_context,
        actor_id=effective_actor_id,
        lane=execution_target_lane or target_lane,
    )
    operation_metering_context: ServiceOperationMeteringContextV1 | None = None
    if (
        effective_settlement_coordinator is not None
        and settlement_context.settlement_policy
        != ServiceOperationSettlementPolicy.none
    ):
        operation_metering_context = (
            await _resolve_service_operation_metering_context(
                coordinator=effective_settlement_coordinator,
                session=session,
                settlement_context=settlement_context,
            )
        )
    with service_api_host_context(
        operation_context=operation_context,
        environment_context=environment_context,
        workspace_root=workspace_root,
        graph_gateway=graph_gateway,
        meta_temporal_graph_route=meta_temporal_graph_route,
        service_name=service_name,
        service_package_id=service_package_id,
        service_package_name=service_package_name,
        lane_subscriptions=lane_subscriptions,
        service_api_dependency_routes=service_api_dependency_routes,
        environment_commit_receipt_source=environment_commit_receipt_source,
        experience_reference_branch_ids_by_experience_name=(
            experience_reference_branch_ids_by_experience_name
        ),
        invocation_context=invocation_context,
        operation_metering_context=operation_metering_context,
        ontology_replica_query=ontology_replica_query,
        ontology_replica_orm_session=ontology_replica_orm_session,
        ontology_authority_package_names=ontology_authority_package_names,
        ontology_authority_source_kind=ontology_authority_source_kind,
        ontology_authority_root=ontology_authority_root,
        materialization=ServiceApiMaterializationContext(
            runtime=runtime,
            graph_context=index,
            target_lane=execution_target_lane or target_lane,
        ),
    ):
        stream_task: asyncio.Task[None] | None = None

        try:
            if (
                effective_settlement_coordinator is not None
                and settlement_context.settlement_policy
                != ServiceOperationSettlementPolicy.none
            ):
                if settlement_context.metering_estimate is None:
                    metering_estimate = await _estimate_service_operation_metering(
                        handler=handler,
                        endpoint_ref=dispatch_plan.endpoint_ref,
                        request_object=dispatch_plan.request_object,
                    )
                    if metering_estimate is not None:
                        settlement_context = replace(
                            settlement_context,
                            metering_estimate=metering_estimate,
                        )
                prepared_settlement = (
                    await effective_settlement_coordinator.before_execute(
                        session=session,
                        preparation=ServiceOperationSettlementPreparation(
                            context=settlement_context,
                        ),
                    )
                )
            if dispatch_plan.build_execution is not None:
                with service_api_trace_phase(
                    "dispatch.build_execution_backend",
                    backend_mode=execution_backend_mode.value,
                    explicit_backend=execution_backend is not None,
                    **trace_fields,
                ):
                    resolved_execution_backend = (
                        execution_backend
                        or build_service_api_execution_backend(
                            execution_plan=fulfillment_execution_plan,
                            backend_mode=execution_backend_mode,
                            graph_context=index,
                            graph_gateway=graph_gateway,
                            operation_context=operation_context,
                            execution_callback=execution_callback,
                        )
                    )
                with service_api_trace_phase(
                    "dispatch.build_execution_object",
                    backend_type=resolved_execution_backend.__class__.__name__,
                    **trace_fields,
                ):
                    execution_object = dispatch_plan.build_execution(
                        resolved_execution_backend
                    )
            if stream_requested:
                if dispatch_plan.stream_invoke is None:
                    raise RuntimeError(
                        "Service API dispatch stream execution requires compiled stream_invoke support for "
                        f"endpoint_ref={dispatch_plan.endpoint_ref!r}."
                    )
                if stream_event_sink is None:
                    raise RuntimeError(
                        "Service API dispatch stream execution requires a stream_event_sink for "
                        f"endpoint_ref={dispatch_plan.endpoint_ref!r}."
                    )
                stream_iterator = dispatch_plan.stream_invoke(
                    handler,
                    dispatch_plan.request_object,
                    execution_object,
                )
                stream_task = asyncio.create_task(
                    _drain_stream_events(
                        stream_iterator=stream_iterator,
                        stream_event_sink=stream_event_sink,
                    )
                )
            response_object = await await_with_service_api_trace(
                dispatch_plan.invoke(
                    handler,
                    dispatch_plan.request_object,
                    execution_object,
                ),
                phase="dispatch.invoke_service_protocol",
                fields=trace_fields,
                backend_mode=execution_backend_mode.value,
            )
            if stream_task is not None:
                await await_with_service_api_trace(
                    stream_task,
                    phase="dispatch.drain_stream_events",
                    fields=trace_fields,
                )
        except Exception as exc:
            if stream_task is not None:
                stream_task.cancel()
                await asyncio.gather(stream_task, return_exceptions=True)
            failed_operation = await materialize_service_operation_status(
                runtime=runtime,
                index=index,
                actor_id=effective_actor_id,
                target_lane=target_lane,
                binding=materialized_operation.binding,
                status=ServiceOperationStatus.failed,
                result_info=str(exc),
                service_config_session=session,
                commit=commit,
                publish=publish,
            )
            with collect_api_invocation_trace_timings() as api_outcome_timings:
                failed_api_call_outcome = await await_with_service_api_trace(
                    materialize_api_call_outcome(
                        runtime=runtime,
                        index=index,
                        actor_id=effective_actor_id,
                        target_lane=api_call_lane,
                        api_source_lane=api_source_lane,
                        api_call_id=dispatch_plan.envelope.api_call_id,
                        api_call_hint=_api_call_hint_from_dispatch_envelope(
                            dispatch_plan.envelope
                        ),
                        status=ApiCallOutcomeStatus.failed,
                        error=str(exc),
                        response_payload=None,
                        commit=commit,
                        publish=publish,
                    ),
                    phase="dispatch.materialize_api_call_outcome",
                    fields=trace_fields,
                    status=ApiCallOutcomeStatus.failed.value,
                    api_call_id=str(dispatch_plan.envelope.api_call_id),
                    branch_id=str(api_call_lane.branch_id),
                    projection_hash=api_call_lane.projection_hash,
                )
            _record_api_call_outcome_trace_timings_for_servicehost(
                timings=api_outcome_timings,
            )
            if (
                effective_settlement_coordinator is not None
                and settlement_context.settlement_policy
                == ServiceOperationSettlementPolicy.reserve_and_finalize
            ):
                await effective_settlement_coordinator.after_execute(
                    session=session,
                    prepared_state=prepared_settlement,
                    finalization=ServiceOperationSettlementFinalization(
                        context=settlement_context,
                        service_operation_status=failed_operation.service_operation.status,
                        result_info=failed_operation.service_operation.result_info,
                        api_call_outcome_id=failed_api_call_outcome.binding.api_call_outcome_id,
                        api_call_outcome_ref=failed_api_call_outcome.api_call_outcome,
                        api_call_outcome_status=failed_api_call_outcome.api_call_outcome.status,
                        api_call_outcome_response_model_id=failed_api_call_outcome.binding.response_model_id,
                        api_call_outcome_error=failed_api_call_outcome.api_call_outcome.error,
                        metering_receipt=None,
                    ),
                )
            raise
    updated_operation = await await_with_service_api_trace(
        materialize_service_operation_status(
            runtime=runtime,
            index=index,
            actor_id=effective_actor_id,
            target_lane=target_lane,
            binding=materialized_operation.binding,
            status=ServiceOperationStatus.succeeded,
            result_info=None,
            service_config_session=session,
            commit=commit,
            publish=publish,
        ),
        phase="dispatch.materialize_service_operation_status",
        fields=trace_fields,
        status=ServiceOperationStatus.succeeded.value,
    )
    with collect_api_invocation_trace_timings() as api_outcome_timings:
        recorded_api_call_outcome = await await_with_service_api_trace(
            materialize_api_call_outcome(
                runtime=runtime,
                index=index,
                actor_id=effective_actor_id,
                target_lane=api_call_lane,
                api_source_lane=api_source_lane,
                api_call_id=dispatch_plan.envelope.api_call_id,
                api_call_hint=_api_call_hint_from_dispatch_envelope(
                    dispatch_plan.envelope
                ),
                status=ApiCallOutcomeStatus.succeeded,
                error=None,
                response_payload=_coerce_api_call_outcome_payload(response_object),
                response_class_config=_resolve_api_call_outcome_response_class_config(
                    index=index,
                    response_type_ref=dispatch_plan.response_type_ref,
                ),
                commit=commit,
                publish=publish,
            ),
            phase="dispatch.materialize_api_call_outcome",
            fields=trace_fields,
            status=ApiCallOutcomeStatus.succeeded.value,
            api_call_id=str(dispatch_plan.envelope.api_call_id),
            branch_id=str(api_call_lane.branch_id),
            projection_hash=api_call_lane.projection_hash,
        )
    _record_api_call_outcome_trace_timings_for_servicehost(
        timings=api_outcome_timings,
    )
    if (
        effective_settlement_coordinator is not None
        and settlement_context.settlement_policy
        == ServiceOperationSettlementPolicy.reserve_and_finalize
    ):
        settlement_receipt = await effective_settlement_coordinator.after_execute(
            session=session,
            prepared_state=prepared_settlement,
            finalization=ServiceOperationSettlementFinalization(
                context=settlement_context,
                service_operation_status=updated_operation.service_operation.status,
                result_info=updated_operation.service_operation.result_info,
                api_call_outcome_id=recorded_api_call_outcome.binding.api_call_outcome_id,
                api_call_outcome_ref=recorded_api_call_outcome.api_call_outcome,
                api_call_outcome_status=recorded_api_call_outcome.api_call_outcome.status,
                api_call_outcome_response_model_id=recorded_api_call_outcome.binding.response_model_id,
                api_call_outcome_error=recorded_api_call_outcome.api_call_outcome.error,
                metering_receipt=extract_service_operation_metering_receipt(
                    response_object
                ),
            ),
        )
    return ExecutedServiceApiDispatch(
        resolved_dispatch=resolved_dispatch,
        preflight=preflight,
        materialized_operation=materialized_operation,
        updated_operation=updated_operation,
        recorded_api_call_outcome=recorded_api_call_outcome,
        validated_fulfillment=validated_fulfillment,
        fulfillment_execution_plan=fulfillment_execution_plan,
        execution_object=execution_object,
        response_object=response_object,
        settlement_receipt=settlement_receipt,
    )


async def _execute_service_api_read_model_dispatch_plan(
    *,
    runtime: object,
    index: object,
    session: Session,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    execution_target_lane: MaterializationLaneContext | None,
    dispatch_plan: ApiServiceDispatchPlan,
    resolved_dispatch: ResolvedServiceApiDispatch,
    preflight: ServiceApiDispatchPreflightResult,
    handler: object,
    execution_backend_mode: ServiceApiExecutionBackendMode,
    graph_gateway: ServiceGraphGateway | None,
    meta_temporal_graph_route: MetaTemporalGraphRoute | None,
    workspace_root: Path | None,
    service_name: str | None,
    service_package_id: UUID | None,
    service_package_name: str | None,
    lane_subscriptions: tuple[ServiceLaneSubscriptionBinding, ...],
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...],
    service_view_provider_routes: tuple[ServiceViewProviderRouteDescriptor, ...],
    environment_commit_receipt_source: ServiceEnvironmentCommitReceiptSource | None,
    experience_reference_branch_ids_by_experience_name: Mapping[str, UUID] | None,
    invocation_context: JsonObject | None,
    ontology_replica_query: ServiceOntologyReplicaQueryProtocol | None,
    ontology_replica_orm_session: ServiceOntologyReplicaOrmSessionProtocol | None,
    ontology_authority_package_names: tuple[str, ...],
    ontology_authority_source_kind: str | None,
    ontology_authority_root: Path | None,
    stream_requested: bool,
    stream_event_sink: ServiceApiStreamEventSink | None,
    trace_fields: Mapping[str, object],
    settlement_coordinator: ServiceOperationSettlementCoordinator | None,
    economy_settlement_adapter: ServiceOperationEconomySettlementAdapter | None,
) -> ExecutedServiceApiDispatch:
    if stream_requested or stream_event_sink is not None:
        raise RuntimeError(
            "Service API read-model dispatch does not support streaming endpoints: "
            f"endpoint_ref={dispatch_plan.endpoint_ref!r}"
        )
    if settlement_coordinator is not None or economy_settlement_adapter is not None:
        raise RuntimeError(
            "Service API read-model dispatch cannot use settlement coordinators: "
            f"endpoint_ref={dispatch_plan.endpoint_ref!r}"
        )
    if dispatch_plan.fulfillment_bindings:
        raise RuntimeError(
            "Service API read-model dispatch v0 supports endpoint-only service handlers. "
            "Graph fulfillment endpoints must use committed receipts: "
            f"endpoint_ref={dispatch_plan.endpoint_ref!r}"
        )
    if dispatch_plan.build_execution is not None:
        raise RuntimeError(
            "Service API read-model dispatch v0 does not build graph execution backends. "
            "Execution-backed endpoints must use committed receipts: "
            f"endpoint_ref={dispatch_plan.endpoint_ref!r}"
        )

    with service_api_trace_phase(
        "dispatch.validate_fulfillment_contract",
        receipt_policy=ServiceApiDispatchReceiptPolicy.read_model.value,
        **trace_fields,
    ):
        validated_fulfillment = validate_service_api_fulfillment_contract(
            session=session,
            resolved_dispatch=resolved_dispatch,
        )

    with service_api_trace_phase(
        "dispatch.read_model.prepare_contexts",
        receipt_policy=ServiceApiDispatchReceiptPolicy.read_model.value,
        **trace_fields,
    ):
        admission_context = normalize_service_operation_admission_context(
            invocation_context=invocation_context,
            legacy_actor_id=actor_id,
        )
        operation_context = _service_operation_context_for_lane(
            admission_context=admission_context,
            actor_id=actor_id,
            lane=execution_target_lane or target_lane,
            operation_key=dispatch_plan.endpoint_ref,
        )
        environment_context = _environment_operation_context_for_lane(
            admission_context=admission_context,
            actor_id=actor_id,
            lane=execution_target_lane or target_lane,
        )
        materialization_context = ServiceApiMaterializationContext(
            runtime=runtime,
            graph_context=index,
            target_lane=execution_target_lane or target_lane,
        )
    with service_api_host_context(
        operation_context=operation_context,
        environment_context=environment_context,
        workspace_root=workspace_root,
        graph_gateway=graph_gateway,
        meta_temporal_graph_route=meta_temporal_graph_route,
        service_name=service_name,
        service_package_id=service_package_id,
        service_package_name=service_package_name,
        lane_subscriptions=lane_subscriptions,
        service_api_dependency_routes=service_api_dependency_routes,
        service_view_provider_routes=service_view_provider_routes,
        environment_commit_receipt_source=environment_commit_receipt_source,
        experience_reference_branch_ids_by_experience_name=(
            experience_reference_branch_ids_by_experience_name
        ),
        invocation_context=invocation_context,
        ontology_replica_query=ontology_replica_query,
        ontology_replica_orm_session=ontology_replica_orm_session,
        ontology_authority_package_names=ontology_authority_package_names,
        ontology_authority_source_kind=ontology_authority_source_kind,
        ontology_authority_root=ontology_authority_root,
        materialization=materialization_context,
    ):
        response_object = await await_with_service_api_trace(
            dispatch_plan.invoke(
                handler,
                dispatch_plan.request_object,
                None,
            ),
            phase="dispatch.invoke_service_protocol",
            fields=trace_fields,
            backend_mode=execution_backend_mode.value,
            receipt_policy=ServiceApiDispatchReceiptPolicy.read_model.value,
        )

    return ExecutedServiceApiDispatch(
        resolved_dispatch=resolved_dispatch,
        preflight=preflight,
        materialized_operation=None,
        updated_operation=None,
        recorded_api_call_outcome=None,
        validated_fulfillment=validated_fulfillment,
        fulfillment_execution_plan=None,
        execution_object=None,
        response_object=response_object,
        receipt_policy=ServiceApiDispatchReceiptPolicy.read_model,
    )


def _service_api_dispatch_requires_pre_execution_operation(
    *,
    dispatch_plan: ApiServiceDispatchPlan,
    stream_requested: bool,
    stream_event_sink: ServiceApiStreamEventSink | None,
    settlement_coordinator: ServiceOperationSettlementCoordinator | None,
) -> bool:
    """Return whether a committed dispatch needs a durable operation before invoke."""

    return bool(
        dispatch_plan.fulfillment_bindings
        or dispatch_plan.build_execution is not None
        or stream_requested
        or stream_event_sink is not None
        or settlement_coordinator is not None
    )


def _required_service_operation_fulfillment_kind(
    *,
    dispatch_plan: ApiServiceDispatchPlan,
    receipt_policy: ServiceApiDispatchReceiptPolicy,
    stream_requested: bool,
    stream_event_sink: ServiceApiStreamEventSink | None,
) -> ServiceOperationFulfillmentKind | None:
    if receipt_policy is ServiceApiDispatchReceiptPolicy.read_model:
        return ServiceOperationFulfillmentKind.view
    if dispatch_plan.fulfillment_bindings or dispatch_plan.build_execution is not None:
        return ServiceOperationFulfillmentKind.coordination
    if stream_requested or stream_event_sink is not None:
        return ServiceOperationFulfillmentKind.actuation
    return None


async def _execute_service_api_final_receipt_dispatch_plan(
    *,
    runtime: object,
    index: object,
    session: Session,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    api_call_lane: MaterializationLaneContext,
    api_source_lane: MaterializationLaneContext | None,
    execution_target_lane: MaterializationLaneContext | None,
    dispatch_plan: ApiServiceDispatchPlan,
    resolved_dispatch: ResolvedServiceApiDispatch,
    preflight: ServiceApiDispatchPreflightResult,
    handler: object,
    service_id: UUID,
    operation_key: str,
    execution_context: JsonObject | None,
    execution_backend_mode: ServiceApiExecutionBackendMode,
    graph_gateway: ServiceGraphGateway | None,
    meta_temporal_graph_route: MetaTemporalGraphRoute | None,
    workspace_root: Path | None,
    service_name: str | None,
    service_package_id: UUID | None,
    service_package_name: str | None,
    lane_subscriptions: tuple[ServiceLaneSubscriptionBinding, ...],
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...],
    service_view_provider_routes: tuple[ServiceViewProviderRouteDescriptor, ...],
    environment_commit_receipt_source: ServiceEnvironmentCommitReceiptSource | None,
    experience_reference_branch_ids_by_experience_name: Mapping[str, UUID] | None,
    invocation_context: JsonObject | None,
    ontology_replica_query: ServiceOntologyReplicaQueryProtocol | None,
    ontology_replica_orm_session: ServiceOntologyReplicaOrmSessionProtocol | None,
    ontology_authority_package_names: tuple[str, ...],
    ontology_authority_source_kind: str | None,
    ontology_authority_root: Path | None,
    trace_fields: Mapping[str, object],
    commit: bool,
    publish: bool,
) -> ExecutedServiceApiDispatch:
    """Execute endpoint-only committed dispatches with one final ServiceOperation receipt."""

    execute_started_at = perf_counter()
    execute_child_duration_s = 0.0
    phase_started_at = perf_counter()
    with service_api_trace_phase(
        "dispatch.validate_fulfillment_contract",
        receipt_strategy="final_only",
        **trace_fields,
    ):
        validated_fulfillment = validate_service_api_fulfillment_contract(
            session=session,
            resolved_dispatch=resolved_dispatch,
        )
    if validated_fulfillment.bindings:
        raise RuntimeError(
            "Final-only Service API receipts require endpoint-only fulfillment: "
            f"endpoint_ref={dispatch_plan.endpoint_ref!r}"
        )
    phase_duration_s = perf_counter() - phase_started_at
    execute_child_duration_s += phase_duration_s
    record_service_api_trace_timing(
        phase="dispatch.final_receipt.validate_fulfillment_contract",
        duration_s=phase_duration_s,
    )

    admission_context = normalize_service_operation_admission_context(
        invocation_context=invocation_context,
        legacy_actor_id=actor_id,
    )
    operation_context = _service_operation_context_for_lane(
        admission_context=admission_context,
        actor_id=actor_id,
        lane=execution_target_lane or target_lane,
        operation_key=operation_key,
    )
    environment_context = _environment_operation_context_for_lane(
        admission_context=admission_context,
        actor_id=actor_id,
        lane=execution_target_lane or target_lane,
    )
    response_object: object | None = None
    try:
        phase_started_at = perf_counter()
        with service_api_trace_phase(
            "dispatch.final_receipt.host_context",
            receipt_strategy="final_only",
            **trace_fields,
        ):
            with service_api_host_context(
                operation_context=operation_context,
                environment_context=environment_context,
                workspace_root=workspace_root,
                graph_gateway=graph_gateway,
                meta_temporal_graph_route=meta_temporal_graph_route,
                service_name=service_name,
                service_package_id=service_package_id,
                service_package_name=service_package_name,
                lane_subscriptions=lane_subscriptions,
                service_api_dependency_routes=service_api_dependency_routes,
                service_view_provider_routes=service_view_provider_routes,
                environment_commit_receipt_source=environment_commit_receipt_source,
                experience_reference_branch_ids_by_experience_name=(
                    experience_reference_branch_ids_by_experience_name
                ),
                invocation_context=invocation_context,
                ontology_replica_query=ontology_replica_query,
                ontology_replica_orm_session=ontology_replica_orm_session,
                ontology_authority_package_names=ontology_authority_package_names,
                ontology_authority_source_kind=ontology_authority_source_kind,
                ontology_authority_root=ontology_authority_root,
                materialization=ServiceApiMaterializationContext(
                    runtime=runtime,
                    graph_context=index,
                    target_lane=execution_target_lane or target_lane,
                ),
            ):
                response_object = await await_with_service_api_trace(
                    dispatch_plan.invoke(
                        handler,
                        dispatch_plan.request_object,
                        None,
                    ),
                    phase="dispatch.invoke_service_protocol",
                    fields=trace_fields,
                    backend_mode=execution_backend_mode.value,
                    receipt_strategy="final_only",
                )
        execute_child_duration_s += perf_counter() - phase_started_at
    except Exception as exc:
        phase_started_at = perf_counter()
        failed_operation = await await_with_service_api_trace(
            materialize_service_operation(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                target_lane=target_lane,
                resolved_dispatch=resolved_dispatch,
                service_id=service_id,
                operation_key=operation_key,
                status=ServiceOperationStatus.failed,
                result_info=str(exc),
                execution_context=execution_context,
                service_config_session=session,
                commit=commit,
                publish=publish,
            ),
            phase="dispatch.materialize_service_operation",
            fields=trace_fields,
            status=ServiceOperationStatus.failed.value,
            receipt_strategy="final_only",
        )
        phase_duration_s = perf_counter() - phase_started_at
        execute_child_duration_s += phase_duration_s
        record_service_api_trace_timing(
            phase="dispatch.final_receipt.materialize_failed_service_operation",
            duration_s=phase_duration_s,
        )
        phase_started_at = perf_counter()
        with collect_api_invocation_trace_timings() as api_outcome_timings:
            await await_with_service_api_trace(
                materialize_api_call_outcome(
                    runtime=runtime,
                    index=index,
                    actor_id=actor_id,
                    target_lane=api_call_lane,
                    api_source_lane=api_source_lane,
                    api_call_id=dispatch_plan.envelope.api_call_id,
                    api_call_hint=_api_call_hint_from_dispatch_envelope(
                        dispatch_plan.envelope
                    ),
                    status=ApiCallOutcomeStatus.failed,
                    error=str(exc),
                    response_payload=None,
                    api_call_deferred=bool(
                        getattr(dispatch_plan.envelope, "deferred_api_call", False)
                    ),
                    commit=commit,
                    publish=publish,
                ),
                phase="dispatch.materialize_api_call_outcome",
                fields=trace_fields,
                status=ApiCallOutcomeStatus.failed.value,
                api_call_id=str(dispatch_plan.envelope.api_call_id),
                branch_id=str(api_call_lane.branch_id),
                projection_hash=api_call_lane.projection_hash,
                receipt_strategy="final_only",
            ),
        _record_api_call_outcome_trace_timings_for_servicehost(
            timings=api_outcome_timings,
        )
        phase_duration_s = perf_counter() - phase_started_at
        execute_child_duration_s += phase_duration_s
        record_service_api_trace_timing(
            phase="dispatch.final_receipt.materialize_failed_api_call_outcome",
            duration_s=phase_duration_s,
        )
        _record_dispatch_execute_unattributed(
            started_at=execute_started_at,
            child_duration_s=execute_child_duration_s,
            phase="dispatch.final_receipt",
        )
        _ = failed_operation
        raise

    phase_started_at = perf_counter()
    materialized_operation = await await_with_service_api_trace(
        materialize_service_operation(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            target_lane=target_lane,
            resolved_dispatch=resolved_dispatch,
            service_id=service_id,
            operation_key=operation_key,
            status=ServiceOperationStatus.succeeded,
            result_info=None,
            execution_context=execution_context,
            service_config_session=session,
            hydrate_committed_operation=False,
            commit=commit,
            publish=publish,
        ),
        phase="dispatch.materialize_service_operation",
        fields=trace_fields,
        status=ServiceOperationStatus.succeeded.value,
        receipt_strategy="final_only",
    )
    phase_duration_s = perf_counter() - phase_started_at
    execute_child_duration_s += phase_duration_s
    record_service_api_trace_timing(
        phase="dispatch.final_receipt.materialize_service_operation",
        duration_s=phase_duration_s,
    )
    updated_operation = ServiceOperationStatusUpdateResult(
        binding=materialized_operation.binding,
        service_operation=materialized_operation.service_operation,
    )
    phase_started_at = perf_counter()
    with collect_api_invocation_trace_timings() as api_outcome_timings:
        recorded_api_call_outcome = await await_with_service_api_trace(
            materialize_api_call_outcome(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                target_lane=api_call_lane,
                api_source_lane=api_source_lane,
                api_call_id=dispatch_plan.envelope.api_call_id,
                api_call_hint=_api_call_hint_from_dispatch_envelope(
                    dispatch_plan.envelope
                ),
                status=ApiCallOutcomeStatus.succeeded,
                error=None,
                response_payload=_coerce_api_call_outcome_payload(response_object),
                response_class_config=_resolve_api_call_outcome_response_class_config(
                    index=index,
                    response_type_ref=dispatch_plan.response_type_ref,
                ),
                api_call_deferred=bool(
                    getattr(dispatch_plan.envelope, "deferred_api_call", False)
                ),
                commit=commit,
                publish=publish,
            ),
            phase="dispatch.materialize_api_call_outcome",
            fields=trace_fields,
            status=ApiCallOutcomeStatus.succeeded.value,
            api_call_id=str(dispatch_plan.envelope.api_call_id),
            branch_id=str(api_call_lane.branch_id),
            projection_hash=api_call_lane.projection_hash,
            receipt_strategy="final_only",
        )
    _record_api_call_outcome_trace_timings_for_servicehost(
        timings=api_outcome_timings,
    )
    phase_duration_s = perf_counter() - phase_started_at
    execute_child_duration_s += phase_duration_s
    record_service_api_trace_timing(
        phase="dispatch.final_receipt.materialize_api_call_outcome",
        duration_s=phase_duration_s,
    )
    _record_dispatch_execute_unattributed(
        started_at=execute_started_at,
        child_duration_s=execute_child_duration_s,
        phase="dispatch.final_receipt",
    )
    return ExecutedServiceApiDispatch(
        resolved_dispatch=resolved_dispatch,
        preflight=preflight,
        materialized_operation=materialized_operation,
        updated_operation=updated_operation,
        recorded_api_call_outcome=recorded_api_call_outcome,
        validated_fulfillment=validated_fulfillment,
        fulfillment_execution_plan=None,
        execution_object=None,
        response_object=response_object,
    )


def validate_service_api_dispatch_preflight(
    *,
    session: Session,
    resolved_dispatch: ResolvedServiceApiDispatch,
    service_id: UUID,
    actor_id: UUID | None,
    operation_access_context: ServiceOperationAccessContext | None = None,
    actor_role_evidence: tuple[ServiceActorRoleEvidence, ...] = (),
    admission_context: ServiceOperationAdmissionContext | None = None,
    contract_access_resolution: ServiceContractAccessContextResolution | None = None,
    operation_key: str | None = None,
    request_hash: str | None = None,
    required_fulfillment_kind: ServiceOperationFulfillmentKind | None = None,
) -> ServiceApiDispatchPreflightResult:
    candidate = require_single_service_api_dispatch_candidate(
        resolved_dispatch=resolved_dispatch,
    )
    service_operation_fulfillment_kind = _validate_service_operation_fulfillment_kind(
        session=session,
        service_operation_config_id=candidate.service_operation_config_id,
        required_fulfillment_kind=required_fulfillment_kind,
        endpoint_ref=resolved_dispatch.dispatch_plan.endpoint_ref,
    )
    operation_preflight = validate_service_operation_preflight(
        session=session,
        service_id=service_id,
        service_operation_config_id=candidate.service_operation_config_id,
        actor_id=actor_id,
        operation_access_context=operation_access_context,
        actor_role_evidence=actor_role_evidence,
        admission_context=admission_context,
        contract_access_resolution=contract_access_resolution,
        operation_key=operation_key,
        request_hash=request_hash,
    )
    return ServiceApiDispatchPreflightResult(
        candidate=candidate,
        access_evidence=operation_preflight.access_evidence,
        actor_role_evidence=operation_preflight.actor_role_evidence,
        contract_admission=operation_preflight.contract_admission,
        service_operation_fulfillment_kind=service_operation_fulfillment_kind,
        required_fulfillment_kind=required_fulfillment_kind,
    )


def _validate_service_operation_fulfillment_kind(
    *,
    session: Session,
    service_operation_config_id: UUID,
    required_fulfillment_kind: ServiceOperationFulfillmentKind | None,
    endpoint_ref: str,
) -> ServiceOperationFulfillmentKind:
    service_operation_config = session.imap_get(
        ServiceOperationConfig,
        service_operation_config_id,
    )
    actual = _coerce_service_operation_fulfillment_kind(
        getattr(
            service_operation_config,
            "fulfillment_kind",
            ServiceOperationFulfillmentKind.coordination,
        ),
        service_operation_config_id=service_operation_config_id,
    )
    if (
        required_fulfillment_kind is not None
        and actual is not required_fulfillment_kind
    ):
        raise RuntimeError(
            "Service API dispatch rejected incompatible ServiceOperationConfig.fulfillment_kind: "
            + f"endpoint_ref={endpoint_ref!r} "
            + f"service_operation_config_id={service_operation_config_id} "
            + f"actual={actual.value!r} required={required_fulfillment_kind.value!r}"
        )
    return actual


def _coerce_service_operation_fulfillment_kind(
    value: object,
    *,
    service_operation_config_id: UUID,
) -> ServiceOperationFulfillmentKind:
    if isinstance(value, ServiceOperationFulfillmentKind):
        return value
    if value is None:
        return ServiceOperationFulfillmentKind.coordination
    if hasattr(value, "value"):
        value = getattr(value, "value")
    try:
        return ServiceOperationFulfillmentKind(str(value))
    except ValueError as exc:
        raise RuntimeError(
            "ServiceOperationConfig has unsupported fulfillment_kind: "
            + f"service_operation_config_id={service_operation_config_id} "
            + f"fulfillment_kind={value!r}"
        ) from exc


def read_service_operation_contract_admission(
    *,
    session: Session,
    service_id: UUID,
    service_operation_config_id: UUID,
    actor_id: UUID | None,
    operation_access_context: ServiceOperationAccessContext | None = None,
    actor_role_evidence: tuple[ServiceActorRoleEvidence, ...] = (),
    admission_context: ServiceOperationAdmissionContext | None = None,
    contract_access_resolution: ServiceContractAccessContextResolution | None = None,
    operation_key: str | None = None,
    request_hash: str | None = None,
) -> ServiceOperationContractAdmissionReadModel:
    effective_actor_id = (
        admission_context.effective_actor_id
        if admission_context is not None
        and admission_context.effective_actor_id is not None
        else actor_id
    )
    service_operation_config = session.imap_get(
        ServiceOperationConfig,
        service_operation_config_id,
    )
    admission_requirements = _read_service_operation_admission_requirements(
        service_operation_config=service_operation_config,
    )
    effective_operation_access_context = operation_access_context
    effective_contract_access_resolution = contract_access_resolution
    if (
        effective_operation_access_context is None
        and effective_contract_access_resolution is None
        and (
            admission_requirements.contract_context_required
            or (
                admission_context is not None
                and admission_context.contract_access_context_ref is not None
            )
        )
    ):
        resolved_contract_access = (
            resolve_service_contract_access_context_from_admission(
                session=session,
                admission_context=admission_context,
            )
        )
        effective_operation_access_context = resolved_contract_access.access_context
        effective_contract_access_resolution = resolved_contract_access.resolution
    access_evidence = _read_operation_access_preflight(
        operation_access_context=effective_operation_access_context,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
    )
    operation_policy = _read_operation_policy_summary(
        operation_access_context=effective_operation_access_context,
        access_evidence=access_evidence,
    )
    role_evidence, role_requirements, role_blockers = _read_actor_role_preflight(
        session=session,
        actor_id=effective_actor_id,
        service_operation_config_id=service_operation_config_id,
        actor_role_evidence=actor_role_evidence,
    )
    blocking_reasons: list[str] = []
    if (
        admission_requirements.contract_context_required
        and effective_operation_access_context is None
    ):
        blocking_reasons.append("missing_contract_access_context")
    if access_evidence is not None and not access_evidence.access_granted:
        blocking_reasons.append(access_evidence.reason.value)
    blocking_reasons.extend(role_blockers)
    participant_blockers = (
        service_participant_admission_blocking_reasons(
            admission_context.participant_admission
        )
        if admission_context is not None
        else ()
    )
    if admission_requirements.actor_context_required and participant_blockers:
        blocking_reasons.extend(participant_blockers)
    if (
        admission_requirements.actor_context_required
        and effective_actor_id is None
        and not participant_blockers
    ):
        blocking_reasons.append("missing_actor_id")
    if (
        admission_requirements.permit_required
        and access_evidence is not None
        and access_evidence.access_granted
        and (operation_policy is None or operation_policy.permit is None)
    ):
        blocking_reasons.append("missing_permit_policy")
    permit_policy = operation_policy.permit if operation_policy is not None else None
    if (
        admission_requirements.permit_required
        and permit_policy is not None
        and permit_policy.requires_smart_contract_permit
    ):
        authorization = (
            admission_context.operation_authorization_ref
            if admission_context is not None
            else None
        )
        if authorization is None:
            blocking_reasons.append("missing_operation_authorization")
        else:
            if authorization.service_contract_id is None:
                blocking_reasons.append("missing_authorization_service_contract_id")
            if authorization.permit_id is None:
                blocking_reasons.append("missing_authorization_permit_id")
            if (
                operation_key is not None
                and authorization.operation_key != operation_key
            ):
                blocking_reasons.append("authorization_operation_mismatch")
            if request_hash is not None and authorization.request_hash != request_hash:
                blocking_reasons.append("authorization_request_hash_mismatch")
            if (
                access_evidence is not None
                and access_evidence.service_contract_id is not None
                and authorization.service_contract_id
                != access_evidence.service_contract_id
            ):
                blocking_reasons.append("authorization_service_contract_mismatch")
    if (
        admission_requirements.settlement_required
        and access_evidence is not None
        and access_evidence.access_granted
        and (operation_policy is None or operation_policy.price is None)
    ):
        blocking_reasons.append("missing_price_policy")
    blocking_reasons = list(dict.fromkeys(blocking_reasons))
    allowed = not blocking_reasons
    return ServiceOperationContractAdmissionReadModel(
        schema="aware.service.contract_admission.read_model.v0",
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        actor_id=effective_actor_id,
        admission_mode=admission_requirements.admission_mode,
        status="allowed" if allowed else "denied",
        allowed=allowed,
        blocking_reasons=tuple(blocking_reasons),
        next_action=_contract_admission_next_action(blocking_reasons),
        contract_context_required=admission_requirements.contract_context_required,
        actor_context_required=admission_requirements.actor_context_required,
        permit_required=admission_requirements.permit_required,
        settlement_required=admission_requirements.settlement_required,
        access_evidence=access_evidence,
        actor_role_evidence=role_evidence,
        actor_role_requirements=role_requirements,
        operation_policy=operation_policy,
        admission_context=admission_context,
        contract_access_resolution=effective_contract_access_resolution,
    )


def validate_service_operation_preflight(
    *,
    session: Session,
    service_id: UUID,
    service_operation_config_id: UUID,
    actor_id: UUID | None,
    operation_access_context: ServiceOperationAccessContext | None = None,
    actor_role_evidence: tuple[ServiceActorRoleEvidence, ...] = (),
    admission_context: ServiceOperationAdmissionContext | None = None,
    contract_access_resolution: ServiceContractAccessContextResolution | None = None,
    operation_key: str | None = None,
    request_hash: str | None = None,
) -> ServiceOperationPreflightResult:
    admission = read_service_operation_contract_admission(
        session=session,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        actor_id=actor_id,
        operation_access_context=operation_access_context,
        actor_role_evidence=actor_role_evidence,
        admission_context=admission_context,
        contract_access_resolution=contract_access_resolution,
        operation_key=operation_key,
        request_hash=request_hash,
    )
    _raise_for_contract_admission_denial(
        admission=admission,
    )
    assert admission.allowed
    accepted_actor_role_evidence = _validate_actor_role_preflight(
        session=session,
        actor_id=admission.actor_id,
        service_operation_config_id=service_operation_config_id,
        actor_role_evidence=actor_role_evidence,
    )
    return ServiceOperationPreflightResult(
        service_operation_config_id=service_operation_config_id,
        access_evidence=admission.access_evidence,
        actor_role_evidence=accepted_actor_role_evidence,
        contract_admission=admission,
    )


def service_actor_role_evidence_from_invocation_context(
    *,
    invocation_context: Mapping[str, object] | None,
) -> tuple[ServiceActorRoleEvidence, ...]:
    root = _object_mapping(invocation_context)
    if not root:
        return ()
    source = (
        _first_mapping(
            root,
            ("service_operation_admission_context", "service_admission_context"),
        )
        or root
    )
    raw_items = _first_sequence(
        source,
        (
            "service_actor_role_evidence",
            "actor_role_evidence",
            "service_actor_role_evidences",
        ),
    )
    evidence_items: list[ServiceActorRoleEvidence] = []
    for raw_item in raw_items:
        payload = _object_mapping(raw_item)
        role_config_id = _optional_uuid(payload.get("role_config_id"))
        if role_config_id is None:
            continue
        evidence_items.append(
            ServiceActorRoleEvidence(
                role_config_id=role_config_id,
                actor_id=_optional_uuid(payload.get("actor_id")),
                access_scope=_optional_text(payload.get("access_scope")) or "operation",
                scope_kind=_optional_text(payload.get("scope_kind")) or "operation",
                scope_ref=_optional_text(payload.get("scope_ref")) or "default",
                class_instance_identity_id=_optional_uuid(
                    payload.get("class_instance_identity_id")
                ),
                role_assignment_binding_id=_optional_uuid(
                    payload.get("role_assignment_binding_id")
                ),
                granted=bool(payload.get("granted", True)),
            )
        )
    return tuple(evidence_items)


def _first_mapping(
    source: Mapping[str, object],
    keys: Sequence[str],
) -> Mapping[str, object] | None:
    for key in keys:
        nested = _object_mapping(source.get(key))
        if nested:
            return nested
    return None


def _first_sequence(
    source: Mapping[str, object],
    keys: Sequence[str],
) -> tuple[object, ...]:
    for key in keys:
        items = _sequence(source.get(key))
        if items:
            return items
    return ()


def _object_mapping(value: object) -> Mapping[str, object]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        return {str(key): item for key, item in mapping.items()}
    return {}


def _sequence(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_uuid(value: object) -> UUID | None:
    if value is None or value == "":
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _read_service_operation_admission_requirements(
    *,
    service_operation_config: ServiceOperationConfig | None,
) -> ServiceOperationAdmissionRequirements:
    admission_mode = _resolve_service_operation_admission_mode(
        service_operation_config=service_operation_config,
    )
    return ServiceOperationAdmissionRequirements(
        admission_mode=admission_mode,
        contract_context_required=admission_mode
        in {
            "contract_and_permit_required",
            "contract_required",
            "metered_settlement_required",
        },
        actor_context_required=admission_mode == "identity_required",
        permit_required=admission_mode == "contract_and_permit_required",
        settlement_required=admission_mode == "metered_settlement_required",
    )


def _resolve_service_operation_admission_mode(
    *,
    service_operation_config: ServiceOperationConfig | None,
) -> str:
    raw = getattr(service_operation_config, "admission_mode", None)
    if raw is None:
        return _legacy_service_operation_admission_mode(
            service_operation_config=service_operation_config,
        )
    value = _enum_value(raw).strip().casefold()
    if value in _SUPPORTED_SERVICE_OPERATION_ADMISSION_MODES:
        return value
    return _legacy_service_operation_admission_mode(
        service_operation_config=service_operation_config,
    )


def _legacy_service_operation_admission_mode(
    *,
    service_operation_config: ServiceOperationConfig | None,
) -> str:
    if service_operation_config is None:
        return "public_read"
    receipt_policy = _enum_value(
        getattr(service_operation_config, "receipt_policy", None)
    ).strip()
    if receipt_policy == ServiceApiDispatchReceiptPolicy.read_model.value:
        return "public_read"
    return "public_read"


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value) or "")


def _read_operation_access_preflight(
    *,
    operation_access_context: ServiceOperationAccessContext | None,
    service_id: UUID,
    service_operation_config_id: UUID,
) -> ServiceAccessEvidence | None:
    if operation_access_context is None:
        return None
    return resolve_service_contract_operation_access_evidence(
        subscriptions=operation_access_context.subscriptions,
        service_id=service_id,
        consumer_finance_entity_id=operation_access_context.consumer_finance_entity_id,
        service_operation_config_id=service_operation_config_id,
        service_contracts_by_smart_contract_id=operation_access_context.service_contracts_by_smart_contract_id,
        service_contract_configs_by_id=operation_access_context.service_contract_configs_by_id,
        now=operation_access_context.now,
    )


def _read_operation_policy_summary(
    *,
    operation_access_context: ServiceOperationAccessContext | None,
    access_evidence: ServiceAccessEvidence | None,
) -> ServiceContractOperationPolicySummary | None:
    operation_grant = _read_operation_grant(
        operation_access_context=operation_access_context,
        access_evidence=access_evidence,
    )
    if operation_grant is None:
        return None
    return build_service_contract_operation_policy_summary(
        operation_grant=operation_grant,
    )


def _read_operation_grant(
    *,
    operation_access_context: ServiceOperationAccessContext | None,
    access_evidence: ServiceAccessEvidence | None,
) -> ServiceContractConfigOperationGrant | None:
    if operation_access_context is None or access_evidence is None:
        return None
    operation_grant_id = access_evidence.service_contract_config_operation_grant_id
    contract_config_id = access_evidence.service_contract_config_id
    if operation_grant_id is None or contract_config_id is None:
        return None
    configs_by_id = operation_access_context.service_contract_configs_by_id or {}
    contract_config = configs_by_id.get(contract_config_id)
    if contract_config is None:
        return None
    for grant in contract_config.operation_grants:
        if grant.id == operation_grant_id:
            return grant
    return None


def _read_actor_role_preflight(
    *,
    session: Session,
    actor_id: UUID | None,
    service_operation_config_id: UUID,
    actor_role_evidence: tuple[ServiceActorRoleEvidence, ...],
) -> tuple[
    tuple[ServiceActorRoleEvidence, ...],
    tuple[ServiceActorRoleRequirementReadModel, ...],
    tuple[str, ...],
]:
    service_operation_config = session.imap_get(
        ServiceOperationConfig, service_operation_config_id
    )
    if service_operation_config is None:
        return (), (), ()
    role_requirements = tuple(service_operation_config.role_requirements or ())
    if not role_requirements:
        return (), (), ()
    if actor_id is None:
        return (
            (),
            tuple(
                _actor_role_requirement_read_model(
                    requirement=requirement,
                    satisfied=False,
                )
                for requirement in role_requirements
            ),
            ("missing_actor_id",),
        )

    accepted: list[ServiceApiActorRoleEvidence] = []
    requirement_models: list[ServiceActorRoleRequirementReadModel] = []
    blockers: list[str] = []
    for requirement in role_requirements:
        matching_evidence = next(
            (
                evidence
                for evidence in actor_role_evidence
                if _actor_role_evidence_satisfies_requirement(
                    evidence=evidence,
                    actor_id=actor_id,
                    role_config_id=requirement.role_config_id,
                    access_scope=requirement.access_scope,
                    scope_kind=requirement.scope_kind,
                    scope_ref=requirement.scope_ref,
                    class_instance_identity_required=(
                        requirement.class_instance_identity_required
                    ),
                    role_assignment_binding_required=(
                        requirement.role_assignment_binding_required
                    ),
                )
            ),
            None,
        )
        satisfied = matching_evidence is not None
        requirement_models.append(
            _actor_role_requirement_read_model(
                requirement=requirement,
                satisfied=satisfied,
            )
        )
        if matching_evidence is not None:
            accepted.append(matching_evidence)
        else:
            blockers.append("missing_actor_role")
    return tuple(accepted), tuple(requirement_models), tuple(dict.fromkeys(blockers))


def _validate_operation_access_preflight(
    *,
    operation_access_context: ServiceOperationAccessContext | None,
    service_id: UUID,
    service_operation_config_id: UUID,
) -> ServiceAccessEvidence | None:
    if operation_access_context is None:
        return None

    evidence = resolve_service_contract_operation_access_evidence(
        subscriptions=operation_access_context.subscriptions,
        service_id=service_id,
        consumer_finance_entity_id=operation_access_context.consumer_finance_entity_id,
        service_operation_config_id=service_operation_config_id,
        service_contracts_by_smart_contract_id=operation_access_context.service_contracts_by_smart_contract_id,
        service_contract_configs_by_id=operation_access_context.service_contract_configs_by_id,
        now=operation_access_context.now,
    )
    if not evidence.access_granted:
        raise PermissionError(
            "Service API dispatch denied by ServiceContractConfig operation grant preflight: "
            + f"reason={evidence.reason.value} "
            + f"service_id={service_id} "
            + f"service_operation_config_id={service_operation_config_id}"
        )
    return evidence


def _validate_actor_role_preflight(
    *,
    session: Session,
    actor_id: UUID | None,
    service_operation_config_id: UUID,
    actor_role_evidence: tuple[ServiceActorRoleEvidence, ...],
) -> tuple[ServiceActorRoleEvidence, ...]:
    service_operation_config = session.imap_get(
        ServiceOperationConfig, service_operation_config_id
    )
    if service_operation_config is None:
        return ()

    role_requirements = tuple(service_operation_config.role_requirements or ())
    if not role_requirements:
        return ()
    if actor_id is None:
        raise PermissionError(
            "Service API dispatch denied by ActorRole preflight: "
            + "actor_id is required when ServiceOperationConfig.role_requirements are declared "
            + f"service_operation_config_id={service_operation_config_id}"
        )

    accepted: list[ServiceApiActorRoleEvidence] = []
    for requirement in role_requirements:
        matching_evidence = next(
            (
                evidence
                for evidence in actor_role_evidence
                if _actor_role_evidence_satisfies_requirement(
                    evidence=evidence,
                    actor_id=actor_id,
                    role_config_id=requirement.role_config_id,
                    access_scope=requirement.access_scope,
                    scope_kind=requirement.scope_kind,
                    scope_ref=requirement.scope_ref,
                    class_instance_identity_required=(
                        requirement.class_instance_identity_required
                    ),
                    role_assignment_binding_required=(
                        requirement.role_assignment_binding_required
                    ),
                )
            ),
            None,
        )
        if matching_evidence is None:
            raise PermissionError(
                "Service API dispatch denied by ActorRole preflight: missing required role evidence "
                + f"service_operation_config_id={service_operation_config_id} "
                + f"role_config_id={requirement.role_config_id} "
                + f"access_scope={requirement.access_scope!r} "
                + f"scope_kind={requirement.scope_kind!r} "
                + f"scope_ref={requirement.scope_ref!r}"
            )
        accepted.append(matching_evidence)
    return tuple(accepted)


def _raise_for_contract_admission_denial(
    *,
    admission: ServiceOperationContractAdmissionReadModel,
) -> None:
    if admission.allowed:
        return
    raise ServiceOperationAdmissionDenied(
        admission=admission,
        message=_contract_admission_denial_message(
            admission=admission,
        ),
    )


def _contract_admission_denial_message(
    *,
    admission: ServiceOperationContractAdmissionReadModel,
) -> str:
    access_evidence = admission.access_evidence
    if access_evidence is not None and not access_evidence.access_granted:
        return (
            "Service API dispatch denied by ServiceContractConfig operation grant preflight: "
            + f"reason={access_evidence.reason.value} "
            + f"service_id={admission.service_id} "
            + "service_operation_config_id="
            + f"{admission.service_operation_config_id}"
        )
    if "missing_actor_id" in admission.blocking_reasons:
        return (
            "Service API dispatch denied by ActorRole preflight: "
            + "actor_id is required when ServiceOperationConfig.role_requirements are declared "
            + "service_operation_config_id="
            + f"{admission.service_operation_config_id}"
        )
    if "missing_actor_role" in admission.blocking_reasons:
        missing = next(
            (
                requirement
                for requirement in admission.actor_role_requirements
                if not requirement.satisfied
            ),
            None,
        )
        if missing is None:
            return (
                "Service API dispatch denied by ActorRole preflight: missing required role evidence "
                + "service_operation_config_id="
                + f"{admission.service_operation_config_id}"
            )
        return (
            "Service API dispatch denied by ActorRole preflight: missing required role evidence "
            + f"service_operation_config_id={admission.service_operation_config_id} "
            + f"role_config_id={missing.role_config_id} "
            + f"access_scope={missing.access_scope!r} "
            + f"scope_kind={missing.scope_kind!r} "
            + f"scope_ref={missing.scope_ref!r}"
        )
    return (
        "Service API dispatch denied by Service contract admission read model: "
        + ",".join(admission.blocking_reasons)
    )


def _actor_role_requirement_read_model(
    *,
    requirement: ServiceOperationConfigRoleRequirement,
    satisfied: bool,
) -> ServiceActorRoleRequirementReadModel:
    return ServiceActorRoleRequirementReadModel(
        role_config_id=requirement.role_config_id,
        access_scope=requirement.access_scope,
        scope_kind=requirement.scope_kind,
        scope_ref=requirement.scope_ref,
        class_instance_identity_required=(requirement.class_instance_identity_required),
        role_assignment_binding_required=(requirement.role_assignment_binding_required),
        satisfied=satisfied,
    )


def _contract_admission_next_action(blocking_reasons: list[str]) -> str | None:
    if not blocking_reasons:
        return None
    if any(
        reason
        in {
            "actor_context_missing",
            "actor_context_not_ready",
            "actor_context_kind_invalid",
            "actor_id_missing",
        }
        for reason in blocking_reasons
    ):
        return "resolve_identity"
    if "session_actor_scope_mismatch" in blocking_reasons:
        return "bind_session_actor"
    if "missing_contract_access_context" in blocking_reasons:
        return "resolve_service_contract_context"
    if "missing_actor_id" in blocking_reasons:
        return "resolve_identity"
    if "missing_actor_role" in blocking_reasons:
        return "resolve_actor_role_evidence"
    if "missing_permit_policy" in blocking_reasons:
        return "configure_service_operation_permit_policy"
    if "missing_price_policy" in blocking_reasons:
        return "configure_service_operation_price_policy"
    reason = blocking_reasons[0]
    if reason == ServiceAccessDecisionReason.missing_operation_grant.value:
        return "grant_service_operation"
    if reason in {
        ServiceAccessDecisionReason.missing_subscription.value,
        ServiceAccessDecisionReason.subscription_inactive.value,
        ServiceAccessDecisionReason.subscription_not_started.value,
        ServiceAccessDecisionReason.subscription_expired.value,
    }:
        return "resolve_service_subscription"
    if reason in {
        ServiceAccessDecisionReason.missing_service_contract.value,
        ServiceAccessDecisionReason.contract_mismatch.value,
        ServiceAccessDecisionReason.contract_inactive.value,
        ServiceAccessDecisionReason.contract_not_started.value,
        ServiceAccessDecisionReason.contract_expired.value,
    }:
        return "resolve_service_contract"
    if reason in {
        ServiceAccessDecisionReason.missing_contract_config.value,
        ServiceAccessDecisionReason.contract_config_mismatch.value,
    }:
        return "resolve_service_contract_config"
    return "inspect_service_contract_admission"


def _actor_role_evidence_satisfies_requirement(
    *,
    evidence: ServiceActorRoleEvidence,
    actor_id: UUID,
    role_config_id: UUID,
    access_scope: str,
    scope_kind: str,
    scope_ref: str,
    class_instance_identity_required: bool,
    role_assignment_binding_required: bool,
) -> bool:
    if not evidence.granted:
        return False
    if evidence.actor_id is not None and evidence.actor_id != actor_id:
        return False
    if evidence.role_config_id != role_config_id:
        return False
    if _norm_scope(evidence.access_scope, default="operation") != _norm_scope(
        access_scope,
        default="operation",
    ):
        return False
    if _norm_scope(evidence.scope_kind, default="operation") != _norm_scope(
        scope_kind,
        default="operation",
    ):
        return False
    if _norm_scope(evidence.scope_ref, default="default") != _norm_scope(
        scope_ref,
        default="default",
    ):
        return False
    if class_instance_identity_required and evidence.class_instance_identity_id is None:
        return False
    if role_assignment_binding_required and evidence.role_assignment_binding_id is None:
        return False
    return True


def _norm_scope(value: str, *, default: str) -> str:
    return (value or "").casefold().strip() or default


async def _drain_stream_events(
    *,
    stream_iterator: AsyncIterator[object],
    stream_event_sink: ServiceApiStreamEventSink,
) -> None:
    async for event in stream_iterator:
        await stream_event_sink(event)


def _coerce_api_call_outcome_payload(
    response_object: object | None,
) -> JsonObject | None:
    payload = dump_service_duplex_payload(response_object)
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise RuntimeError(
            "ApiCallOutcome currently requires one JSON-object response payload."
        )
    return cast(JsonObject, payload)


def _api_call_hint_from_dispatch_envelope(envelope: object) -> ApiCall:
    request_model_id = getattr(envelope, "request_model_id", None)
    request_class_config_id = getattr(envelope, "request_class_config_id", None)
    call_key = getattr(envelope, "call_key")
    request_model = (
        InlineValueInstance.model_construct(
            id=request_model_id,
            class_config_id=request_class_config_id,
            owner_key=call_key,
            inline_value_instance_attributes=[],
        )
        if request_model_id is not None and request_class_config_id is not None
        else None
    )
    return ApiCall.model_construct(
        id=getattr(envelope, "api_call_id"),
        api_capability_endpoint_id=getattr(
            envelope,
            "api_capability_endpoint_id",
        ),
        request_model_id=request_model_id,
        request_model=request_model,
        call_key=call_key,
        description=getattr(envelope, "description", None),
        request_hash=getattr(envelope, "request_hash"),
        outcome=None,
    )


def _resolve_api_call_outcome_response_class_config(
    *,
    index: object,
    response_type_ref: str | None,
) -> ClassConfig | None:
    authored_ref = str(response_type_ref or "").strip()
    if not authored_ref:
        return None

    matches = tuple(
        class_config
        for class_config in index.class_configs_by_id.values()
        if _authored_class_ref_from_class_fqn(class_fqn=(class_config.class_fqn or ""))
        == authored_ref
    )
    if len(matches) == 1:
        return matches[0]
    if not matches:
        registered_matches = _resolve_registered_pydantic_response_class_configs(
            response_type_ref=authored_ref
        )
        if len(registered_matches) == 1:
            return registered_matches[0]
        if not registered_matches:
            return None
        raise RuntimeError(
            "Service runtime resolved ambiguous registered response ClassConfig for API call outcome "
            "materialization: "
            f"response_type_ref={authored_ref!r} matches={[str(item.id) for item in registered_matches]}"
        )
    raise RuntimeError(
        "Service runtime resolved ambiguous response ClassConfig for API call outcome materialization: "
        f"response_type_ref={authored_ref!r} matches={[str(item.id) for item in matches]}"
    )


def _resolve_registered_pydantic_response_class_configs(
    *,
    response_type_ref: str,
) -> tuple[ClassConfig, ...]:
    package_prefix = response_type_ref.split(".", 1)[0].strip()
    if package_prefix:
        register_pydantic_package_class_configs(package_prefix=package_prefix)

    class_name = response_type_ref.rsplit(".", 1)[-1].strip()
    matches: list[ClassConfig] = []
    for entry in iter_registered_class_config_payloads():
        source = (entry.source or "").strip()
        if package_prefix and source and not source.startswith(package_prefix + "/"):
            continue
        class_config = ClassConfig.model_validate(entry.payload)
        class_fqn = (class_config.class_fqn or "").strip()
        if (
            _authored_class_ref_from_class_fqn(class_fqn=class_fqn) == response_type_ref
            or class_fqn == response_type_ref
            or (class_name and class_fqn.endswith("." + class_name))
        ):
            matches.append(class_config)

    return tuple({item.id: item for item in matches if item.id is not None}.values())


def _authored_class_ref_from_class_fqn(*, class_fqn: str) -> str:
    parts = [part.strip() for part in class_fqn.split(".") if part.strip()]
    if len(parts) <= 2:
        return class_fqn.strip()
    return ".".join(
        [
            parts[0],
            *[part for part in parts[1:-1] if part.casefold() != "default"],
            parts[-1],
        ]
    )


__all__ = [
    "ExecutedServiceApiDispatch",
    "ServiceActorRoleEvidence",
    "ServiceApiActorRoleEvidence",
    "ServiceApiDispatchPreflightResult",
    "ServiceApiDispatchReceiptPolicy",
    "ServiceOperationAdmissionDenied",
    "ServiceApiOperationAccessContext",
    "ServiceOperationAccessContext",
    "ServiceOperationAdmissionRequirements",
    "ServiceOperationContractAdmissionReadModel",
    "ServiceOperationAdmissionContext",
    "ServiceOperationPreflightResult",
    "ServiceApiStreamEventSink",
    "execute_service_api_dispatch_plan",
    "service_operation_admission_blocked_payload",
    "service_actor_role_evidence_from_invocation_context",
    "service_api_dispatch_receipt",
    "service_api_dispatch_response_payload",
    "service_operation_contract_admission_payload",
    "read_service_operation_contract_admission",
    "validate_service_api_dispatch_preflight",
    "validate_service_operation_preflight",
]
