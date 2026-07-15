from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Service Ontology
from aware_service_ontology.service.service_enums import (
    ServiceSubscriptionCycleStatus,
    ServiceSubscriptionInvoiceStatus,
    ServiceSubscriptionStatus,
)
from aware_service_ontology.service.service_subscription import ServiceSubscription
from aware_service_ontology.service.service_subscription_cycle import ServiceSubscriptionCycle
from aware_service_ontology.service.service_subscription_invoice import ServiceSubscriptionInvoice

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from typing import cast

from aware_economy_ontology.finance.finance_entity import FinanceEntity
from aware_economy_ontology.smart_contract.smart_contract import SmartContract
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_plan import ServicePlan
from aware_service_ontology.stable_ids import stable_service_subscription_id

# --- AWARE: USER_IMPORTS END


async def build(
    consumer_finance_entity_id: UUID,
    service_id: UUID,
    plan_id: UUID,
    contract_id: UUID,
    external_subscription_handle: str | None = None,
    status: ServiceSubscriptionStatus = ServiceSubscriptionStatus.active,
    current_period_start: datetime | None = None,
    current_period_end: datetime | None = None,
    cancel_at_period_end: bool = False,
    metadata_json: JsonObject | None = None,
) -> ServiceSubscription:
    """
    Creates or upserts one consumer subscription receipt for a canonical Service.
    """

    # --- AWARE: LOGIC START build
    if (
        current_period_start is not None
        and current_period_end is not None
        and current_period_end <= current_period_start
    ):
        raise ValueError("ServiceSubscription.build requires current_period_end after current_period_start")

    session = current_handler_session()
    _ = session.imap_get(Service, service_id)
    _ = session.imap_get(FinanceEntity, consumer_finance_entity_id)
    _ = session.imap_get(SmartContract, contract_id)

    plan = session.imap_get(ServicePlan, plan_id)
    if plan is not None and plan.service_id != service_id:
        raise RuntimeError(
            "ServiceSubscription.build plan does not belong to referenced service: "
            + f"service_id={service_id} "
            + f"plan_id={plan_id}"
        )

    subscription_id = stable_service_subscription_id(
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_id=service_id,
    )
    metadata_payload = cast(JsonObject, dict(metadata_json)) if metadata_json is not None else None

    existing = session.imap_get(ServiceSubscription, subscription_id)
    if existing is not None:
        if (
            existing.consumer_finance_entity_id != consumer_finance_entity_id
            or existing.service_id != service_id
            or existing.plan_id != plan_id
            or existing.contract_id != contract_id
        ):
            raise RuntimeError(
                "ServiceSubscription.build payload mismatch for existing subscription: "
                + f"service_subscription_id={subscription_id}"
            )
        if current_period_start is not None:
            existing.current_period_start = current_period_start
        if current_period_end is not None:
            existing.current_period_end = current_period_end
        if external_subscription_handle is not None:
            existing.external_subscription_handle = external_subscription_handle
        existing.cancel_at_period_end = cancel_at_period_end
        existing.status = status
        if metadata_payload is not None:
            existing.metadata_json = metadata_payload
        return existing

    return ServiceSubscription(
        id=subscription_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_id=service_id,
        plan_id=plan_id,
        contract_id=contract_id,
        external_subscription_handle=external_subscription_handle,
        status=status,
        current_period_start=current_period_start,
        current_period_end=current_period_end,
        cancel_at_period_end=cancel_at_period_end,
        metadata_json=metadata_payload,
    )
    # --- AWARE: LOGIC END build


async def create_cycle(
    service_subscription: ServiceSubscription,
    cycle_number: int,
    period_start: datetime,
    period_end: datetime,
    status: ServiceSubscriptionCycleStatus = ServiceSubscriptionCycleStatus.pending,
    invoice_id: UUID | None = None,
) -> ServiceSubscriptionCycle:
    """
    Appends one billing cycle receipt under this ServiceSubscription.
    """

    # --- AWARE: LOGIC START create_cycle
    created = await ServiceSubscriptionCycle.build_via_service_subscription(
        service_subscription_id=service_subscription.id,
        cycle_number=cycle_number,
        period_start=period_start,
        period_end=period_end,
        status=status,
        invoice_id=invoice_id,
    )
    invoice = None
    if invoice_id is not None:
        invoice = current_handler_session().imap_get(ServiceSubscriptionInvoice, invoice_id)
        if invoice is not None:
            created.invoice = invoice
    for existing in service_subscription.cycles:
        if existing.id == created.id:
            if invoice is not None:
                existing.invoice = invoice
            return existing
    service_subscription.cycles.append(created)
    return created
    # --- AWARE: LOGIC END create_cycle


async def create_invoice(
    service_subscription: ServiceSubscription,
    amount: Annotated[Decimal, DecimalWire()],
    coin_id: UUID,
    external_invoice_handle: str | None = None,
    status: ServiceSubscriptionInvoiceStatus = ServiceSubscriptionInvoiceStatus.open,
) -> ServiceSubscriptionInvoice:
    """
    Appends one invoice receipt under this ServiceSubscription.
    """

    # --- AWARE: LOGIC START create_invoice
    if amount <= 0:
        raise ValueError("ServiceSubscription.create_invoice requires amount > 0")

    session = current_handler_session()
    plan = session.imap_get(ServicePlan, service_subscription.plan_id)
    if plan is not None and plan.coin_id != coin_id:
        raise RuntimeError(
            "ServiceSubscription.create_invoice requires coin_id to match the subscription plan currency: "
            + f"service_subscription_id={service_subscription.id} "
            + f"plan_id={service_subscription.plan_id}"
        )

    created = await ServiceSubscriptionInvoice.build_via_service_subscription(
        service_subscription_id=service_subscription.id,
        amount=amount,
        coin_id=coin_id,
        external_invoice_handle=external_invoice_handle,
        status=status,
    )
    for existing in service_subscription.invoices:
        if existing.id == created.id:
            return existing
    service_subscription.invoices.append(created)
    return created
    # --- AWARE: LOGIC END create_invoice
