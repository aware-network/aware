from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Economy Ontology Orm Models
from aware_economy_ontology_orm_models.smart_contract.smart_contract_enums import SmartContractType

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.smart_contract.smart_contract import SmartContract


class SmartContractConfig(ORMModel):
    # Relationships
    smart_contracts: list[SmartContract] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str
    name: str
    smart_contract_schema: JsonObject | None = Field(default_factory=JsonObject)
    type: SmartContractType
