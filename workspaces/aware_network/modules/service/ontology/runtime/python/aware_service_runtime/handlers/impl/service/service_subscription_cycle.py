from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_enums import ServiceSubscriptionCycleStatus
from aware_service_ontology.service.service_subscription_cycle import ServiceSubscriptionCycle

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.service.service_subscription import ServiceSubscription
from aware_service_ontology.service.service_subscription_invoice import ServiceSubscriptionInvoice
from aware_service_ontology.stable_ids import stable_service_subscription_cycle_id

# --- AWARE: USER_IMPORTS END


async def build_via_service_subscription(
    service_subscription_id: UUID,
    cycle_number: int,
    period_start: datetime,
    period_end: datetime,
    status: ServiceSubscriptionCycleStatus = ServiceSubscriptionCycleStatus.pending,
    invoice_id: UUID | None = None,
) -> ServiceSubscriptionCycle:
    """
    Records one billing cycle under a ServiceSubscription.
    """

    # --- AWARE: LOGIC START build_via_service_subscription
    if cycle_number <= 0:
        raise ValueError("ServiceSubscriptionCycle.build_via_service_subscription requires cycle_number > 0")
    if period_end <= period_start:
        raise ValueError(
            "ServiceSubscriptionCycle.build_via_service_subscription requires period_end after period_start"
        )

    session = current_handler_session()
    _ = session.imap_get(ServiceSubscription, service_subscription_id)

    if invoice_id is not None:
        invoice = session.imap_get(ServiceSubscriptionInvoice, invoice_id)
        if invoice is not None and invoice.service_subscription_id != service_subscription_id:
            raise RuntimeError(
                "ServiceSubscriptionCycle.build_via_service_subscription invoice does not belong to subscription: "
                + f"service_subscription_id={service_subscription_id} "
                + f"invoice_id={invoice_id}"
            )

    cycle_id = stable_service_subscription_cycle_id(
        service_subscription_id=service_subscription_id,
        cycle_number=cycle_number,
    )
    existing = session.imap_get(ServiceSubscriptionCycle, cycle_id)
    if existing is not None:
        if (
            existing.service_subscription_id != service_subscription_id
            or existing.cycle_number != cycle_number
            or existing.period_start != period_start
            or existing.period_end != period_end
        ):
            raise RuntimeError(
                "ServiceSubscriptionCycle.build_via_service_subscription payload mismatch for existing cycle: "
                + f"service_subscription_cycle_id={cycle_id}"
            )
        if invoice_id is not None:
            if existing.invoice_id is not None and existing.invoice_id != invoice_id:
                raise RuntimeError(
                    "ServiceSubscriptionCycle.build_via_service_subscription invoice mismatch for existing cycle: "
                    + f"service_subscription_cycle_id={cycle_id}"
                )
            existing.invoice_id = invoice_id
        existing.status = status
        return existing

    return ServiceSubscriptionCycle(
        id=cycle_id,
        service_subscription_id=service_subscription_id,
        cycle_number=cycle_number,
        period_start=period_start,
        period_end=period_end,
        status=status,
        invoice_id=invoice_id,
    )
    # --- AWARE: LOGIC END build_via_service_subscription
