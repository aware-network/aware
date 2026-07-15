from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal, Protocol
from uuid import UUID

from aware_api_ontology.api.api_call import ApiCall
from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus
from aware_api_ontology.api.api_call_outcome import ApiCallOutcome
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_meta.materialization.contracts import MaterializationLaneContext
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_orm.session.session import Session
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_config_api import ServiceConfigApi
from aware_service_ontology.service.service_enums import (
    ServiceOperationSettlementPolicy,
    ServiceOperationStatus,
)
from aware_service_ontology.service.service_operation import ServiceOperation
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.service.service_operation_config_api_endpoint import (
    ServiceOperationConfigApiEndpoint,
)

from aware_service_runtime.api_ingress.admission_context import (
    ServiceContractAccessContextRef,
    ServiceOperationAdmissionContext,
    ServiceOperationAuthorizationRef,
)
from aware_service_runtime.api_ingress.access import (
    ServiceContractOperationPolicySummary,
)
from aware_service_runtime.api_ingress.dispatch import (
    ResolvedServiceApiDispatch,
    require_single_service_api_dispatch_candidate,
)


@dataclass(frozen=True, slots=True)
class ServiceOperationMeteringEvidenceV1:
    schema: Literal["aware.service.operation_metering.v1"]
    phase: Literal["upper_bound", "actual"]
    cost_basis_amount: Decimal
    cost_basis_coin_id: UUID
    evidence_ref: str


@dataclass(frozen=True, slots=True)
class ServiceOperationMeteringContextV1:
    """Service-owned commercial coordinates admitted to a product meter."""

    schema: Literal["aware.service.operation_metering_context.v1"]
    cost_basis_coin_id: UUID


@dataclass(frozen=True, slots=True)
class ServiceOperationSettlementReceiptRefs:
    service_operation_id: UUID
    service_contract_id: UUID
    permit_id: UUID
    price_id: UUID
    price_schedule_id: UUID
    rate_snapshot_id: UUID
    price_reservation_id: UUID
    smart_contract_reservation_id: UUID
    settlement_id: UUID
    transaction_id: UUID | None
    payer_wallet_balance_id: UUID
    receiver_wallet_balance_id: UUID
    status: str
    idempotent_replay: bool


@dataclass(frozen=True, slots=True)
class ServiceOperationSettlementContext:
    actor_id: UUID | None
    service_id: UUID
    service_ref: Service
    service_config_api_id: UUID
    service_config_api_ref: ServiceConfigApi
    service_operation_id: UUID
    service_operation_ref: ServiceOperation
    service_operation_config_id: UUID
    service_operation_config_ref: ServiceOperationConfig
    service_api_endpoint_binding_id: UUID | None
    service_api_endpoint_binding_ref: ServiceOperationConfigApiEndpoint | None
    api_capability_endpoint_id: UUID
    api_capability_endpoint_ref: ApiCapabilityEndpoint
    api_call_id: UUID | None
    api_call_ref: ApiCall
    request_hash: str
    operation_key: str
    price_id: UUID | None
    pricing_policy_id: UUID | None
    settlement_policy: ServiceOperationSettlementPolicy
    metering_estimate: ServiceOperationMeteringEvidenceV1 | None
    contract_access_context_ref: ServiceContractAccessContextRef | None
    operation_authorization_ref: ServiceOperationAuthorizationRef | None
    service_lane: MaterializationLaneContext
    api_call_lane: MaterializationLaneContext
    economy_price_lane: MaterializationLaneContext | None


@dataclass(frozen=True, slots=True)
class ServiceOperationSettlementPreparation:
    context: ServiceOperationSettlementContext


@dataclass(frozen=True, slots=True)
class ServiceOperationSettlementFinalization:
    context: ServiceOperationSettlementContext
    service_operation_status: ServiceOperationStatus
    result_info: str | None
    api_call_outcome_id: UUID | None
    api_call_outcome_ref: ApiCallOutcome | None
    api_call_outcome_status: ApiCallOutcomeStatus | None
    api_call_outcome_response_model_id: UUID | None
    api_call_outcome_error: str | None
    metering_receipt: ServiceOperationMeteringEvidenceV1 | None


class ServiceOperationSettlementCoordinator(Protocol):
    async def resolve_metering_context(
        self,
        *,
        session: Session,
        preparation: ServiceOperationSettlementPreparation,
    ) -> ServiceOperationMeteringContextV1 | None: ...

    async def before_execute(
        self,
        *,
        session: Session,
        preparation: ServiceOperationSettlementPreparation,
    ) -> object | None: ...

    async def after_execute(
        self,
        *,
        session: Session,
        prepared_state: object | None,
        finalization: ServiceOperationSettlementFinalization,
    ) -> ServiceOperationSettlementReceiptRefs | None: ...


