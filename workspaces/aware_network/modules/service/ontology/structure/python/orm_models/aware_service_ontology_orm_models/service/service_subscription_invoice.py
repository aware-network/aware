from __future__ import annotations

# Standard
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Service Ontology Orm Models
from aware_service_ontology_orm_models.service.service_enums import ServiceSubscriptionInvoiceStatus

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin import Coin


class ServiceSubscriptionInvoice(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)

    # Attributes
    amount: Annotated[Decimal, DecimalWire()]
    external_invoice_handle: str | None = Field(default=None)
    status: ServiceSubscriptionInvoiceStatus = Field(default=ServiceSubscriptionInvoiceStatus.open)

    # Foreign Keys
    service_subscription_id: UUID = Field(description="Foreign key for ServiceSubscription.invoices")
    coin_id: UUID = Field(description="Foreign key for ServiceSubscriptionInvoice.coin")
