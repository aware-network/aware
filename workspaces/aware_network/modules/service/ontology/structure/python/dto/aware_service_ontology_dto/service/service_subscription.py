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
from aware_service_ontology_dto.service.service_enums import ServiceSubscriptionStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_dto.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_dto.smart_contract.smart_contract import SmartContract
    from aware_service_ontology_dto.service.service import Service
    from aware_service_ontology_dto.service.service_plan import ServicePlan
    from aware_service_ontology_dto.service.service_subscription_cycle import ServiceSubscriptionCycle
    from aware_service_ontology_dto.service.service_subscription_invoice import ServiceSubscriptionInvoice


class ServiceSubscription(BaseModel):
    # Relationships
    consumer_finance_entity: FinanceEntity | None = Field(default=None)
    contract: SmartContract | None = Field(default=None)
    cycles: list[ServiceSubscriptionCycle] = Field(default_factory=list)
    invoices: list[ServiceSubscriptionInvoice] = Field(default_factory=list)
    plan: ServicePlan | None = Field(default=None)
    service: Service | None = Field(default=None)

    # Attributes
    cancel_at_period_end: bool = Field(default=False)
    current_period_end: datetime | None = Field(default=None)
    current_period_start: datetime | None = Field(default=None)
    external_subscription_handle: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default=None)
    status: ServiceSubscriptionStatus = Field(default=ServiceSubscriptionStatus.active)
