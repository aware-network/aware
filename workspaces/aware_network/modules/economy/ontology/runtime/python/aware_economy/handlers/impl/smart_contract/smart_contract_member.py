from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.smart_contract.smart_contract_enums import SmartContractMemberType
from aware_economy_ontology.smart_contract.smart_contract_member import SmartContractMember

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Runtime
from aware_economy.ontology.materialization import materialize_smart_contract_member

# --- AWARE: USER_IMPORTS END


async def create_via_smart_contract(
    smart_contract_id: UUID, finance_entity_id: UUID, type: SmartContractMemberType
) -> SmartContractMember:
    """
    Creates a SmartContractMember for a contract.

    Receipt: SmartContractMember linked to SmartContract + FinanceEntity.
    """

    # --- AWARE: LOGIC START create_via_smart_contract
    return materialize_smart_contract_member(
        smart_contract_id=smart_contract_id,
        finance_entity_id=finance_entity_id,
        type=type,
    )
    # --- AWARE: LOGIC END create_via_smart_contract
