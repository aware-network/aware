from __future__ import annotations

# Standard
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Service Ontology
from aware_service_ontology.service.service_enums import ServiceSubscriptionInvoiceStatus

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology.coin.coin import Coin


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

    @classmethod
    async def build_via_service_subscription(
        cls,
        service_subscription_id: UUID,
        amount: Annotated[Decimal, DecimalWire()],
        coin_id: UUID,
        external_invoice_handle: str | None = None,
        status: ServiceSubscriptionInvoiceStatus = ServiceSubscriptionInvoiceStatus.open,
    ) -> ServiceSubscriptionInvoice:
        """Records one invoice under a ServiceSubscription."""

        payload = {
            "service_subscription_id": service_subscription_id,
            "amount": amount,
            "coin_id": coin_id,
            "external_invoice_handle": external_invoice_handle,
            "status": status,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_service_subscription", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceSubscriptionInvoice):
            return value
        return ServiceSubscriptionInvoice.validate_invocation_value(value)


class ServiceSubscriptionInvoiceBuildViaServiceSubscriptionInput(BaseModel):
    service_subscription_id: UUID = Field(description="Foreign key for ServiceSubscription.invoices")
    amount: Annotated[Decimal, DecimalWire()]
    coin_id: UUID
    external_invoice_handle: str | None = Field(default=None)
    status: ServiceSubscriptionInvoiceStatus = Field(default=ServiceSubscriptionInvoiceStatus.open)


class ServiceSubscriptionInvoiceBuildViaServiceSubscriptionOutput(BaseModel):
    value: ServiceSubscriptionInvoice


FUNCTIONS = {
    "ServiceSubscriptionInvoice": {
        "build_via_service_subscription": {
            "canonical": {
                "name": "build_via_service_subscription",
                "description": "Records one invoice under a ServiceSubscription.",
                "is_constructor": True,
            },
            "input": ServiceSubscriptionInvoiceBuildViaServiceSubscriptionInput,
            "output": ServiceSubscriptionInvoiceBuildViaServiceSubscriptionOutput,
        },
    },
}

__all__ = [
    "ServiceSubscriptionInvoice",
    "ServiceSubscriptionInvoiceBuildViaServiceSubscriptionInput",
    "ServiceSubscriptionInvoiceBuildViaServiceSubscriptionOutput",
    "FUNCTIONS",
]
