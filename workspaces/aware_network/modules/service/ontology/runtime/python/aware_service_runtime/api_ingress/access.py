from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from aware_service_ontology.service.service_contract import ServiceContract
from aware_service_ontology.service.service_contract_config import ServiceContractConfig
from aware_service_ontology.service.service_contract_config_operation_grant import (
    ServiceContractConfigOperationGrant,
)
from aware_service_ontology.service.service_contract_operation_permit_policy import (
    ServiceContractOperationPermitPolicy,
)
from aware_service_ontology.service.service_contract_operation_price_policy import (
    ServiceContractOperationPricePolicy,
)
from aware_service_ontology.service.service_contract_operation_quota_policy import (
    ServiceContractOperationQuotaPolicy,
)
from aware_service_ontology.service.service_enums import (
    ServiceContractStatus,
    ServiceSubscriptionStatus,
)
from aware_service_ontology.service.service_subscription import ServiceSubscription

GRANTING_SUBSCRIPTION_STATUSES = frozenset(
    {
        ServiceSubscriptionStatus.active,
        ServiceSubscriptionStatus.trial,
    }
)


class ServiceAccessDecisionReason(str, Enum):
    granted = "granted"
    missing_subscription = "missing_subscription"
    service_mismatch = "service_mismatch"
    consumer_mismatch = "consumer_mismatch"
    subscription_inactive = "subscription_inactive"
    subscription_not_started = "subscription_not_started"
    subscription_expired = "subscription_expired"
    contract_mismatch = "contract_mismatch"
    contract_inactive = "contract_inactive"
    contract_not_started = "contract_not_started"
    contract_expired = "contract_expired"
    missing_service_contract = "missing_service_contract"
    missing_contract_config = "missing_contract_config"
    contract_config_mismatch = "contract_config_mismatch"
    missing_operation_grant = "missing_operation_grant"


@dataclass(frozen=True, slots=True)
class ServiceAccessEvidence:
    service_id: UUID
    consumer_finance_entity_id: UUID
    access_granted: bool
    reason: ServiceAccessDecisionReason
    service_subscription_id: UUID | None = None
    service_plan_id: UUID | None = None
    service_operation_config_id: UUID | None = None
    smart_contract_id: UUID | None = None
    service_contract_id: UUID | None = None
    service_contract_config_id: UUID | None = None
    service_contract_config_operation_grant_id: UUID | None = None
    subscription_status: ServiceSubscriptionStatus | None = None
    service_contract_status: ServiceContractStatus | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    contract_effective_from: datetime | None = None
    contract_effective_until: datetime | None = None
    cancel_at_period_end: bool = False
    external_subscription_handle: str | None = None
    source: Literal["service_subscription", "service_contract_operation"] = (
        "service_subscription"
    )
    commercial_scope: Literal["service", "service_contract_config"] = "service"
    pricing_scope: Literal["service_plan", "service_operation_config"] = "service_plan"


@dataclass(frozen=True, slots=True)
class ServiceContractOperationQuotaPolicySummary:
    service_contract_config_operation_grant_id: UUID | None
    unit: str
    limit_amount: int | None
    window: str
    burst_limit: int | None
    over_limit_behavior: str
    fail_closed: bool


@dataclass(frozen=True, slots=True)
class ServiceContractOperationPermitPolicySummary:
    service_contract_config_operation_grant_id: UUID | None
    requires_active_contract: bool
    requires_smart_contract_permit: bool
    requires_reservation_before_execute: bool
    permit_scope: str
    idempotency_scope: str
    fail_closed: bool


@dataclass(frozen=True, slots=True)
class ServiceContractOperationPricePolicySummary:
    service_contract_config_operation_grant_id: UUID | None
    price_source: str
    price_id: UUID | None
    price_ref: str | None
    pricing_policy_id: UUID | None
    pricing_policy_ref: str | None
    settlement_policy_override: str | None
    max_cost_required: bool
    quote_ttl_s: int | None
    fail_closed: bool


@dataclass(frozen=True, slots=True)
class ServiceContractOperationPolicySummary:
    service_contract_config_operation_grant_id: UUID
    source: Literal["typed_objects"] = "typed_objects"
    quota: ServiceContractOperationQuotaPolicySummary | None = None
    permit: ServiceContractOperationPermitPolicySummary | None = None
    price: ServiceContractOperationPricePolicySummary | None = None


