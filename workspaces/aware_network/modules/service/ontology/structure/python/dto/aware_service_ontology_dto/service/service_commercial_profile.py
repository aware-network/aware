from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_dto.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_dto.smart_contract.smart_contract_config import SmartContractConfig


class ServiceCommercialProfile(BaseModel):
    # Relationships
    default_smart_contract_config: SmartContractConfig | None = Field(default=None)
    producer_finance_entity: FinanceEntity | None = Field(default=None)

    # Attributes
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
