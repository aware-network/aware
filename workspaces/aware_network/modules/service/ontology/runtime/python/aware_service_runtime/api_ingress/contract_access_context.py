from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar, cast
from uuid import UUID

from aware_code.types import JsonObject
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.session import Session
from aware_service_ontology.service.service_contract import ServiceContract
from aware_service_ontology.service.service_contract_config import ServiceContractConfig
from aware_service_ontology.service.service_contract_config_operation_grant import (
    ServiceContractConfigOperationGrant,
)
from aware_service_ontology.service.service_enums import (
    ServiceContractStatus,
    ServiceSubscriptionStatus,
)
from aware_service_ontology.service.service_subscription import ServiceSubscription

from aware_service_runtime.api_ingress.admission_context import (
    ServiceContractAccessContextRef,
    ServiceOperationAdmissionContext,
    service_contract_access_context_ref_payload,
)

_T = TypeVar("_T", bound=BaseORMModel)


@dataclass(frozen=True, slots=True)
class ServiceOperationAccessContext:
    consumer_finance_entity_id: UUID
    subscriptions: tuple[ServiceSubscription, ...] = ()
    service_contracts_by_smart_contract_id: Mapping[UUID, ServiceContract] | None = None
    service_contract_configs_by_id: Mapping[UUID, ServiceContractConfig] | None = None
    now: datetime | None = None


@dataclass(frozen=True, slots=True)
class ServiceContractAccessContextResolution:
    schema: str = "aware.service.contract_access_context_resolution.v0"
    status: str = "missing_ref"
    resolved: bool = False
    source: str = "service_runtime.contract_access_context"
    blocker: str | None = None
    blockers: tuple[str, ...] = ()
    next_action: str | None = None
    consumer_finance_entity_id: UUID | None = None
    service_subscription_id: UUID | None = None
    service_contract_id: UUID | None = None
    service_contract_config_id: UUID | None = None
    smart_contract_id: UUID | None = None
    contract_access_context_ref: ServiceContractAccessContextRef | None = None


@dataclass(frozen=True, slots=True)
class ResolvedServiceContractAccessContext:
    access_context: ServiceOperationAccessContext | None
    resolution: ServiceContractAccessContextResolution


@dataclass(frozen=True, slots=True)
class ServiceContractAccessContextBootstrapReadModel:
    schema: str = "aware.service.contract_access_context.bootstrap_read_model.v0"
    status: str = "blocked"
    ready: bool = False
    source: str = "service_runtime.contract_access_context_bootstrap"
    service_id: UUID | None = None
    service_operation_config_id: UUID | None = None
    consumer_finance_entity_id: UUID | None = None
    service_subscription_id: UUID | None = None
    service_contract_id: UUID | None = None
    service_contract_config_id: UUID | None = None
    smart_contract_id: UUID | None = None
    blocker: str | None = None
    blockers: tuple[str, ...] = ()
    next_action: str | None = None
    contract_access_context_ref: ServiceContractAccessContextRef | None = None


def read_service_contract_access_context_bootstrap(
    *,
    session: Session,
    service_id: UUID,
    consumer_finance_entity_id: UUID | None,
    service_operation_config_id: UUID | None = None,
    service_subscription_id: UUID | None = None,
    service_contract_id: UUID | None = None,
    service_contract_config_id: UUID | None = None,
    smart_contract_id: UUID | None = None,
) -> ServiceContractAccessContextBootstrapReadModel:
    """Build the caller-carried contract access refs from Service-owned truth."""

    if consumer_finance_entity_id is None:
        return _bootstrap_read_model(
            service_id=service_id,
            service_operation_config_id=service_operation_config_id,
            consumer_finance_entity_id=None,
            service_subscription_id=service_subscription_id,
            service_contract_id=service_contract_id,
            service_contract_config_id=service_contract_config_id,
            smart_contract_id=smart_contract_id,
            blockers=("missing_consumer_finance_entity_id",),
        )

    subscription = _resolve_service_subscription(
        session=session,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_subscription_id=service_subscription_id,
        smart_contract_id=smart_contract_id,
    )
    effective_smart_contract_id = smart_contract_id or (
        subscription.contract_id if subscription is not None else None
    )
    service_contract = _resolve_service_contract(
        session=session,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_contract_id=service_contract_id,
        smart_contract_id=effective_smart_contract_id,
    )
    effective_contract_config_id = service_contract_config_id or (
        service_contract.service_contract_config_id
        if service_contract is not None
        else None
    )
    service_contract_config = _optional_imap_get(
        session=session,
        model=ServiceContractConfig,
        object_id=effective_contract_config_id,
    )

    blockers = _bootstrap_blockers(
        subscription=subscription,
        service_contract=service_contract,
        service_contract_config=service_contract_config,
    )
    if (
        service_operation_config_id is not None
        and service_contract_config is not None
        and not _contract_config_grants_operation(
            service_contract_config=service_contract_config,
            service_operation_config_id=service_operation_config_id,
        )
    ):
        blockers = (*blockers, "operation_not_granted")
    blockers = tuple(dict.fromkeys(blockers))
    return _bootstrap_read_model(
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_subscription_id=(
            subscription.id if subscription is not None else service_subscription_id
        ),
        service_contract_id=(
            service_contract.id if service_contract is not None else service_contract_id
        ),
        service_contract_config_id=(
            service_contract_config.id
            if service_contract_config is not None
            else effective_contract_config_id
        ),
        smart_contract_id=effective_smart_contract_id
        or (
            service_contract.smart_contract_id if service_contract is not None else None
        ),
        blockers=blockers,
    )


