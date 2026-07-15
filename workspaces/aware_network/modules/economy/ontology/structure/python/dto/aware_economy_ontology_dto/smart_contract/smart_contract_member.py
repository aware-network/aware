from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.smart_contract.smart_contract_enums import SmartContractMemberType

if TYPE_CHECKING:
    from aware_economy_ontology_dto.finance.finance_entity import FinanceEntity


class SmartContractMember(BaseModel):
    # Relationships
    finance_entity: FinanceEntity | None = Field(default=None)

    # Attributes
    type: SmartContractMemberType
