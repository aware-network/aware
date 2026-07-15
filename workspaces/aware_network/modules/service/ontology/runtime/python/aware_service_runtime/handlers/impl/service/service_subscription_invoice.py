from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_enums import ServiceSubscriptionInvoiceStatus
from aware_service_ontology.service.service_subscription_invoice import ServiceSubscriptionInvoice

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_economy_ontology.coin.coin import Coin
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.service.service_subscription import ServiceSubscription
from aware_service_ontology.stable_ids import stable_service_subscription_invoice_id

# --- AWARE: USER_IMPORTS END


async def build_via_service_subscription(
    service_subscription_id: UUID,
    amount: Annotated[Decimal, DecimalWire()],
    coin_id: UUID,
    external_invoice_handle: str | None = None,
    status: ServiceSubscriptionInvoiceStatus = ServiceSubscriptionInvoiceStatus.open,
) -> ServiceSubscriptionInvoice:
    """
    Records one invoice under a ServiceSubscription.
    """

    # --- AWARE: LOGIC START build_via_service_subscription
    if amount <= 0:
        raise ValueError("ServiceSubscriptionInvoice.build_via_service_subscription requires amount > 0")

    session = current_handler_session()
    _ = session.imap_get(ServiceSubscription, service_subscription_id)
    _ = session.imap_get(Coin, coin_id)

    invoice_id = stable_service_subscription_invoice_id(
        service_subscription_id=service_subscription_id,
        coin_id=coin_id,
        amount=amount,
    )
    external_invoice_handle_norm = (external_invoice_handle or "").strip() or None

    existing = session.imap_get(ServiceSubscriptionInvoice, invoice_id)
    if existing is not None:
        if (
            existing.service_subscription_id != service_subscription_id
            or existing.coin_id != coin_id
            or existing.amount != amount
        ):
            raise RuntimeError(
                "ServiceSubscriptionInvoice.build_via_service_subscription payload mismatch for existing invoice: "
                + f"service_subscription_invoice_id={invoice_id}"
            )
        if external_invoice_handle_norm is not None:
            existing.external_invoice_handle = external_invoice_handle_norm
        existing.status = status
        return existing

    return ServiceSubscriptionInvoice(
        id=invoice_id,
        service_subscription_id=service_subscription_id,
        amount=amount,
        coin_id=coin_id,
        external_invoice_handle=external_invoice_handle_norm,
        status=status,
    )
    # --- AWARE: LOGIC END build_via_service_subscription
