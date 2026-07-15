from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology
from aware_economy_ontology.smart_contract.smart_contract_enums import (
    SmartContractStatus,
    SmartContractType,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_economy_ontology.smart_contract.smart_contract import SmartContract


class SmartContractConfig(ORMModel):
    # Relationships
    smart_contracts: list[SmartContract] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str
    name: str
    smart_contract_schema: JsonObject | None = Field(default_factory=JsonObject)
    type: SmartContractType

    @classmethod
    async def build(
        cls, name: str, description: str, type: SmartContractType, smart_contract_schema: JsonObject | None = {}
    ) -> SmartContractConfig:
        """
        Creates a SmartContractConfig template.

        Receipt: SmartContractConfig(name, description, type, schema).
        """

        payload = {
            "name": name,
            "description": description,
            "type": type,
            "smart_contract_schema": smart_contract_schema,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SmartContractConfig):
            return value
        return SmartContractConfig.validate_invocation_value(value)

    async def create_smart_contract(
        self,
        blockchain_address: str,
        status: SmartContractStatus = SmartContractStatus.active,
        arguments: JsonObject | None = None,
    ) -> SmartContract:
        """Creates one SmartContract under this SmartContractConfig."""

        payload = {"blockchain_address": blockchain_address, "status": status, "arguments": arguments}
        result = await invoke_instance(orm_model=self, function_name="create_smart_contract", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.smart_contract.smart_contract import SmartContract

        if isinstance(value, SmartContract):
            return value
        return SmartContract.validate_invocation_value(value)


class SmartContractConfigBuildInput(BaseModel):
    name: str
    description: str
    type: SmartContractType
    smart_contract_schema: JsonObject | None = Field(default_factory=JsonObject)


class SmartContractConfigBuildOutput(BaseModel):
    value: SmartContractConfig


class SmartContractConfigCreateSmartContractInput(BaseModel):
    blockchain_address: str
    status: SmartContractStatus = Field(default=SmartContractStatus.active)
    arguments: JsonObject | None = Field(default=None)


class SmartContractConfigCreateSmartContractOutput(BaseModel):
    value: SmartContract


FUNCTIONS = {
    "SmartContractConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Creates a SmartContractConfig template.\n\nReceipt: SmartContractConfig(name, description, type, schema).",
                "is_constructor": True,
            },
            "input": SmartContractConfigBuildInput,
            "output": SmartContractConfigBuildOutput,
        },
        "create_smart_contract": {
            "canonical": {
                "name": "create_smart_contract",
                "description": "Creates one SmartContract under this SmartContractConfig.",
                "is_constructor": False,
            },
            "input": SmartContractConfigCreateSmartContractInput,
            "output": SmartContractConfigCreateSmartContractOutput,
        },
    },
}

__all__ = [
    "SmartContractConfig",
    "SmartContractConfigBuildInput",
    "SmartContractConfigBuildOutput",
    "SmartContractConfigCreateSmartContractInput",
    "SmartContractConfigCreateSmartContractOutput",
    "FUNCTIONS",
]
