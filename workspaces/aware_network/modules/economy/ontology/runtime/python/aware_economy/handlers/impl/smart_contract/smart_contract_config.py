from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Code
from aware_code.types import JsonObject

# Economy Ontology
from aware_economy_ontology.smart_contract.smart_contract_enums import (
    SmartContractStatus,
    SmartContractType,
)
from aware_economy_ontology.smart_contract.smart_contract import SmartContract
from aware_economy_ontology.smart_contract.smart_contract_config import SmartContractConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Runtime
from aware_economy.stable_ids import stable_smart_contract_config_id

# --- AWARE: USER_IMPORTS END


async def build(
    name: str, description: str, type: SmartContractType, smart_contract_schema: JsonObject | None = JsonObject()
) -> SmartContractConfig:
    """
    Creates a SmartContractConfig template.

    Receipt: SmartContractConfig(name, description, type, schema).
    """

    # --- AWARE: LOGIC START build
    type_key = getattr(type, "value", str(type))
    config_id = stable_smart_contract_config_id(name=name, type=str(type_key))
    schema_json = smart_contract_schema if smart_contract_schema is not None else JsonObject({})
    return SmartContractConfig(
        id=config_id,
        name=name.strip(),
        description=description.strip(),
        type=type,
        smart_contract_schema=schema_json,
    )
    # --- AWARE: LOGIC END build


async def create_smart_contract(
    smart_contract_config: SmartContractConfig,
    blockchain_address: str,
    status: SmartContractStatus = SmartContractStatus.active,
    arguments: JsonObject | None = None,
) -> SmartContract:
    """
    Creates one SmartContract under this SmartContractConfig.
    """

    # --- AWARE: LOGIC START create_smart_contract
    contract = await SmartContract.build_via_smart_contract_config(
        smart_contract_config_id=smart_contract_config.id,
        blockchain_address=blockchain_address,
        status=status,
        arguments=arguments,
    )
    smart_contract_config.smart_contracts.append(contract)
    return contract
    # --- AWARE: LOGIC END create_smart_contract