def build_service_operation_settlement_context(
    *,
    session: Session,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    service_lane: MaterializationLaneContext,
    api_call_lane: MaterializationLaneContext,
    resolved_dispatch: ResolvedServiceApiDispatch,
    service_id: UUID,
    service_operation_id: UUID,
    service_operation_config_id: UUID,
    service_api_endpoint_binding_id: UUID | None,
    operation_key: str,
    admission_context: ServiceOperationAdmissionContext | None = None,
    operation_policy: ServiceContractOperationPolicySummary | None = None,
    invocation_context: Mapping[str, object] | None = None,
) -> ServiceOperationSettlementContext:
    candidate = require_single_service_api_dispatch_candidate(
        resolved_dispatch=resolved_dispatch,
    )
    api_call_id = resolved_dispatch.dispatch_plan.envelope.api_call_id
    request_hash = (resolved_dispatch.dispatch_plan.envelope.request_hash or "").strip()
    if not request_hash:
        raise RuntimeError(
            "Service settlement context requires dispatch_plan.envelope.request_hash"
        )
    operation_price_id = resolve_service_operation_config_price_id(
        session=session,
        service_operation_config_id=service_operation_config_id,
    )
    operation_settlement_policy = resolve_service_operation_config_settlement_policy(
        session=session,
        service_operation_config_id=service_operation_config_id,
    )
    price_id, pricing_policy_id, settlement_policy = _resolve_effective_price_terms(
        operation_price_id=operation_price_id,
        operation_settlement_policy=operation_settlement_policy,
        operation_policy=operation_policy,
    )
    metering_estimate = normalize_service_operation_metering_evidence(
        _mapping_value(invocation_context, "service_operation_metering_estimate"),
        expected_phase="upper_bound",
    )
    economy_price_lane: MaterializationLaneContext | None = None
    if (
        price_id is not None
        or settlement_policy != ServiceOperationSettlementPolicy.none
    ):
        price_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="Price",
        )
        economy_price_lane = MaterializationLaneContext(
            branch_id=service_lane.branch_id,
            projection_hash=price_projection_hash,
        )
    if settlement_policy != ServiceOperationSettlementPolicy.none and price_id is None:
        raise RuntimeError(
            "Service settlement policy requires ServiceOperationConfig.price_id when settlement is enabled"
        )
    return ServiceOperationSettlementContext(
        actor_id=actor_id,
        service_id=service_id,
        service_ref=Service.model_construct(id=service_id),
        service_config_api_id=candidate.service_config_api_id,
        service_config_api_ref=ServiceConfigApi.model_construct(
            id=candidate.service_config_api_id,
        ),
        service_operation_id=service_operation_id,
        service_operation_ref=ServiceOperation.model_construct(
            id=service_operation_id,
        ),
        service_operation_config_id=service_operation_config_id,
        service_operation_config_ref=ServiceOperationConfig.model_construct(
            id=service_operation_config_id,
        ),
        service_api_endpoint_binding_id=service_api_endpoint_binding_id,
        service_api_endpoint_binding_ref=(
            ServiceOperationConfigApiEndpoint.model_construct(
                id=service_api_endpoint_binding_id,
            )
            if service_api_endpoint_binding_id is not None
            else None
        ),
        api_capability_endpoint_id=resolved_dispatch.dispatch_plan.envelope.api_capability_endpoint_id,
        api_capability_endpoint_ref=ApiCapabilityEndpoint.model_construct(
            id=resolved_dispatch.dispatch_plan.envelope.api_capability_endpoint_id,
        ),
        api_call_id=api_call_id,
        api_call_ref=ApiCall.model_construct(id=api_call_id),
        request_hash=request_hash,
        operation_key=operation_key,
        price_id=price_id,
        pricing_policy_id=pricing_policy_id,
        settlement_policy=settlement_policy,
        metering_estimate=metering_estimate,
        contract_access_context_ref=(
            admission_context.contract_access_context_ref
            if admission_context is not None
            else None
        ),
        operation_authorization_ref=(
            admission_context.operation_authorization_ref
            if admission_context is not None
            else None
        ),
        service_lane=service_lane,
        api_call_lane=api_call_lane,
        economy_price_lane=economy_price_lane,
    )


def extract_service_operation_metering_receipt(
    response_object: object,
) -> ServiceOperationMeteringEvidenceV1 | None:
    payload = _object_mapping(response_object)
    return normalize_service_operation_metering_evidence(
        _mapping_value(payload, "service_operation_metering_receipt"),
        expected_phase="actual",
    )


