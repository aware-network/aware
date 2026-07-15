from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from aware_economy.capital_amount import (
    amount_equal,
    canonical_amount_text,
    non_negative_amount,
    positive_amount,
)
from aware_economy.canonical.transaction import create_transaction_via_settlement_portal
from aware_economy_ontology.smart_contract.smart_contract_settlement import (
    SmartContractSettlement,
)
from aware_economy_ontology.smart_contract.smart_contract_settlement_enums import (
    SmartContractSettlementStatus,
)
from aware_economy_ontology.stable_ids import (
    stable_smart_contract_settlement_id,
    stable_transaction_id,
)
from aware_economy_ontology.transaction.transaction import Transaction


def materialize_smart_contract_settlement(
    *,
    smart_contract_reservation_id: UUID,
    payer_finance_entity_id: UUID,
    payer_wallet_public_id: UUID,
    receiver_finance_entity_id: UUID,
    receiver_wallet_public_id: UUID,
    coin_id: UUID,
    final_cost: Decimal,
    status: SmartContractSettlementStatus = SmartContractSettlementStatus.prepared,
) -> SmartContractSettlement:
    final_cost = non_negative_amount(
        final_cost,
        field_name="smart contract settlement final_cost",
    )

    settlement_id = stable_smart_contract_settlement_id(
        smart_contract_reservation_id=smart_contract_reservation_id,
    )
    return SmartContractSettlement(
        id=settlement_id,
        smart_contract_reservation_id=smart_contract_reservation_id,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        final_cost=final_cost,
        status=status,
    )


async def ensure_transaction_for_smart_contract_settlement(
    *,
    smart_contract_settlement: SmartContractSettlement,
    nonce: int,
    description: str | None = None,
    idempotency_key: str | None = None,
) -> Transaction:
    if nonce <= 0:
        raise ValueError(
            "smart_contract_settlement.create_transaction requires nonce > 0"
        )
    positive_amount(
        smart_contract_settlement.final_cost,
        field_name="smart contract settlement final_cost",
    )

    expected_transaction_id = stable_transaction_id(
        capital_origin_id=smart_contract_settlement.payer_wallet_public_id,
        target_wallet_public_id=smart_contract_settlement.receiver_wallet_public_id,
        coin_id=smart_contract_settlement.coin_id,
        nonce=nonce,
    )
    existing = next(
        (
            candidate
            for candidate in smart_contract_settlement.transactions
            if str(candidate.id) == str(expected_transaction_id)
        ),
        None,
    )
    if existing is not None:
        if not amount_equal(
            existing.coin_amount,
            smart_contract_settlement.final_cost,
        ):
            raise ValueError(
                "smart_contract_settlement.create_transaction existing coin_amount mismatch"
            )
        return existing

    transaction = await create_transaction_via_settlement_portal(
        smart_contract_settlement=smart_contract_settlement,
        transaction_id=expected_transaction_id,
        payload={
            "source_wallet_public_id": smart_contract_settlement.payer_wallet_public_id,
            "capital_origin_id": smart_contract_settlement.payer_wallet_public_id,
            "target_wallet_public_id": smart_contract_settlement.receiver_wallet_public_id,
            "coin_id": smart_contract_settlement.coin_id,
            "coin_amount": canonical_amount_text(
                smart_contract_settlement.final_cost,
                field_name="smart contract settlement final_cost",
            ),
            "nonce": nonce,
            "description": description,
            "idempotency_key": idempotency_key,
        },
    )
    if str(transaction.id) != str(expected_transaction_id):
        raise ValueError(
            "smart_contract_settlement.create_transaction transaction.id mismatch: "
            f"actual={transaction.id} expected={expected_transaction_id}"
        )
    if not any(
        str(candidate.id) == str(transaction.id)
        for candidate in smart_contract_settlement.transactions
    ):
        smart_contract_settlement.transactions.append(transaction)
    return transaction


__all__ = [
    "ensure_transaction_for_smart_contract_settlement",
    "materialize_smart_contract_settlement",
]
