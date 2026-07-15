from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology
from aware_economy_ontology.smart_contract.smart_contract_enums import SmartContractMemberType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_economy_ontology.finance.finance_entity import FinanceEntity


class SmartContractMember(ORMModel):
    # Relationships
    finance_entity: FinanceEntity | None = Field(default=None, exclude=True)

    # Attributes
    type: SmartContractMemberType

    # Foreign Keys
    smart_contract_id: UUID = Field(description="Foreign key for SmartContract.smart_contract_members")
    finance_entity_id: UUID = Field(description="Foreign key for SmartContractMember.finance_entity")

    @classmethod
    async def create_via_smart_contract(
        cls, smart_contract_id: UUID, finance_entity_id: UUID, type: SmartContractMemberType
    ) -> SmartContractMember:
        """
        Creates a SmartContractMember for a contract.

        Receipt: SmartContractMember linked to SmartContract + FinanceEntity.
        """

        payload = {"smart_contract_id": smart_contract_id, "finance_entity_id": finance_entity_id, "type": type}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_smart_contract", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SmartContractMember):
            return value
        return SmartContractMember.validate_invocation_value(value)


class SmartContractMemberCreateViaSmartContractInput(BaseModel):
    smart_contract_id: UUID = Field(description="Foreign key for SmartContract.smart_contract_members")
    finance_entity_id: UUID
    type: SmartContractMemberType


class SmartContractMemberCreateViaSmartContractOutput(BaseModel):
    value: SmartContractMember


FUNCTIONS = {
    "SmartContractMember": {
        "create_via_smart_contract": {
            "canonical": {
                "name": "create_via_smart_contract",
                "description": "Creates a SmartContractMember for a contract.\n\nReceipt: SmartContractMember linked to SmartContract + FinanceEntity.",
                "is_constructor": True,
            },
            "input": SmartContractMemberCreateViaSmartContractInput,
            "output": SmartContractMemberCreateViaSmartContractOutput,
        },
    },
}

__all__ = [
    "SmartContractMember",
    "SmartContractMemberCreateViaSmartContractInput",
    "SmartContractMemberCreateViaSmartContractOutput",
    "FUNCTIONS",
]
