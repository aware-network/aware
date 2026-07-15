from __future__ import annotations

# Standard
from datetime import datetime
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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Service Ontology
from aware_service_ontology.service.service_enums import (
    ServiceSubscriptionCycleStatus,
    ServiceSubscriptionInvoiceStatus,
    ServiceSubscriptionStatus,
)

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology.finance.finance_entity import FinanceEntity
    from aware_economy_ontology.smart_contract.smart_contract import SmartContract
    from aware_service_ontology.service.service import Service
    from aware_service_ontology.service.service_plan import ServicePlan
    from aware_service_ontology.service.service_subscription_cycle import ServiceSubscriptionCycle
    from aware_service_ontology.service.service_subscription_invoice import ServiceSubscriptionInvoice


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

    @classmethod
    async def build(
        cls,
        consumer_finance_entity_id: UUID,
        service_id: UUID,
        plan_id: UUID,
        contract_id: UUID,
        external_subscription_handle: str | None = None,
        status: ServiceSubscriptionStatus = ServiceSubscriptionStatus.active,
        current_period_start: datetime | None = None,
        current_period_end: datetime | None = None,
        cancel_at_period_end: bool = False,
        metadata_json: JsonObject | None = None,
    ) -> ServiceSubscription:
        """Creates or upserts one consumer subscription receipt for a canonical Service."""

        payload = {
            "consumer_finance_entity_id": consumer_finance_entity_id,
            "service_id": service_id,
            "plan_id": plan_id,
            "contract_id": contract_id,
            "external_subscription_handle": external_subscription_handle,
            "status": status,
            "current_period_start": current_period_start,
            "current_period_end": current_period_end,
            "cancel_at_period_end": cancel_at_period_end,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceSubscription):
            return value
        return ServiceSubscription.validate_invocation_value(value)

    async def create_cycle(
        self,
        cycle_number: int,
        period_start: datetime,
        period_end: datetime,
        status: ServiceSubscriptionCycleStatus = ServiceSubscriptionCycleStatus.pending,
        invoice_id: UUID | None = None,
    ) -> ServiceSubscriptionCycle:
        """Appends one billing cycle receipt under this ServiceSubscription."""

        payload = {
            "cycle_number": cycle_number,
            "period_start": period_start,
            "period_end": period_end,
            "status": status,
            "invoice_id": invoice_id,
        }
        result = await invoke_instance(orm_model=self, function_name="create_cycle", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_subscription_cycle import ServiceSubscriptionCycle

        if isinstance(value, ServiceSubscriptionCycle):
            return value
        return ServiceSubscriptionCycle.validate_invocation_value(value)

    async def create_invoice(
        self,
        amount: Annotated[Decimal, DecimalWire()],
        coin_id: UUID,
        external_invoice_handle: str | None = None,
        status: ServiceSubscriptionInvoiceStatus = ServiceSubscriptionInvoiceStatus.open,
    ) -> ServiceSubscriptionInvoice:
        """Appends one invoice receipt under this ServiceSubscription."""

        payload = {
            "amount": amount,
            "coin_id": coin_id,
            "external_invoice_handle": external_invoice_handle,
            "status": status,
        }
        result = await invoke_instance(orm_model=self, function_name="create_invoice", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_subscription_invoice import ServiceSubscriptionInvoice

        if isinstance(value, ServiceSubscriptionInvoice):
            return value
        return ServiceSubscriptionInvoice.validate_invocation_value(value)


class ServiceSubscriptionBuildInput(BaseModel):
    consumer_finance_entity_id: UUID
    service_id: UUID
    plan_id: UUID
    contract_id: UUID
    external_subscription_handle: str | None = Field(default=None)
    status: ServiceSubscriptionStatus = Field(default=ServiceSubscriptionStatus.active)
    current_period_start: datetime | None = Field(default=None)
    current_period_end: datetime | None = Field(default=None)
    cancel_at_period_end: bool = Field(default=False)
    metadata_json: JsonObject | None = Field(default=None)


class ServiceSubscriptionBuildOutput(BaseModel):
    value: ServiceSubscription


class ServiceSubscriptionCreateCycleInput(BaseModel):
    cycle_number: int
    period_start: datetime
    period_end: datetime
    status: ServiceSubscriptionCycleStatus = Field(default=ServiceSubscriptionCycleStatus.pending)
    invoice_id: UUID | None = Field(default=None)


class ServiceSubscriptionCreateCycleOutput(BaseModel):
    value: ServiceSubscriptionCycle


class ServiceSubscriptionCreateInvoiceInput(BaseModel):
    amount: Annotated[Decimal, DecimalWire()]
    coin_id: UUID
    external_invoice_handle: str | None = Field(default=None)
    status: ServiceSubscriptionInvoiceStatus = Field(default=ServiceSubscriptionInvoiceStatus.open)


class ServiceSubscriptionCreateInvoiceOutput(BaseModel):
    value: ServiceSubscriptionInvoice


FUNCTIONS = {
    "ServiceSubscription": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Creates or upserts one consumer subscription receipt for a canonical Service.",
                "is_constructor": True,
            },
            "input": ServiceSubscriptionBuildInput,
            "output": ServiceSubscriptionBuildOutput,
        },
        "create_cycle": {
            "canonical": {
                "name": "create_cycle",
                "description": "Appends one billing cycle receipt under this ServiceSubscription.",
                "is_constructor": False,
            },
            "input": ServiceSubscriptionCreateCycleInput,
            "output": ServiceSubscriptionCreateCycleOutput,
        },
        "create_invoice": {
            "canonical": {
                "name": "create_invoice",
                "description": "Appends one invoice receipt under this ServiceSubscription.",
                "is_constructor": False,
            },
            "input": ServiceSubscriptionCreateInvoiceInput,
            "output": ServiceSubscriptionCreateInvoiceOutput,
        },
    },
}

__all__ = [
    "ServiceSubscription",
    "ServiceSubscriptionBuildInput",
    "ServiceSubscriptionBuildOutput",
    "ServiceSubscriptionCreateCycleInput",
    "ServiceSubscriptionCreateCycleOutput",
    "ServiceSubscriptionCreateInvoiceInput",
    "ServiceSubscriptionCreateInvoiceOutput",
    "FUNCTIONS",
]
