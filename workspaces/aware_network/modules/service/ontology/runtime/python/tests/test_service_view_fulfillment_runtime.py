from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from aware_orm.session.session import Session
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_contract import ServiceContract
from aware_service_ontology.service.service_contract_config import ServiceContractConfig
from aware_service_ontology.service.service_contract_config_operation_grant import (
    ServiceContractConfigOperationGrant,
)
from aware_service_ontology.service.service_enums import (
    ServiceContractKind,
    ServiceContractStatus,
    ServiceOperationAdmissionMode,
    ServiceSubscriptionStatus,
)
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.service.service_operation_config_api_view import (
    ServiceOperationConfigApiView,
)
from aware_service_ontology.service.service_operation_config_role_requirement import (
    ServiceOperationConfigRoleRequirement,
)
from aware_service_ontology.service.service_subscription import ServiceSubscription
from aware_service_runtime.api_ingress.execution import (
    ServiceActorRoleEvidence,
    ServiceOperationAccessContext,
)
from aware_service_runtime.api_ingress.view_fulfillment import (
    resolve_service_api_view_fulfillment,
)


def test_service_view_fulfillment_resolves_operation_grant_preflight() -> None:
    now = datetime(2026, 5, 12, tzinfo=UTC)
    (
        session,
        service_id,
        api_view_id,
        service_operation_config_id,
        _,
    ) = _view_fulfillment_session()
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_contract_config_id = uuid4()
    grant = _operation_grant(
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
    )

    plan = resolve_service_api_view_fulfillment(
        session=session,
        service_id=service_id,
        api_view_id=api_view_id,
        actor_id=None,
        operation_access_context=ServiceOperationAccessContext(
            consumer_finance_entity_id=consumer_finance_entity_id,
            subscriptions=(
                _subscription(
                    service_id=service_id,
                    consumer_finance_entity_id=consumer_finance_entity_id,
                    smart_contract_id=smart_contract_id,
                    now=now,
                ),
            ),
            service_contracts_by_smart_contract_id={
                smart_contract_id: _service_contract(
                    service_id=service_id,
                    service_contract_config_id=service_contract_config_id,
                    consumer_finance_entity_id=consumer_finance_entity_id,
                    smart_contract_id=smart_contract_id,
                    now=now,
                )
            },
            service_contract_configs_by_id={
                service_contract_config_id: _contract_config(
                    service_contract_config_id=service_contract_config_id,
                    operation_grants=(grant,),
                )
            },
            now=now,
        ),
    )

    assert plan.service_id == service_id
    assert plan.api_view_id == api_view_id
    assert plan.service_operation_config_id == service_operation_config_id
    assert plan.preflight.access_evidence is not None
    assert plan.preflight.access_evidence.access_granted is True
    assert (
        plan.preflight.access_evidence.service_contract_config_operation_grant_id
        == grant.id
    )


def test_service_view_fulfillment_denies_missing_operation_grant() -> None:
    now = datetime(2026, 5, 12, tzinfo=UTC)
    (
        session,
        service_id,
        api_view_id,
        _,
        _,
    ) = _view_fulfillment_session()
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    service_contract_config_id = uuid4()

    with pytest.raises(PermissionError, match="missing_operation_grant"):
        resolve_service_api_view_fulfillment(
            session=session,
            service_id=service_id,
            api_view_id=api_view_id,
            actor_id=None,
            operation_access_context=ServiceOperationAccessContext(
                consumer_finance_entity_id=consumer_finance_entity_id,
                subscriptions=(
                    _subscription(
                        service_id=service_id,
                        consumer_finance_entity_id=consumer_finance_entity_id,
                        smart_contract_id=smart_contract_id,
                        now=now,
                    ),
                ),
                service_contracts_by_smart_contract_id={
                    smart_contract_id: _service_contract(
                        service_id=service_id,
                        service_contract_config_id=service_contract_config_id,
                        consumer_finance_entity_id=consumer_finance_entity_id,
                        smart_contract_id=smart_contract_id,
                        now=now,
                    )
                },
                service_contract_configs_by_id={
                    service_contract_config_id: _contract_config(
                        service_contract_config_id=service_contract_config_id,
                        operation_grants=(),
                    )
                },
                now=now,
            ),
        )


def test_service_view_fulfillment_requires_actor_role_evidence() -> None:
    (
        session,
        service_id,
        api_view_id,
        _,
        role_config_id,
    ) = _view_fulfillment_session(with_role_requirement=True)

    with pytest.raises(PermissionError, match="actor_id is required"):
        resolve_service_api_view_fulfillment(
            session=session,
            service_id=service_id,
            api_view_id=api_view_id,
            actor_id=None,
        )

    with pytest.raises(PermissionError, match=str(role_config_id)):
        resolve_service_api_view_fulfillment(
            session=session,
            service_id=service_id,
            api_view_id=api_view_id,
            actor_id=uuid4(),
        )


