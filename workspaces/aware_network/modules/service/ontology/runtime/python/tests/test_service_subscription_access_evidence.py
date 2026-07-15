from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import aware_service_runtime.api_ingress.access as access_module
from aware_service_ontology.service.service_contract import ServiceContract
from aware_service_ontology.service.service_contract_config import ServiceContractConfig
from aware_service_ontology.service.service_contract_config_operation_grant import (
    ServiceContractConfigOperationGrant,
)
from aware_service_ontology.service.service_enums import (
    ServiceContractKind,
    ServiceContractStatus,
    ServiceSubscriptionStatus,
)
from aware_service_ontology.service.service_subscription import ServiceSubscription
from aware_service_runtime.api_ingress.access import (
    ServiceAccessDecisionReason,
    ServiceAccessEvidence,
    build_service_contract_operation_access_evidence,
    build_service_subscription_access_evidence,
    resolve_service_contract_operation_access_evidence,
    resolve_service_subscription_access_evidence,
)


def test_active_subscription_access_evidence_is_service_plan_scoped() -> None:
    now = datetime(2026, 5, 9, tzinfo=UTC)
    service_id = uuid4()
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    subscription = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        status=ServiceSubscriptionStatus.active,
        current_period_start=now - timedelta(days=1),
        current_period_end=now + timedelta(days=29),
    )
    service_contract = _service_contract(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        status=ServiceContractStatus.active,
        effective_from=now - timedelta(days=1),
        effective_until=now + timedelta(days=365),
    )

    evidence = build_service_subscription_access_evidence(
        subscription=subscription,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_contract=service_contract,
        now=now,
    )

    assert evidence.access_granted is True
    assert evidence.reason == ServiceAccessDecisionReason.granted
    assert evidence.service_subscription_id == subscription.id
    assert evidence.service_plan_id == subscription.plan_id
    assert evidence.smart_contract_id == smart_contract_id
    assert evidence.service_contract_id == service_contract.id
    assert evidence.subscription_status == ServiceSubscriptionStatus.active
    assert evidence.service_contract_status == ServiceContractStatus.active
    assert evidence.commercial_scope == "service"
    assert evidence.pricing_scope == "service_plan"


def test_operation_access_requires_contract_config_operation_grant() -> None:
    now = datetime(2026, 5, 9, tzinfo=UTC)
    service_id = uuid4()
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_operation_config_id = uuid4()
    service_contract_config_id = uuid4()
    subscription = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        status=ServiceSubscriptionStatus.active,
        current_period_start=now - timedelta(days=1),
        current_period_end=now + timedelta(days=29),
    )
    service_contract = _service_contract(
        service_id=service_id,
        service_contract_config_id=service_contract_config_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        status=ServiceContractStatus.active,
        effective_from=now - timedelta(days=1),
        effective_until=now + timedelta(days=365),
    )
    operation_grant = _operation_grant(
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
    )
    service_contract_config = _contract_config(
        service_contract_config_id=service_contract_config_id,
        operation_grants=[operation_grant],
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

    assert evidence.access_granted is True
    assert evidence.reason == ServiceAccessDecisionReason.granted
    assert evidence.source == "service_contract_operation"
    assert evidence.commercial_scope == "service_contract_config"
    assert evidence.pricing_scope == "service_operation_config"
    assert evidence.service_contract_config_id == service_contract_config_id
    assert evidence.service_operation_config_id == service_operation_config_id
    assert evidence.service_contract_config_operation_grant_id == operation_grant.id


def test_operation_access_denies_missing_operation_grant() -> None:
    now = datetime(2026, 5, 9, tzinfo=UTC)
    service_id = uuid4()
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_operation_config_id = uuid4()
    service_contract_config_id = uuid4()
    subscription = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        status=ServiceSubscriptionStatus.active,
        current_period_start=now - timedelta(days=1),
        current_period_end=now + timedelta(days=29),
    )
    service_contract = _service_contract(
        service_id=service_id,
        service_contract_config_id=service_contract_config_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        status=ServiceContractStatus.active,
        effective_from=now - timedelta(days=1),
        effective_until=now + timedelta(days=365),
    )
    service_contract_config = _contract_config(
        service_contract_config_id=service_contract_config_id,
        operation_grants=[
            _operation_grant(
                service_contract_config_id=service_contract_config_id,
                service_operation_config_id=uuid4(),
            )
        ],
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

    assert evidence.access_granted is False
    assert evidence.reason == ServiceAccessDecisionReason.missing_operation_grant
    assert evidence.service_contract_config_id == service_contract_config_id
    assert evidence.service_operation_config_id == service_operation_config_id
    assert evidence.service_contract_config_operation_grant_id is None


def test_trial_subscription_grants_access_until_period_end() -> None:
    now = datetime(2026, 5, 9, tzinfo=UTC)
    service_id = uuid4()
    consumer_finance_entity_id = uuid4()
    subscription = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        status=ServiceSubscriptionStatus.trial,
        current_period_start=now - timedelta(days=1),
        current_period_end=now + timedelta(days=14),
        cancel_at_period_end=True,
    )

    evidence = build_service_subscription_access_evidence(
        subscription=subscription,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        now=now,
    )

    assert evidence.access_granted is True
    assert evidence.subscription_status == ServiceSubscriptionStatus.trial
    assert evidence.cancel_at_period_end is True


