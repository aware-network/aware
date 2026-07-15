from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Economy Ontology Orm Models
from aware_economy_ontology_orm_models.smart_contract.smart_contract_enums import SmartContractMemberType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.finance.finance_entity import FinanceEntity


class SmartContractMember(ORMModel):
    # Relationships
    finance_entity: FinanceEntity | None = Field(default=None, exclude=True)

    # Attributes
    type: SmartContractMemberType

    # Foreign Keys
    smart_contract_id: UUID = Field(description="Foreign key for SmartContract.smart_contract_members")
    finance_entity_id: UUID = Field(description="Foreign key for SmartContractMember.finance_entity")
