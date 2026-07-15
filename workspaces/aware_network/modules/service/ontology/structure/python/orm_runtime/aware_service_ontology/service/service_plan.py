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
from aware_service_ontology.service.service_enums import ServicePlanCycle

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology.coin.coin import Coin
    from aware_economy_ontology.smart_contract.smart_contract_config import SmartContractConfig


class ServicePlan(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)
    smart_contract_config: SmartContractConfig | None = Field(default=None, exclude=True)

    # Attributes
    cycle: ServicePlanCycle
    external_price_handle: str | None = Field(default=None)
    policy_json: JsonObject = Field(default_factory=JsonObject)
    price_amount: Annotated[Decimal, DecimalWire()]

    # Foreign Keys
    service_id: UUID = Field(description="Foreign key for Service.plans")
    coin_id: UUID = Field(description="Foreign key for ServicePlan.coin")
    smart_contract_config_id: UUID = Field(description="Foreign key for ServicePlan.smart_contract_config")

    @classmethod
    async def build_via_service(
        cls,
        service_id: UUID,
        cycle: ServicePlanCycle,
        price_amount: Annotated[Decimal, DecimalWire()],
        coin_id: UUID,
        smart_contract_config_id: UUID,
        external_price_handle: str | None = None,
        policy_json: JsonObject = {},
    ) -> ServicePlan:
        """Creates one Service-owned pricing plan under a concrete Service."""

        payload = {
            "service_id": service_id,
            "cycle": cycle,
            "price_amount": price_amount,
            "coin_id": coin_id,
            "smart_contract_config_id": smart_contract_config_id,
            "external_price_handle": external_price_handle,
            "policy_json": policy_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServicePlan):
            return value
        return ServicePlan.validate_invocation_value(value)


class ServicePlanBuildViaServiceInput(BaseModel):
    service_id: UUID = Field(description="Foreign key for Service.plans")
    cycle: ServicePlanCycle
    price_amount: Annotated[Decimal, DecimalWire()]
    coin_id: UUID
    smart_contract_config_id: UUID
    external_price_handle: str | None = Field(default=None)
    policy_json: JsonObject = Field(default_factory=JsonObject)


class ServicePlanBuildViaServiceOutput(BaseModel):
    value: ServicePlan


FUNCTIONS = {
    "ServicePlan": {
        "build_via_service": {
            "canonical": {
                "name": "build_via_service",
                "description": "Creates one Service-owned pricing plan under a concrete Service.",
                "is_constructor": True,
            },
            "input": ServicePlanBuildViaServiceInput,
            "output": ServicePlanBuildViaServiceOutput,
        },
    },
}

__all__ = [
    "ServicePlan",
    "ServicePlanBuildViaServiceInput",
    "ServicePlanBuildViaServiceOutput",
    "FUNCTIONS",
]
