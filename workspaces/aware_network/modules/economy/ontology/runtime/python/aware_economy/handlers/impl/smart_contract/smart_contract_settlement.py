from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.smart_contract.smart_contract_settlement_enums import SmartContractSettlementStatus
from aware_economy_ontology.smart_contract.smart_contract_settlement import SmartContractSettlement
from aware_economy_ontology.transaction.transaction import Transaction

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Runtime
from aware_economy.ontology.materialization import (
    ensure_transaction_for_smart_contract_settlement,
    materialize_smart_contract_settlement,
)
from aware_economy.capital_amount import (
    non_negative_amount,
    positive_amount,
)

# --- AWARE: USER_IMPORTS END


async def set_status(
    smart_contract_settlement: SmartContractSettlement, status: SmartContractSettlementStatus
) -> SmartContractSettlement:
    """
    Updates smart-contract settlement lifecycle status.

    Receipt: SmartContractSettlement status transition.
    """

    # --- AWARE: LOGIC START set_status
    current = smart_contract_settlement.status
    if current == status:
        return smart_contract_settlement
    if current == SmartContractSettlementStatus.settled:
        raise ValueError(
            "smart_contract_settlement status is terminal and cannot transition: " f"{current} -> {status}"
        )
    smart_contract_settlement.status = status
    return smart_contract_settlement
    # --- AWARE: LOGIC END set_status


async def create_transaction(
    smart_contract_settlement: SmartContractSettlement,
    nonce: int,
    description: str | None = None,
    idempotency_key: str | None = None,
) -> Transaction:
    """
    Creates or reuses the canonical capital-transfer receipt for this settlement.

    Receipt: Transaction(status=created) referenced by this settlement.
    """

    # --- AWARE: LOGIC START create_transaction
    if nonce <= 0:
        raise ValueError("smart_contract_settlement.create_transaction requires nonce > 0")
    positive_amount(
        smart_contract_settlement.final_cost,
        field_name="smart contract settlement final_cost",
    )

    return await ensure_transaction_for_smart_contract_settlement(
        smart_contract_settlement=smart_contract_settlement,
        nonce=nonce,
        description=description,
        idempotency_key=idempotency_key,
    )
    # --- AWARE: LOGIC END create_transaction


async def create_via_smart_contract_reservation(
    smart_contract_reservation_id: UUID,
    payer_finance_entity_id: UUID,
    payer_wallet_public_id: UUID,
    receiver_finance_entity_id: UUID,
    receiver_wallet_public_id: UUID,
    coin_id: UUID,
    final_cost: Annotated[Decimal, DecimalWire()],
    status: SmartContractSettlementStatus = SmartContractSettlementStatus.prepared,
) -> SmartContractSettlement:
    """
    Creates a settlement receipt under a smart-contract reservation.

    Receipt: SmartContractSettlement(status=prepared).
    """

    # --- AWARE: LOGIC START create_via_smart_contract_reservation
    final_cost = non_negative_amount(
        final_cost,
        field_name="smart contract settlement final_cost",
    )

    return materialize_smart_contract_settlement(
        smart_contract_reservation_id=smart_contract_reservation_id,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        final_cost=final_cost,
        status=status,
    )
    # --- AWARE: LOGIC END create_via_smart_contract_reservation