def service_contract_access_context_bootstrap_payload(
    read_model: ServiceContractAccessContextBootstrapReadModel,
) -> JsonObject:
    return _drop_none(
        {
            "schema": read_model.schema,
            "status": read_model.status,
            "ready": read_model.ready,
            "source": read_model.source,
            "service_id": _uuid_text(read_model.service_id),
            "service_operation_config_id": _uuid_text(
                read_model.service_operation_config_id
            ),
            "consumer_finance_entity_id": _uuid_text(
                read_model.consumer_finance_entity_id
            ),
            "service_subscription_id": _uuid_text(read_model.service_subscription_id),
            "service_contract_id": _uuid_text(read_model.service_contract_id),
            "service_contract_config_id": _uuid_text(
                read_model.service_contract_config_id
            ),
            "smart_contract_id": _uuid_text(read_model.smart_contract_id),
            "blocker": read_model.blocker,
            "blockers": list(read_model.blockers),
            "next_action": read_model.next_action,
            "service_contract_access_context": (
                service_contract_access_context_ref_payload(
                    read_model.contract_access_context_ref
                )
            ),
        }
    )


def resolve_service_contract_access_context_from_admission(
    *,
    session: Session,
    admission_context: ServiceOperationAdmissionContext | None,
    now: datetime | None = None,
) -> ResolvedServiceContractAccessContext:
    ref = (
        admission_context.contract_access_context_ref
        if admission_context is not None
        else None
    )
    if ref is None:
        return ResolvedServiceContractAccessContext(
            access_context=None,
            resolution=_resolution(
                status="missing_ref",
                resolved=False,
                blocker="missing_contract_access_context",
                next_action="resolve_service_contract_context",
                ref=None,
            ),
        )
    if ref.consumer_finance_entity_id is None:
        return ResolvedServiceContractAccessContext(
            access_context=None,
            resolution=_resolution(
                status="blocked",
                resolved=False,
                blocker="missing_consumer_finance_entity_id",
                next_action="resolve_service_contract_context",
                ref=ref,
            ),
        )

    subscription = _optional_imap_get(
        session=session,
        model=ServiceSubscription,
        object_id=ref.service_subscription_id,
    )
    service_contract = _optional_imap_get(
        session=session,
        model=ServiceContract,
        object_id=ref.service_contract_id,
    )
    contract_config_id = ref.service_contract_config_id or (
        service_contract.service_contract_config_id
        if service_contract is not None
        else None
    )
    service_contract_config = _optional_imap_get(
        session=session,
        model=ServiceContractConfig,
        object_id=contract_config_id,
    )

    blockers = _hydration_blockers(
        ref=ref,
        subscription=subscription,
        service_contract=service_contract,
        service_contract_config=service_contract_config,
    )
    access_context = ServiceOperationAccessContext(
        consumer_finance_entity_id=ref.consumer_finance_entity_id,
        subscriptions=(subscription,) if subscription is not None else (),
        service_contracts_by_smart_contract_id=(
            {service_contract.smart_contract_id: service_contract}
            if service_contract is not None
            else {}
        ),
        service_contract_configs_by_id=(
            {service_contract_config.id: service_contract_config}
            if service_contract_config is not None
            else {}
        ),
        now=now,
    )
    return ResolvedServiceContractAccessContext(
        access_context=access_context,
        resolution=_resolution(
            status="resolved" if not blockers else "partial",
            resolved=not blockers,
            blocker=blockers[0] if blockers else None,
            blockers=blockers,
            next_action="resolve_service_contract_context" if blockers else None,
            ref=ref,
        ),
    )


