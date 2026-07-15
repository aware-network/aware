from __future__ import annotations

# Standard
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Service Ontology Dto
from aware_service_ontology_dto.service.service_enums import ServiceSubscriptionInvoiceStatus

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin import Coin


class ServiceSubscriptionInvoice(BaseModel):
    # Relationships
    coin: Coin | None = Field(default=None)

    # Attributes
    amount: Annotated[Decimal, DecimalWire()]
    external_invoice_handle: str | None = Field(default=None)
    status: ServiceSubscriptionInvoiceStatus = Field(default=ServiceSubscriptionInvoiceStatus.open)
