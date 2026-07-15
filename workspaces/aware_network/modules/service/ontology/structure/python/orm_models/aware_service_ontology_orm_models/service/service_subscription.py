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
from aware_service_ontology_orm_models.service.service_enums import ServiceSubscriptionStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_orm_models.smart_contract.smart_contract import SmartContract
    from aware_service_ontology_orm_models.service.service import Service
    from aware_service_ontology_orm_models.service.service_plan import ServicePlan
    from aware_service_ontology_orm_models.service.service_subscription_cycle import ServiceSubscriptionCycle
    from aware_service_ontology_orm_models.service.service_subscription_invoice import ServiceSubscriptionInvoice


class ServiceSubscription(ORMModel):
    # Relationships
    consumer_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    contract: SmartContract | None = Field(default=None, exclude=True)
    cycles: list[ServiceSubscriptionCycle] = Field(default_factory=list, exclude=True)
    invoices: list[ServiceSubscriptionInvoice] = Field(default_factory=list, exclude=True)
    plan: ServicePlan | None = Field(default=None, exclude=True)
    service: Service | None = Field(default=None, exclude=True)

    # Attributes
    cancel_at_period_end: bool = Field(default=False)
    current_period_end: datetime | None = Field(default=None)
    current_period_start: datetime | None = Field(default=None)
    external_subscription_handle: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default=None)
    status: ServiceSubscriptionStatus = Field(default=ServiceSubscriptionStatus.active)

    # Foreign Keys
    consumer_finance_entity_id: UUID = Field(description="Foreign key for ServiceSubscription.consumer_finance_entity")
    contract_id: UUID = Field(description="Foreign key for ServiceSubscription.contract")
    plan_id: UUID = Field(description="Foreign key for ServiceSubscription.plan")
    service_id: UUID = Field(description="Foreign key for ServiceSubscription.service")
