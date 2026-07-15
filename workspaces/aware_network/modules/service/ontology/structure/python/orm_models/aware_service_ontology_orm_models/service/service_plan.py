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
from aware_service_ontology_orm_models.service.service_enums import ServicePlanCycle

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin import Coin
    from aware_economy_ontology_orm_models.smart_contract.smart_contract_config import SmartContractConfig


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