def service_contract_access_context_resolution_payload(
    resolution: ServiceContractAccessContextResolution | None,
) -> JsonObject | None:
    if resolution is None:
        return None
    return _drop_none(
        {
            "schema": resolution.schema,
            "status": resolution.status,
            "resolved": resolution.resolved,
            "source": resolution.source,
            "blocker": resolution.blocker,
            "blockers": list(resolution.blockers),
            "next_action": resolution.next_action,
            "consumer_finance_entity_id": _uuid_text(
                resolution.consumer_finance_entity_id
            ),
            "service_subscription_id": _uuid_text(resolution.service_subscription_id),
            "service_contract_id": _uuid_text(resolution.service_contract_id),
            "service_contract_config_id": _uuid_text(
                resolution.service_contract_config_id
            ),
            "smart_contract_id": _uuid_text(resolution.smart_contract_id),
            "contract_access_context_ref": (
                service_contract_access_context_ref_payload(
                    resolution.contract_access_context_ref
                )
            ),
        }
    )


def _hydration_blockers(
    *,
    ref: ServiceContractAccessContextRef,
    subscription: ServiceSubscription | None,
    service_contract: ServiceContract | None,
    service_contract_config: ServiceContractConfig | None,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if ref.service_subscription_id is not None and subscription is None:
        blockers.append("service_subscription_not_found")
    if ref.service_contract_id is not None and service_contract is None:
        blockers.append("service_contract_not_found")
    if (
        ref.service_contract_config_id is not None or service_contract is not None
    ) and service_contract_config is None:
        blockers.append("service_contract_config_not_found")
    return tuple(dict.fromkeys(blockers))


def _bootstrap_blockers(
    *,
    subscription: ServiceSubscription | None,
    service_contract: ServiceContract | None,
    service_contract_config: ServiceContractConfig | None,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if subscription is None:
        blockers.append("missing_subscription")
    if service_contract is None:
        blockers.append("missing_service_contract")
    if service_contract_config is None:
        blockers.append("missing_contract_config")
    return tuple(blockers)


def _resolve_service_subscription(
    *,
    session: Session,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    service_subscription_id: UUID | None,
    smart_contract_id: UUID | None,
) -> ServiceSubscription | None:
    if service_subscription_id is not None:
        subscription = _optional_imap_get(
            session=session,
            model=ServiceSubscription,
            object_id=service_subscription_id,
        )
        if subscription is None:
            return None
        if not _subscription_matches(
            subscription=subscription,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            smart_contract_id=smart_contract_id,
        ):
            return None
        return subscription
    return _first(
        _matching_subscriptions(
            session=session,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            smart_contract_id=smart_contract_id,
        )
    )


def _resolve_service_contract(
    *,
    session: Session,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    service_contract_id: UUID | None,
    smart_contract_id: UUID | None,
) -> ServiceContract | None:
    if service_contract_id is not None:
        service_contract = _optional_imap_get(
            session=session,
            model=ServiceContract,
            object_id=service_contract_id,
        )
        if service_contract is None:
            return None
        if not _service_contract_matches(
            service_contract=service_contract,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            smart_contract_id=smart_contract_id,
        ):
            return None
        return service_contract
    return _first(
        _matching_service_contracts(
            session=session,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            smart_contract_id=smart_contract_id,
        )
    )


def _matching_subscriptions(
    *,
    session: Session,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    smart_contract_id: UUID | None,
) -> tuple[ServiceSubscription, ...]:
    return tuple(
        subscription
        for subscription in _objects_of_type(session, ServiceSubscription)
        if _subscription_matches(
            subscription=subscription,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            smart_contract_id=smart_contract_id,
        )
    )


def _matching_service_contracts(
    *,
    session: Session,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    smart_contract_id: UUID | None,
) -> tuple[ServiceContract, ...]:
    return tuple(
        service_contract
        for service_contract in _objects_of_type(session, ServiceContract)
        if _service_contract_matches(
            service_contract=service_contract,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            smart_contract_id=smart_contract_id,
        )
    )


def _subscription_matches(
    *,
    subscription: ServiceSubscription,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    smart_contract_id: UUID | None,
) -> bool:
    if subscription.service_id != service_id:
        return False
    if subscription.consumer_finance_entity_id != consumer_finance_entity_id:
        return False
    if subscription.status != ServiceSubscriptionStatus.active:
        return False
    if smart_contract_id is not None and subscription.contract_id != smart_contract_id:
        return False
    return True


def _service_contract_matches(
    *,
    service_contract: ServiceContract,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    smart_contract_id: UUID | None,
) -> bool:
    if service_contract.service_id != service_id:
        return False
    if service_contract.consumer_finance_entity_id != consumer_finance_entity_id:
        return False
    if service_contract.status != ServiceContractStatus.active:
        return False
    if (
        smart_contract_id is not None
        and service_contract.smart_contract_id != smart_contract_id
    ):
        return False
    return True


def _contract_config_grants_operation(
    *,
    service_contract_config: ServiceContractConfig,
    service_operation_config_id: UUID,
) -> bool:
    return any(
        grant.service_operation_config_id == service_operation_config_id
        for grant in _operation_grants(service_contract_config)
    )


def _operation_grants(
    service_contract_config: ServiceContractConfig,
) -> Sequence[ServiceContractConfigOperationGrant]:
    return tuple(service_contract_config.operation_grants or ())


def _objects_of_type(session: Session, model: type[_T]) -> tuple[_T, ...]:
    return tuple(obj for obj in session.imap_all_objects() if isinstance(obj, model))


def _first(values: Sequence[_T]) -> _T | None:
    return values[0] if values else None


def _bootstrap_read_model(
    *,
    service_id: UUID,
    service_operation_config_id: UUID | None,
    consumer_finance_entity_id: UUID | None,
    service_subscription_id: UUID | None,
    service_contract_id: UUID | None,
    service_contract_config_id: UUID | None,
    smart_contract_id: UUID | None,
    blockers: tuple[str, ...],
) -> ServiceContractAccessContextBootstrapReadModel:
    ready = not blockers
    ref = (
        ServiceContractAccessContextRef(
            consumer_finance_entity_id=consumer_finance_entity_id,
            service_subscription_id=service_subscription_id,
            service_contract_id=service_contract_id,
            service_contract_config_id=service_contract_config_id,
            smart_contract_id=smart_contract_id,
        )
        if ready and consumer_finance_entity_id is not None
        else None
    )
    return ServiceContractAccessContextBootstrapReadModel(
        status="ready" if ready else "blocked",
        ready=ready,
        service_id=service_id,
        service_operation_config_id=service_operation_config_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_subscription_id=service_subscription_id,
        service_contract_id=service_contract_id,
        service_contract_config_id=service_contract_config_id,
        smart_contract_id=smart_contract_id,
        blocker=blockers[0] if blockers else None,
        blockers=blockers,
        next_action=_bootstrap_next_action(blockers),
        contract_access_context_ref=ref,
    )


def _bootstrap_next_action(blockers: tuple[str, ...]) -> str | None:
    if not blockers:
        return None
    first_blocker = blockers[0]
    return {
        "missing_consumer_finance_entity_id": "resolve_consumer_finance_entity",
        "missing_subscription": "resolve_service_subscription",
        "missing_service_contract": "resolve_service_contract",
        "missing_contract_config": "resolve_service_contract_config",
        "missing_service_operation_config": "resolve_service_operation_config",
        "operation_not_granted": "grant_service_operation",
    }.get(first_blocker, "resolve_service_contract_context")


def _optional_imap_get(
    *,
    session: Session,
    model: type[_T],
    object_id: UUID | None,
) -> _T | None:
    if object_id is None:
        return None
    return session.imap_get(model, object_id)


def _resolution(
    *,
    status: str,
    resolved: bool,
    blocker: str | None = None,
    blockers: tuple[str, ...] = (),
    next_action: str | None,
    ref: ServiceContractAccessContextRef | None,
) -> ServiceContractAccessContextResolution:
    all_blockers = blockers or ((blocker,) if blocker else ())
    return ServiceContractAccessContextResolution(
        status=status,
        resolved=resolved,
        blocker=blocker,
        blockers=all_blockers,
        next_action=next_action,
        consumer_finance_entity_id=(
            ref.consumer_finance_entity_id if ref is not None else None
        ),
        service_subscription_id=(
            ref.service_subscription_id if ref is not None else None
        ),
        service_contract_id=ref.service_contract_id if ref is not None else None,
        service_contract_config_id=(
            ref.service_contract_config_id if ref is not None else None
        ),
        smart_contract_id=ref.smart_contract_id if ref is not None else None,
        contract_access_context_ref=ref,
    )


def _uuid_text(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _drop_none(payload: Mapping[str, object | None]) -> JsonObject:
    return cast(
        JsonObject,
        {key: value for key, value in payload.items() if value is not None},
    )


__all__ = [
    "ResolvedServiceContractAccessContext",
    "ServiceContractAccessContextBootstrapReadModel",
    "ServiceContractAccessContextResolution",
    "ServiceOperationAccessContext",
    "read_service_contract_access_context_bootstrap",
    "resolve_service_contract_access_context_from_admission",
    "service_contract_access_context_bootstrap_payload",
    "service_contract_access_context_resolution_payload",
]
