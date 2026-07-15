from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.smart_contract.smart_contract_enums import SmartContractType

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_dto.smart_contract.smart_contract import SmartContract


class SmartContractConfig(BaseModel):
    # Relationships
    smart_contracts: list[SmartContract] = Field(default_factory=list)

    # Attributes
    description: str
    name: str
    smart_contract_schema: JsonObject | None = Field(default_factory=JsonObject)
    type: SmartContractType
