from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from aware_economy.handlers.impl.smart_contract.smart_contract import (
    finalize_settlement,
)
from aware_economy_ontology.smart_contract.smart_contract import SmartContract
from aware_economy_ontology.smart_contract.smart_contract_enums import (
    SmartContractMemberType,
    SmartContractStatus,
)
from aware_economy_ontology.smart_contract.smart_contract_member import (
    SmartContractMember,
)
from aware_economy_ontology.smart_contract.smart_contract_permit import (
    SmartContractPermit,
)
from aware_economy_ontology.smart_contract.smart_contract_permit_enums import (
    SmartContractPermitStatus,
)
from aware_economy_ontology.smart_contract.smart_contract_reservation import (
    SmartContractReservation,
)
from aware_economy_ontology.smart_contract.smart_contract_reservation_enums import (
    ReservationStatus,
)
from aware_economy_ontology.smart_contract.smart_contract_settlement import (
    SmartContractSettlement,
)
from aware_economy_ontology.smart_contract.smart_contract_settlement_enums import (
    SmartContractSettlementStatus,
)
from aware_economy_ontology.stable_ids import (
    stable_smart_contract_reservation_id,
    stable_smart_contract_settlement_id,
    stable_transaction_id,
)
from aware_economy_ontology.transaction.transaction import Transaction
from aware_economy_ontology.transaction.transaction_enums import TransactionStatus


@pytest.mark.asyncio
async def test_finalize_settlement_rehydrates_canonical_transaction_on_settled_reentry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    smart_contract_id = uuid4()
    permit_id = uuid4()
    payer_finance_entity_id = uuid4()
    receiver_finance_entity_id = uuid4()
    payer_wallet_public_id = uuid4()
    receiver_wallet_public_id = uuid4()
    coin_id = uuid4()
    op_nonce = 1
    final_cost = Decimal("7.0")

    reservation_id = stable_smart_contract_reservation_id(
        smart_contract_permit_id=permit_id,
        op_nonce=op_nonce,
    )
    settlement_id = stable_smart_contract_settlement_id(
        smart_contract_reservation_id=reservation_id,
    )
    transaction_id = stable_transaction_id(
        capital_origin_id=payer_wallet_public_id,
        target_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        nonce=op_nonce,
    )

    settlement = SmartContractSettlement(
        id=settlement_id,
        smart_contract_reservation_id=reservation_id,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        final_cost=Decimal("7"),
        status=SmartContractSettlementStatus.prepared,
    )
    reservation = SmartContractReservation(
        id=reservation_id,
        smart_contract_permit_id=permit_id,
        op_nonce=op_nonce,
        args_hash="args:hash:1",
        max_cost=Decimal("10"),
        final_cost=Decimal("7"),
        rate_snapshot_id=uuid4(),
        deadline=datetime(2030, 1, 1, tzinfo=UTC),
        status=ReservationStatus.settled,
    )
    reservation.smart_contract_settlements.append(settlement)
    permit = SmartContractPermit(
        id=permit_id,
        smart_contract_id=smart_contract_id,
        finance_entity_id=payer_finance_entity_id,
        permit_nonce=1,
        cap_amount=Decimal("20"),
        expires_at=datetime(2030, 1, 1, tzinfo=UTC),
        price_schedule_id=uuid4(),
        coin_id=coin_id,
        status=SmartContractPermitStatus.active,
    )
    permit.smart_contract_reservations.append(reservation)
    smart_contract = SmartContract(
        id=smart_contract_id,
        smart_contract_config_id=uuid4(),
        blockchain_address="dev:smart-contract",
        status=SmartContractStatus.active,
    )
    smart_contract.smart_contract_permits.append(permit)
    smart_contract.smart_contract_members.extend(
        [
            SmartContractMember(
                id=uuid4(),
                smart_contract_id=smart_contract_id,
                finance_entity_id=payer_finance_entity_id,
                type=SmartContractMemberType.payer,
            ),
            SmartContractMember(
                id=uuid4(),
                smart_contract_id=smart_contract_id,
                finance_entity_id=receiver_finance_entity_id,
                type=SmartContractMemberType.receiver,
            ),
        ]
    )

    calls = {"create_transaction": 0, "set_status": 0}

    async def _fake_create_transaction(
        self: SmartContractSettlement,
        nonce: int,
        description: str | None = None,
        idempotency_key: str | None = None,
    ) -> Transaction:
        calls["create_transaction"] += 1
        existing = next(
            (candidate for candidate in self.transactions if str(candidate.id) == str(transaction_id)),
            None,
        )
        if existing is not None:
            return existing
        transaction = Transaction(
            id=transaction_id,
            capital_origin_id=payer_wallet_public_id,
            source_wallet_public_id=payer_wallet_public_id,
            target_wallet_public_id=receiver_wallet_public_id,
            coin_id=coin_id,
            coin_amount=Decimal("7"),
            nonce=nonce,
            description=description,
            idempotency_key=idempotency_key,
            gas_price="0.00000001",
            sender_signature="sender-signature",
            transaction_hash="transaction-hash",
            status=TransactionStatus.created,
        )
        self.transactions.append(transaction)
        return transaction

    async def _fake_set_status(
        self: SmartContractSettlement,
        status: SmartContractSettlementStatus,
    ) -> SmartContractSettlement:
        calls["set_status"] += 1
        self.status = status
        return self

    monkeypatch.setattr(SmartContractSettlement, "create_transaction", _fake_create_transaction)
    monkeypatch.setattr(SmartContractSettlement, "set_status", _fake_set_status)

    result = await finalize_settlement(
        smart_contract=smart_contract,
        permit_id=permit_id,
        reservation_id=reservation_id,
        final_cost=final_cost,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
    )

    assert result is settlement
    assert settlement.status == SmartContractSettlementStatus.settled
    assert len(settlement.transactions) == 1
    assert settlement.transactions[0].id == transaction_id
    assert settlement.transactions[0].coin_amount == Decimal("7")
    assert calls == {"create_transaction": 1, "set_status": 1}

    replay = await finalize_settlement(
        smart_contract=smart_contract,
        permit_id=permit_id,
        reservation_id=reservation_id,
        final_cost=final_cost,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
    )

    assert replay is settlement
    assert settlement.status == SmartContractSettlementStatus.settled
    assert len(settlement.transactions) == 1
    assert settlement.transactions[0].id == transaction_id
    assert calls == {"create_transaction": 1, "set_status": 1}