def normalize_service_operation_metering_evidence(
    value: object,
    *,
    expected_phase: Literal["upper_bound", "actual"],
) -> ServiceOperationMeteringEvidenceV1 | None:
    if value is None:
        return None
    payload = _object_mapping(value)
    if not payload:
        raise ValueError("Service operation metering evidence must be an object")
    schema = str(payload.get("schema") or "").strip()
    if schema != "aware.service.operation_metering.v1":
        raise ValueError(f"Unsupported Service operation metering schema: {schema!r}")
    phase = str(payload.get("phase") or "").strip()
    if phase != expected_phase:
        raise ValueError(
            "Service operation metering phase mismatch: "
            f"expected={expected_phase!r} actual={phase!r}"
        )
    amount = _exact_non_negative_decimal(
        payload.get("cost_basis_amount"),
        field_name="cost_basis_amount",
    )
    coin_id = _required_uuid(
        payload.get("cost_basis_coin_id"),
        field_name="cost_basis_coin_id",
    )
    evidence_ref = str(payload.get("evidence_ref") or "").strip()
    if not evidence_ref:
        raise ValueError("Service operation metering evidence_ref must be non-empty")
    return ServiceOperationMeteringEvidenceV1(
        schema="aware.service.operation_metering.v1",
        phase=expected_phase,
        cost_basis_amount=amount,
        cost_basis_coin_id=coin_id,
        evidence_ref=evidence_ref,
    )


def _resolve_effective_price_terms(
    *,
    operation_price_id: UUID | None,
    operation_settlement_policy: ServiceOperationSettlementPolicy,
    operation_policy: ServiceContractOperationPolicySummary | None,
) -> tuple[UUID | None, UUID | None, ServiceOperationSettlementPolicy]:
    policy = operation_policy.price if operation_policy is not None else None
    if policy is None:
        return operation_price_id, None, operation_settlement_policy
    if policy.price_source == "operation_default":
        price_id = operation_price_id
    elif policy.price_source == "contract_override":
        if policy.price_id is None:
            raise RuntimeError(
                "Service contract price_source=contract_override requires typed price_id"
            )
        price_id = policy.price_id
    else:
        raise RuntimeError(
            f"Unsupported Service contract price_source: {policy.price_source!r}"
        )
    settlement_policy = operation_settlement_policy
    if policy.settlement_policy_override is not None:
        try:
            settlement_policy = ServiceOperationSettlementPolicy(
                policy.settlement_policy_override
            )
        except ValueError as exc:
            raise RuntimeError(
                "Unsupported Service contract settlement policy override: "
                f"{policy.settlement_policy_override!r}"
            ) from exc
    return price_id, policy.pricing_policy_id, settlement_policy


def _object_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="python")
        if isinstance(dumped, Mapping):
            return dumped
    return {}


def _mapping_value(
    value: Mapping[str, object] | None,
    key: str,
) -> object:
    return value.get(key) if value is not None else None


def _exact_non_negative_decimal(value: object, *, field_name: str) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"{field_name} must be an exact Decimal, int, or decimal text")
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be an exact decimal amount") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{field_name} must be finite and >= 0")
    return amount


def _required_uuid(value: object, *, field_name: str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"{field_name} must be a UUID") from exc


def resolve_service_operation_config_price_id(
    *,
    session: Session,
    service_operation_config_id: UUID,
) -> UUID | None:
    service_operation_config = session.imap_get(
        ServiceOperationConfig,
        service_operation_config_id,
    )
    if service_operation_config is None:
        return None
    return service_operation_config.price_id


def resolve_service_operation_config_settlement_policy(
    *,
    session: Session,
    service_operation_config_id: UUID,
) -> ServiceOperationSettlementPolicy:
    service_operation_config = session.imap_get(
        ServiceOperationConfig,
        service_operation_config_id,
    )
    if service_operation_config is None:
        return ServiceOperationSettlementPolicy.none
    policy = getattr(service_operation_config, "settlement_policy", None)
    if policy is None:
        return ServiceOperationSettlementPolicy.none
    return policy


__all__ = [
    "ServiceOperationSettlementContext",
    "ServiceOperationSettlementCoordinator",
    "ServiceOperationSettlementFinalization",
    "ServiceOperationMeteringEvidenceV1",
    "ServiceOperationMeteringContextV1",
    "ServiceOperationSettlementPreparation",
    "ServiceOperationSettlementReceiptRefs",
    "build_service_operation_settlement_context",
    "extract_service_operation_metering_receipt",
    "normalize_service_operation_metering_evidence",
    "resolve_service_operation_config_settlement_policy",
    "resolve_service_operation_config_price_id",
]
