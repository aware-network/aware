from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Service Ontology Dto
from aware_service_ontology_dto.service.service_enums import ServiceSubscriptionCycleStatus

if TYPE_CHECKING:
    from aware_service_ontology_dto.service.service_subscription_invoice import ServiceSubscriptionInvoice


class ServiceSubscriptionCycle(BaseModel):
    # Relationships
    invoice: ServiceSubscriptionInvoice | None = Field(default=None)

    # Attributes
    cycle_number: int
    period_end: datetime
    period_start: datetime
    status: ServiceSubscriptionCycleStatus = Field(default=ServiceSubscriptionCycleStatus.pending)
