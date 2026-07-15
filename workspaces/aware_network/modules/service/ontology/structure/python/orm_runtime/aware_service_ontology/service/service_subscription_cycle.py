from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
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
from aware_service_ontology.service.service_enums import ServiceSubscriptionCycleStatus

if TYPE_CHECKING:
    from aware_service_ontology.service.service_subscription_invoice import ServiceSubscriptionInvoice


class ServiceSubscriptionCycle(ORMModel):
    # Relationships
    invoice: ServiceSubscriptionInvoice | None = Field(default=None, exclude=True)

    # Attributes
    cycle_number: int
    period_end: datetime
    period_start: datetime
    status: ServiceSubscriptionCycleStatus = Field(default=ServiceSubscriptionCycleStatus.pending)

    # Foreign Keys
    service_subscription_id: UUID = Field(description="Foreign key for ServiceSubscription.cycles")
    invoice_id: UUID | None = Field(default=None, description="Foreign key for ServiceSubscriptionCycle.invoice")

    @classmethod
    async def build_via_service_subscription(
        cls,
        service_subscription_id: UUID,
        cycle_number: int,
        period_start: datetime,
        period_end: datetime,
        status: ServiceSubscriptionCycleStatus = ServiceSubscriptionCycleStatus.pending,
        invoice_id: UUID | None = None,
    ) -> ServiceSubscriptionCycle:
        """Records one billing cycle under a ServiceSubscription."""

        payload = {
            "service_subscription_id": service_subscription_id,
            "cycle_number": cycle_number,
            "period_start": period_start,
            "period_end": period_end,
            "status": status,
            "invoice_id": invoice_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_service_subscription", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceSubscriptionCycle):
            return value
        return ServiceSubscriptionCycle.validate_invocation_value(value)


class ServiceSubscriptionCycleBuildViaServiceSubscriptionInput(BaseModel):
    service_subscription_id: UUID = Field(description="Foreign key for ServiceSubscription.cycles")
    cycle_number: int
    period_start: datetime
    period_end: datetime
    status: ServiceSubscriptionCycleStatus = Field(default=ServiceSubscriptionCycleStatus.pending)
    invoice_id: UUID | None = Field(default=None)


class ServiceSubscriptionCycleBuildViaServiceSubscriptionOutput(BaseModel):
    value: ServiceSubscriptionCycle


FUNCTIONS = {
    "ServiceSubscriptionCycle": {
        "build_via_service_subscription": {
            "canonical": {
                "name": "build_via_service_subscription",
                "description": "Records one billing cycle under a ServiceSubscription.",
                "is_constructor": True,
            },
            "input": ServiceSubscriptionCycleBuildViaServiceSubscriptionInput,
            "output": ServiceSubscriptionCycleBuildViaServiceSubscriptionOutput,
        },
    },
}

__all__ = [
    "ServiceSubscriptionCycle",
    "ServiceSubscriptionCycleBuildViaServiceSubscriptionInput",
    "ServiceSubscriptionCycleBuildViaServiceSubscriptionOutput",
    "FUNCTIONS",
]