def test_subscription_access_denies_inactive_and_expired_receipts() -> None:
    now = datetime(2026, 5, 9, tzinfo=UTC)
    service_id = uuid4()
    consumer_finance_entity_id = uuid4()
    inactive = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        status=ServiceSubscriptionStatus.past_due,
        current_period_start=now - timedelta(days=10),
        current_period_end=now + timedelta(days=20),
    )
    expired = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        status=ServiceSubscriptionStatus.active,
        current_period_start=now - timedelta(days=30),
        current_period_end=now,
    )

    inactive_evidence = build_service_subscription_access_evidence(
        subscription=inactive,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        now=now,
    )
    expired_evidence = build_service_subscription_access_evidence(
        subscription=expired,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        now=now,
    )

    assert inactive_evidence.access_granted is False
    assert inactive_evidence.reason == ServiceAccessDecisionReason.subscription_inactive
    assert expired_evidence.access_granted is False
    assert expired_evidence.reason == ServiceAccessDecisionReason.subscription_expired


def test_subscription_access_denies_contract_mismatch() -> None:
    now = datetime(2026, 5, 9, tzinfo=UTC)
    service_id = uuid4()
    consumer_finance_entity_id = uuid4()
    subscription = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        status=ServiceSubscriptionStatus.active,
        current_period_start=now - timedelta(days=1),
        current_period_end=now + timedelta(days=29),
    )
    mismatched_contract = _service_contract(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=uuid4(),
        status=ServiceContractStatus.active,
        effective_from=now - timedelta(days=1),
        effective_until=now + timedelta(days=365),
    )

    evidence = build_service_subscription_access_evidence(
        subscription=subscription,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_contract=mismatched_contract,
        now=now,
    )

    assert evidence.access_granted is False
    assert evidence.reason == ServiceAccessDecisionReason.contract_mismatch
    assert evidence.service_contract_id == mismatched_contract.id


def test_resolver_returns_first_granted_service_subscription() -> None:
    now = datetime(2026, 5, 9, tzinfo=UTC)
    service_id = uuid4()
    consumer_finance_entity_id = uuid4()
    wrong_service_subscription = _subscription(
        service_id=uuid4(),
        consumer_finance_entity_id=consumer_finance_entity_id,
        status=ServiceSubscriptionStatus.active,
        current_period_start=now - timedelta(days=1),
        current_period_end=now + timedelta(days=29),
    )
    granted_subscription = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        status=ServiceSubscriptionStatus.active,
        current_period_start=now - timedelta(days=1),
        current_period_end=now + timedelta(days=29),
    )

    evidence = resolve_service_subscription_access_evidence(
        subscriptions=[wrong_service_subscription, granted_subscription],
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        now=now,
    )

    assert evidence.access_granted is True
    assert evidence.service_subscription_id == granted_subscription.id