def build_service_contract_operation_policy_summary(
    *,
    operation_grant: ServiceContractConfigOperationGrant,
) -> ServiceContractOperationPolicySummary:
    """Summarize typed policy objects without consulting compatibility JSON."""

    return ServiceContractOperationPolicySummary(
        service_contract_config_operation_grant_id=operation_grant.id,
        quota=_quota_policy_summary(operation_grant.quota_policy),
        permit=_permit_policy_summary(operation_grant.permit_policy),
        price=_price_policy_summary(operation_grant.price_policy),
    )


def build_service_subscription_access_evidence(
    *,
    subscription: ServiceSubscription | None,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    service_contract: ServiceContract | None = None,
    now: datetime | None = None,
) -> ServiceAccessEvidence:
    checked_at = _normalize_required_datetime(now or datetime.now(UTC))
    if subscription is None:
        return _denied(
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            reason=ServiceAccessDecisionReason.missing_subscription,
        )

    if subscription.service_id != service_id:
        return _evidence_from_subscription(
            subscription=subscription,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            service_contract=service_contract,
            access_granted=False,
            reason=ServiceAccessDecisionReason.service_mismatch,
        )
    if subscription.consumer_finance_entity_id != consumer_finance_entity_id:
        return _evidence_from_subscription(
            subscription=subscription,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            service_contract=service_contract,
            access_granted=False,
            reason=ServiceAccessDecisionReason.consumer_mismatch,
        )
    if subscription.status not in GRANTING_SUBSCRIPTION_STATUSES:
        return _evidence_from_subscription(
            subscription=subscription,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            service_contract=service_contract,
            access_granted=False,
            reason=ServiceAccessDecisionReason.subscription_inactive,
        )

    current_period_start = _normalize_datetime(subscription.current_period_start)
    if current_period_start is not None and current_period_start > checked_at:
        return _evidence_from_subscription(
            subscription=subscription,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            service_contract=service_contract,
            access_granted=False,
            reason=ServiceAccessDecisionReason.subscription_not_started,
        )

    current_period_end = _normalize_datetime(subscription.current_period_end)
    if current_period_end is not None and current_period_end <= checked_at:
        return _evidence_from_subscription(
            subscription=subscription,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            service_contract=service_contract,
            access_granted=False,
            reason=ServiceAccessDecisionReason.subscription_expired,
        )

    if service_contract is not None:
        contract_denial = _validate_service_contract(
            service_contract=service_contract,
            subscription=subscription,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            checked_at=checked_at,
        )
        if contract_denial is not None:
            return _evidence_from_subscription(
                subscription=subscription,
                service_id=service_id,
                consumer_finance_entity_id=consumer_finance_entity_id,
                service_contract=service_contract,
                access_granted=False,
                reason=contract_denial,
            )

    return _evidence_from_subscription(
        subscription=subscription,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_contract=service_contract,
        access_granted=True,
        reason=ServiceAccessDecisionReason.granted,
    )


def resolve_service_subscription_access_evidence(
    *,
    subscriptions: Iterable[ServiceSubscription],
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    service_contracts_by_smart_contract_id: (
        Mapping[UUID, ServiceContract] | None
    ) = None,
    now: datetime | None = None,
) -> ServiceAccessEvidence:
    denials: list[ServiceAccessEvidence] = []
    for subscription in subscriptions:
        service_contract = None
        if service_contracts_by_smart_contract_id is not None:
            service_contract = service_contracts_by_smart_contract_id.get(
                subscription.contract_id
            )
        evidence = build_service_subscription_access_evidence(
            subscription=subscription,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            service_contract=service_contract,
            now=now,
        )
        if evidence.access_granted:
            return evidence
        denials.append(evidence)

    for denial in denials:
        if denial.reason not in (
            ServiceAccessDecisionReason.service_mismatch,
            ServiceAccessDecisionReason.consumer_mismatch,
        ):
            return denial

    return _denied(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        reason=ServiceAccessDecisionReason.missing_subscription,
    )


