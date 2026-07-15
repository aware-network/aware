from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Economy Ontology Orm Models
from aware_economy_ontology_orm_models.smart_contract.smart_contract_enums import SmartContractStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.smart_contract.smart_contract_member import SmartContractMember
    from aware_economy_ontology_orm_models.smart_contract.smart_contract_permit import SmartContractPermit


class SmartContract(ORMModel):
    # Relationships
    smart_contract_members: list[SmartContractMember] = Field(default_factory=list, exclude=True)
    smart_contract_permits: list[SmartContractPermit] = Field(default_factory=list, exclude=True)

    # Attributes
    arguments: JsonObject = Field(default_factory=JsonObject)
    blockchain_address: str
    status: SmartContractStatus

    # Foreign Keys
    smart_contract_config_id: UUID = Field(description="Foreign key for SmartContractConfig.smart_contracts")
