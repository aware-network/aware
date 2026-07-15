from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.smart_contract.smart_contract_enums import SmartContractStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_dto.smart_contract.smart_contract_member import SmartContractMember
    from aware_economy_ontology_dto.smart_contract.smart_contract_permit import SmartContractPermit


class SmartContract(BaseModel):
    # Relationships
    smart_contract_members: list[SmartContractMember] = Field(default_factory=list)
    smart_contract_permits: list[SmartContractPermit] = Field(default_factory=list)

    # Attributes
    arguments: JsonObject = Field(default_factory=JsonObject)
    blockchain_address: str
    status: SmartContractStatus
