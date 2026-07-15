from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Service Ontology Orm Models
from aware_service_ontology_orm_models.service.service_enums import ServiceSubscriptionCycleStatus

if TYPE_CHECKING:
    from aware_service_ontology_orm_models.service.service_subscription_invoice import ServiceSubscriptionInvoice


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