def build_service_contract_operation_access_evidence(
    *,
    subscription: ServiceSubscription | None,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    service_operation_config_id: UUID,
    service_contract: ServiceContract | None = None,
    service_contract_config: ServiceContractConfig | None = None,
    now: datetime | None = None,
) -> ServiceAccessEvidence:
    base = build_service_subscription_access_evidence(
        subscription=subscription,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_contract=service_contract,
        now=now,
    )
    if not base.access_granted:
        return _operation_evidence_from_base(
            base=base,
            service_operation_config_id=service_operation_config_id,
            access_granted=False,
            reason=base.reason,
        )

    if service_contract is None:
        return _operation_evidence_from_base(
            base=base,
            service_operation_config_id=service_operation_config_id,
            access_granted=False,
            reason=ServiceAccessDecisionReason.missing_service_contract,
        )

    if service_contract_config is None:
        return _operation_evidence_from_base(
            base=base,
            service_operation_config_id=service_operation_config_id,
            service_contract_config_id=service_contract.service_contract_config_id,
            access_granted=False,
            reason=ServiceAccessDecisionReason.missing_contract_config,
        )

    if service_contract.service_contract_config_id != service_contract_config.id:
        return _operation_evidence_from_base(
            base=base,
            service_operation_config_id=service_operation_config_id,
            service_contract_config_id=service_contract_config.id,
            access_granted=False,
            reason=ServiceAccessDecisionReason.contract_config_mismatch,
        )

    grant = _find_operation_grant(
        service_contract_config=service_contract_config,
        service_operation_config_id=service_operation_config_id,
    )
    if grant is None:
        return _operation_evidence_from_base(
            base=base,
            service_operation_config_id=service_operation_config_id,
            service_contract_config_id=service_contract_config.id,
            access_granted=False,
            reason=ServiceAccessDecisionReason.missing_operation_grant,
        )

    return _operation_evidence_from_base(
        base=base,
        service_operation_config_id=service_operation_config_id,
        service_contract_config_id=service_contract_config.id,
        service_contract_config_operation_grant_id=grant.id,
        access_granted=True,
        reason=ServiceAccessDecisionReason.granted,
    )


def resolve_service_contract_operation_access_evidence(
    *,
    subscriptions: Iterable[ServiceSubscription],
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    service_operation_config_id: UUID,
    service_contracts_by_smart_contract_id: (
        Mapping[UUID, ServiceContract] | None
    ) = None,
    service_contract_configs_by_id: Mapping[UUID, ServiceContractConfig] | None = None,
    now: datetime | None = None,
) -> ServiceAccessEvidence:
    denials: list[ServiceAccessEvidence] = []
    for subscription in subscriptions:
        service_contract = None
        service_contract_config = None
        if service_contracts_by_smart_contract_id is not None:
            service_contract = service_contracts_by_smart_contract_id.get(
                subscription.contract_id
            )
        if service_contract is not None and service_contract_configs_by_id is not None:
            service_contract_config = service_contract_configs_by_id.get(
                service_contract.service_contract_config_id
            )
        evidence = build_service_contract_operation_access_evidence(
            subscription=subscription,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            service_operation_config_id=service_operation_config_id,
            service_contract=service_contract,
            service_contract_config=service_contract_config,
            now=now,
        )
        if evidence.access_granted:
            return evidence
        denials.append(evidence)

    for denial in denials:
        if denial.reason not in (
            ServiceAccessDecisionReason.service_mismatch,
            ServiceAccessDecisionReason.consumer_mismatch,
        ):
            return denial

    return _denied(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        reason=ServiceAccessDecisionReason.missing_subscription,
    )


def _validate_service_contract(
    *,
    service_contract: ServiceContract,
    subscription: ServiceSubscription,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    checked_at: datetime,
) -> ServiceAccessDecisionReason | None:
    if (
        service_contract.service_id != service_id
        or service_contract.consumer_finance_entity_id != consumer_finance_entity_id
        or service_contract.smart_contract_id != subscription.contract_id
    ):
        return ServiceAccessDecisionReason.contract_mismatch
    if service_contract.status != ServiceContractStatus.active:
        return ServiceAccessDecisionReason.contract_inactive

    effective_from = _normalize_datetime(service_contract.effective_from)
    if effective_from is not None and effective_from > checked_at:
        return ServiceAccessDecisionReason.contract_not_started

    effective_until = _normalize_datetime(service_contract.effective_until)
    if effective_until is not None and effective_until <= checked_at:
        return ServiceAccessDecisionReason.contract_expired

    return None


def _evidence_from_subscription(
    *,
    subscription: ServiceSubscription,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    service_contract: ServiceContract | None,
    access_granted: bool,
    reason: ServiceAccessDecisionReason,
) -> ServiceAccessEvidence:
    return ServiceAccessEvidence(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        access_granted=access_granted,
        reason=reason,
        service_subscription_id=subscription.id,
        service_plan_id=subscription.plan_id,
        smart_contract_id=subscription.contract_id,
        service_contract_id=(
            service_contract.id if service_contract is not None else None
        ),
        service_contract_config_id=(
            service_contract.service_contract_config_id
            if service_contract is not None
            else None
        ),
        subscription_status=subscription.status,
        service_contract_status=(
            service_contract.status if service_contract is not None else None
        ),
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        contract_effective_from=(
            service_contract.effective_from if service_contract is not None else None
        ),
        contract_effective_until=(
            service_contract.effective_until if service_contract is not None else None
        ),
        cancel_at_period_end=subscription.cancel_at_period_end,
        external_subscription_handle=subscription.external_subscription_handle,
    )