def test_service_view_fulfillment_accepts_actor_role_evidence() -> None:
    (
        session,
        service_id,
        api_view_id,
        service_operation_config_id,
        role_config_id,
    ) = _view_fulfillment_session(with_role_requirement=True)
    actor_id = uuid4()

    plan = resolve_service_api_view_fulfillment(
        session=session,
        service_id=service_id,
        api_view_id=api_view_id,
        actor_id=actor_id,
        actor_role_evidence=(
            ServiceActorRoleEvidence(
                actor_id=actor_id,
                role_config_id=role_config_id,
                access_scope="operation",
                scope_kind="operation",
                scope_ref="default",
                role_assignment_binding_id=uuid4(),
            ),
        ),
    )

    assert plan.service_operation_config_id == service_operation_config_id
    assert len(plan.preflight.actor_role_evidence) == 1
    assert plan.preflight.actor_role_evidence[0].role_config_id == role_config_id


def test_service_view_fulfillment_rejects_ambiguous_service_operation_configs() -> None:
    (
        session,
        service_id,
        api_view_id,
        _,
        _,
    ) = _view_fulfillment_session()
    service = session.imap_get(Service, service_id)
    assert service is not None
    second_operation_config_id = uuid4()
    session.imap_add(
        ServiceOperationConfig(
            id=second_operation_config_id,
            service_config_id=service.service_config_id,
            name="same_view_alt",
            description=None,
        )
    )
    session.imap_add(
        ServiceOperationConfigApiView(
            id=uuid4(),
            service_operation_config_id=second_operation_config_id,
            service_config_api_id=uuid4(),
            api_view_id=api_view_id,
            description=None,
        )
    )

    with pytest.raises(RuntimeError, match="exactly one"):
        resolve_service_api_view_fulfillment(
            session=session,
            service_id=service_id,
            api_view_id=api_view_id,
            actor_id=None,
        )


def _view_fulfillment_session(
    *, with_role_requirement: bool = False
) -> tuple[Session, UUID, UUID, UUID, UUID]:
    session = Session(branch_id=uuid4(), skip_db=True)
    service_config_id = uuid4()
    service_config_api_id = uuid4()
    service_id = uuid4()
    service_operation_config_id = uuid4()
    api_view_id = uuid4()
    role_config_id = uuid4()

    operation_config = ServiceOperationConfig(
        id=service_operation_config_id,
        service_config_id=service_config_id,
        name="identity_admission_view",
        admission_mode=(
            ServiceOperationAdmissionMode.identity_required
            if with_role_requirement
            else ServiceOperationAdmissionMode.contract_required
        ),
        description=None,
    )
    if with_role_requirement:
        operation_config.role_requirements.append(
            ServiceOperationConfigRoleRequirement(
                id=uuid4(),
                service_operation_config_id=service_operation_config_id,
                role_config_id=role_config_id,
                access_scope="operation",
                scope_kind="operation",
                scope_ref="default",
                class_instance_identity_required=False,
                role_assignment_binding_required=True,
                description=None,
            )
        )

    for obj in (
        Service(
            id=service_id,
            service_config_id=service_config_id,
            name="identity_service",
            description=None,
        ),
        operation_config,
        ServiceOperationConfigApiView(
            id=uuid4(),
            service_operation_config_id=service_operation_config_id,
            service_config_api_id=service_config_api_id,
            api_view_id=api_view_id,
            description=None,
        ),
    ):
        session.imap_add(obj)

    return (
        session,
        service_id,
        api_view_id,
        service_operation_config_id,
        role_config_id,
    )


def _subscription(
    *,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    smart_contract_id: UUID,
    now: datetime,
) -> ServiceSubscription:
    return ServiceSubscription.model_construct(
        id=uuid4(),
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_id=service_id,
        plan_id=uuid4(),
        contract_id=smart_contract_id,
        external_subscription_handle="sub_test",
        status=ServiceSubscriptionStatus.active,
        current_period_start=now - timedelta(days=1),
        current_period_end=now + timedelta(days=29),
        cancel_at_period_end=False,
        metadata_json={},
    )


def _service_contract(
    *,
    service_id: UUID,
    service_contract_config_id: UUID,
    consumer_finance_entity_id: UUID,
    smart_contract_id: UUID,
    now: datetime,
) -> ServiceContract:
    return ServiceContract.model_construct(
        id=uuid4(),
        service_id=service_id,
        service_contract_config_id=service_contract_config_id,
        commercial_profile_id=uuid4(),
        producer_finance_entity_id=uuid4(),
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        kind=ServiceContractKind.subscription,
        effective_from=now - timedelta(days=1),
        effective_until=now + timedelta(days=365),
        status=ServiceContractStatus.active,
        metadata_json={},
    )


def _contract_config(
    *,
    service_contract_config_id: UUID,
    operation_grants: tuple[ServiceContractConfigOperationGrant, ...],
) -> ServiceContractConfig:
    return ServiceContractConfig.model_construct(
        id=service_contract_config_id,
        service_config_id=uuid4(),
        name="Default contract",
        default_kind=ServiceContractKind.subscription,
        projection_experience_id=None,
        description=None,
        metadata_json={},
        operation_grants=list(operation_grants),
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