def test_operation_resolver_returns_first_granted_contract_config_grant() -> None:
    now = datetime(2026, 5, 9, tzinfo=UTC)
    service_id = uuid4()
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_operation_config_id = uuid4()
    service_contract_config_id = uuid4()
    subscription = _subscription(
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        status=ServiceSubscriptionStatus.active,
        current_period_start=now - timedelta(days=1),
        current_period_end=now + timedelta(days=29),
    )
    service_contract = _service_contract(
        service_id=service_id,
        service_contract_config_id=service_contract_config_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        status=ServiceContractStatus.active,
        effective_from=now - timedelta(days=1),
        effective_until=now + timedelta(days=365),
    )
    grant = _operation_grant(
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
    )

    evidence = resolve_service_contract_operation_access_evidence(
        subscriptions=[subscription],
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_operation_config_id=service_operation_config_id,
        service_contracts_by_smart_contract_id={smart_contract_id: service_contract},
        service_contract_configs_by_id={
            service_contract_config_id: _contract_config(
                service_contract_config_id=service_contract_config_id,
                operation_grants=[grant],
            )
        },
        now=now,
    )

    assert evidence.access_granted is True
    assert evidence.service_contract_config_operation_grant_id == grant.id


def test_service_access_evidence_has_no_resource_pricing_boundary() -> None:
    evidence_field_names = {field.name for field in fields(ServiceAccessEvidence)}
    assert "environment_id" not in evidence_field_names
    assert "process_id" not in evidence_field_names
    assert "thread_id" not in evidence_field_names
    assert "layout_id" not in evidence_field_names

    source = Path(access_module.__file__).read_text()
    assert "aware_environment" not in source


def _subscription(
    *,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    smart_contract_id: UUID | None = None,
    status: ServiceSubscriptionStatus,
    current_period_start: datetime,
    current_period_end: datetime,
    cancel_at_period_end: bool = False,
) -> ServiceSubscription:
    return ServiceSubscription.model_construct(
        id=uuid4(),
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_id=service_id,
        plan_id=uuid4(),
        contract_id=smart_contract_id or uuid4(),
        external_subscription_handle="sub_test",
        status=status,
        current_period_start=current_period_start,
        current_period_end=current_period_end,
        cancel_at_period_end=cancel_at_period_end,
        metadata_json={},
    )


def _service_contract(
    *,
    service_id: UUID,
    service_contract_config_id: UUID | None = None,
    consumer_finance_entity_id: UUID,
    smart_contract_id: UUID,
    status: ServiceContractStatus,
    effective_from: datetime,
    effective_until: datetime,
) -> ServiceContract:
    return ServiceContract.model_construct(
        id=uuid4(),
        service_id=service_id,
        service_contract_config_id=service_contract_config_id or uuid4(),
        commercial_profile_id=uuid4(),
        producer_finance_entity_id=uuid4(),
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        kind=ServiceContractKind.subscription,
        effective_from=effective_from,
        effective_until=effective_until,
        status=status,
        metadata_json={},
    )


def _contract_config(
    *,
    service_contract_config_id: UUID,
    operation_grants: list[ServiceContractConfigOperationGrant],
) -> ServiceContractConfig:
    return ServiceContractConfig.model_construct(
        id=service_contract_config_id,
        service_config_id=uuid4(),
        name="Default contract",
        default_kind=ServiceContractKind.subscription,
        projection_experience_id=None,
        description=None,
        metadata_json={},
        operation_grants=operation_grants,
        actor_role_grants=[],
    )


def _operation_grant(
    *,
    service_contract_config_id: UUID,
    service_operation_config_id: UUID,
) -> ServiceContractConfigOperationGrant:
    return ServiceContractConfigOperationGrant.model_construct(
        id=uuid4(),
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
        access_scope="operation",
        quota_policy_json={},
        permit_policy_json={},
        price_policy_json={},
        description=None,
    )