def _find_operation_grant(
    *,
    service_contract_config: ServiceContractConfig,
    service_operation_config_id: UUID,
) -> ServiceContractConfigOperationGrant | None:
    for grant in service_contract_config.operation_grants:
        if grant.service_operation_config_id == service_operation_config_id:
            return grant
    return None


def _quota_policy_summary(
    policy: ServiceContractOperationQuotaPolicy | None,
) -> ServiceContractOperationQuotaPolicySummary | None:
    if policy is None:
        return None
    return ServiceContractOperationQuotaPolicySummary(
        service_contract_config_operation_grant_id=(
            policy.service_contract_config_operation_grant_id
        ),
        unit=_enum_value(policy.unit),
        limit_amount=policy.limit_amount,
        window=_enum_value(policy.window),
        burst_limit=policy.burst_limit,
        over_limit_behavior=_enum_value(policy.over_limit_behavior),
        fail_closed=policy.fail_closed,
    )


def _permit_policy_summary(
    policy: ServiceContractOperationPermitPolicy | None,
) -> ServiceContractOperationPermitPolicySummary | None:
    if policy is None:
        return None
    return ServiceContractOperationPermitPolicySummary(
        service_contract_config_operation_grant_id=(
            policy.service_contract_config_operation_grant_id
        ),
        requires_active_contract=policy.requires_active_contract,
        requires_smart_contract_permit=policy.requires_smart_contract_permit,
        requires_reservation_before_execute=(
            policy.requires_reservation_before_execute
        ),
        permit_scope=_enum_value(policy.permit_scope),
        idempotency_scope=_enum_value(policy.idempotency_scope),
        fail_closed=policy.fail_closed,
    )


def _price_policy_summary(
    policy: ServiceContractOperationPricePolicy | None,
) -> ServiceContractOperationPricePolicySummary | None:
    if policy is None:
        return None
    return ServiceContractOperationPricePolicySummary(
        service_contract_config_operation_grant_id=(
            policy.service_contract_config_operation_grant_id
        ),
        price_source=_enum_value(policy.price_source),
        price_id=policy.price_id,
        price_ref=policy.price_ref,
        pricing_policy_id=policy.pricing_policy_id,
        pricing_policy_ref=policy.pricing_policy_ref,
        settlement_policy_override=_optional_enum_value(
            policy.settlement_policy_override
        ),
        max_cost_required=policy.max_cost_required,
        quote_ttl_s=policy.quote_ttl_s,
        fail_closed=policy.fail_closed,
    )


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


def _optional_enum_value(value: object | None) -> str | None:
    if value is None:
        return None
    return _enum_value(value)


def _operation_evidence_from_base(
    *,
    base: ServiceAccessEvidence,
    service_operation_config_id: UUID,
    access_granted: bool,
    reason: ServiceAccessDecisionReason,
    service_contract_config_id: UUID | None = None,
    service_contract_config_operation_grant_id: UUID | None = None,
) -> ServiceAccessEvidence:
    return replace(
        base,
        access_granted=access_granted,
        reason=reason,
        service_operation_config_id=service_operation_config_id,
        service_contract_config_id=(
            service_contract_config_id or base.service_contract_config_id
        ),
        service_contract_config_operation_grant_id=(
            service_contract_config_operation_grant_id
        ),
        source="service_contract_operation",
        commercial_scope="service_contract_config",
        pricing_scope="service_operation_config",
    )


def _denied(
    *,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    reason: ServiceAccessDecisionReason,
) -> ServiceAccessEvidence:
    return ServiceAccessEvidence(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        access_granted=False,
        reason=reason,
    )


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_required_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = [
    "GRANTING_SUBSCRIPTION_STATUSES",
    "ServiceAccessDecisionReason",
    "ServiceAccessEvidence",
    "ServiceContractOperationPermitPolicySummary",
    "ServiceContractOperationPolicySummary",
    "ServiceContractOperationPricePolicySummary",
    "ServiceContractOperationQuotaPolicySummary",
    "build_service_contract_operation_policy_summary",
    "build_service_contract_operation_access_evidence",
    "build_service_subscription_access_evidence",
    "resolve_service_contract_operation_access_evidence",
    "resolve_service_subscription_access_evidence",
]
