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
from aware_service_ontology_dto.service.service_enums import ServicePlanCycle

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin import Coin
    from aware_economy_ontology_dto.smart_contract.smart_contract_config import SmartContractConfig


class ServicePlan(BaseModel):
    # Relationships
    coin: Coin | None = Field(default=None)
    smart_contract_config: SmartContractConfig | None = Field(default=None)

    # Attributes
    cycle: ServicePlanCycle
    external_price_handle: str | None = Field(default=None)
    policy_json: JsonObject = Field(default_factory=JsonObject)
    price_amount: Annotated[Decimal, DecimalWire()]
