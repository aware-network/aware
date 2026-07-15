from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from aware_economy_ontology.coin.coin import Coin
from aware_economy_ontology.coin.coin_enums import CoinType
from aware_economy_ontology.smart_contract.smart_contract_permit import (
    SmartContractPermit,
)
from aware_economy_ontology.wallet.wallet import Wallet
from aware_economy_ontology.wallet.wallet_public import WalletPublic
from aware_orm.session.session import Session
from aware_service_ontology.service.service_contract import ServiceContract
from aware_service_ontology.service.service_contract_economy_settlement import (
    ServiceContractEconomySettlement,
)
from aware_service_ontology.service.service_enums import (
    ServiceContractKind,
    ServiceContractStatus,
)
from aware_service_ontology.stable_ids import (
    stable_service_contract_economy_settlement_id,
)
from aware_service_runtime.handlers.impl.service import (
    service_contract as contract_impl,
)
from aware_service_runtime.handlers.impl.service import (
    service_contract_economy_settlement as settlement_impl,
)


def _deadline() -> datetime:
    return datetime(2026, 7, 7, 12, 30, tzinfo=timezone.utc)


def _service_contract(
    *,
    service_contract_id: UUID,
    consumer_finance_entity_id: UUID,
    producer_finance_entity_id: UUID,
    smart_contract_id: UUID,
) -> ServiceContract:
    return ServiceContract.model_construct(
        id=service_contract_id,
        service_id=uuid4(),
        commercial_profile_id=uuid4(),
        producer_finance_entity_id=producer_finance_entity_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_contract_config_id=uuid4(),
        smart_contract_id=smart_contract_id,
        kind=ServiceContractKind.metered,
        status=ServiceContractStatus.active,
        effective_from=_deadline(),
        metadata_json={
            "economy_settlement": {
                "permit_id": str(uuid4()),
                "permit_nonce": 99999,
            }
        },
    )


def _wallet(*, wallet_id: UUID, wallet_public_id: UUID) -> Wallet:
    return Wallet.model_construct(
        id=wallet_id,
        wallet_public_id=wallet_public_id,
        public_key=f"pub:{wallet_public_id}",
        private_key_encrypted="custody:test-wallet",
    )


def _wallet_public(*, wallet_public_id: UUID, address: str) -> WalletPublic:
    return WalletPublic.model_construct(
        id=wallet_public_id,
        address=address,
        public_key=f"pub:{wallet_public_id}",
    )


def _permit(
    *,
    permit_id: UUID,
    smart_contract_id: UUID,
    finance_entity_id: UUID,
    permit_nonce: int,
    coin_id: UUID,
) -> SmartContractPermit:
    return SmartContractPermit.model_construct(
        id=permit_id,
        smart_contract_id=smart_contract_id,
        finance_entity_id=finance_entity_id,
        permit_nonce=permit_nonce,
        coin_id=coin_id,
        cap_amount="100",
        expires_at=_deadline(),
        price_schedule_id=uuid4(),
    )


def _coin(*, coin_id: UUID) -> Coin:
    return Coin.model_construct(
        id=coin_id,
        symbol="AWR",
        name="Aware Test Coin",
        type=CoinType.token,
        decimals=8,
    )


def _settlement_session(
    *,
    service_contract_id: UUID,
    consumer_finance_entity_id: UUID,
    producer_finance_entity_id: UUID,
    smart_contract_id: UUID,
    permit_id: UUID,
    permit_nonce: int,
    payer_wallet_id: UUID,
    payer_wallet_public_id: UUID,
    receiver_wallet_id: UUID,
    receiver_wallet_public_id: UUID,
    coin_id: UUID,
) -> tuple[Session, ServiceContract]:
    session = Session(branch_id=uuid4(), skip_db=True)
    service_contract = _service_contract(
        service_contract_id=service_contract_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        producer_finance_entity_id=producer_finance_entity_id,
        smart_contract_id=smart_contract_id,
    )
    for instance in (
        service_contract,
        _permit(
            permit_id=permit_id,
            smart_contract_id=smart_contract_id,
            finance_entity_id=consumer_finance_entity_id,
            permit_nonce=permit_nonce,
            coin_id=coin_id,
        ),
        _wallet(wallet_id=payer_wallet_id, wallet_public_id=payer_wallet_public_id),
        _wallet_public(
            wallet_public_id=payer_wallet_public_id,
            address="aware:test:payer",
        ),
        _wallet(
            wallet_id=receiver_wallet_id,
            wallet_public_id=receiver_wallet_public_id,
        ),
        _wallet_public(
            wallet_public_id=receiver_wallet_public_id,
            address="aware:test:receiver",
        ),
        _coin(coin_id=coin_id),
    ):
        session.imap_add(instance)
    return session, service_contract


@pytest.mark.asyncio
async def test_service_contract_economy_settlement_builds_and_reuses_typed_coordinate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service_contract_id = uuid4()
    consumer_finance_entity_id = uuid4()
    producer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    permit_id = uuid4()
    permit_nonce = 7
    payer_wallet_id = uuid4()
    payer_wallet_public_id = uuid4()
    receiver_wallet_id = uuid4()
    receiver_wallet_public_id = uuid4()
    coin_id = uuid4()
    session, service_contract = _settlement_session(
        service_contract_id=service_contract_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        producer_finance_entity_id=producer_finance_entity_id,
        smart_contract_id=smart_contract_id,
        permit_id=permit_id,
        permit_nonce=permit_nonce,
        payer_wallet_id=payer_wallet_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_wallet_id=receiver_wallet_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
    )
    monkeypatch.setattr(settlement_impl, "current_handler_session", lambda: session)

    created = await settlement_impl.build_via_service_contract(
        service_contract_id=service_contract_id,
        permit_id=permit_id,
        permit_nonce=permit_nonce,
        payer_wallet_id=payer_wallet_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_wallet_id=receiver_wallet_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        deadline=_deadline(),
    )

    assert created.id == stable_service_contract_economy_settlement_id(
        service_contract_id=service_contract_id
    )
    assert created.service_contract_id == service_contract_id
    assert created.permit_id == permit_id
    assert created.permit_nonce == permit_nonce
    assert created.payer_wallet_id == payer_wallet_id
    assert created.payer_wallet_public_id == payer_wallet_public_id
    assert created.receiver_wallet_id == receiver_wallet_id
    assert created.receiver_wallet_public_id == receiver_wallet_public_id
    assert created.coin_id == coin_id
    assert created.deadline == _deadline()
    assert service_contract.economy_settlement is created
    assert session.imap_get(ServiceContractEconomySettlement, created.id) is created

    reused = await settlement_impl.build_via_service_contract(
        service_contract_id=service_contract_id,
        permit_id=permit_id,
        permit_nonce=permit_nonce,
        payer_wallet_id=payer_wallet_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_wallet_id=receiver_wallet_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        deadline=_deadline(),
    )
    assert reused is created

    with pytest.raises(RuntimeError, match="payload mismatch"):
        await settlement_impl.build_via_service_contract(
            service_contract_id=service_contract_id,
            permit_id=permit_id,
            permit_nonce=permit_nonce,
            payer_wallet_id=payer_wallet_id,
            payer_wallet_public_id=payer_wallet_public_id,
            receiver_wallet_id=receiver_wallet_id,
            receiver_wallet_public_id=receiver_wallet_public_id,
            coin_id=coin_id,
            deadline=_deadline() + timedelta(minutes=1),
        )


@pytest.mark.asyncio
async def test_service_contract_economy_settlement_rejects_mismatched_economy_refs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service_contract_id = uuid4()
    consumer_finance_entity_id = uuid4()
    smart_contract_id = uuid4()
    permit_id = uuid4()
    permit_nonce = 7
    payer_wallet_id = uuid4()
    payer_wallet_public_id = uuid4()
    receiver_wallet_id = uuid4()
    receiver_wallet_public_id = uuid4()
    coin_id = uuid4()
    session, _service_contract = _settlement_session(
        service_contract_id=service_contract_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        producer_finance_entity_id=uuid4(),
        smart_contract_id=smart_contract_id,
        permit_id=permit_id,
        permit_nonce=permit_nonce,
        payer_wallet_id=payer_wallet_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_wallet_id=receiver_wallet_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
    )
    monkeypatch.setattr(settlement_impl, "current_handler_session", lambda: session)

    with pytest.raises(RuntimeError, match="permit_nonce"):
        await settlement_impl.build_via_service_contract(
            service_contract_id=service_contract_id,
            permit_id=permit_id,
            permit_nonce=permit_nonce + 1,
            payer_wallet_id=payer_wallet_id,
            payer_wallet_public_id=payer_wallet_public_id,
            receiver_wallet_id=receiver_wallet_id,
            receiver_wallet_public_id=receiver_wallet_public_id,
            coin_id=coin_id,
            deadline=_deadline(),
        )

    with pytest.raises(RuntimeError, match="payer_wallet_public_id"):
        await settlement_impl.build_via_service_contract(
            service_contract_id=service_contract_id,
            permit_id=permit_id,
            permit_nonce=permit_nonce,
            payer_wallet_id=payer_wallet_id,
            payer_wallet_public_id=uuid4(),
            receiver_wallet_id=receiver_wallet_id,
            receiver_wallet_public_id=receiver_wallet_public_id,
            coin_id=coin_id,
            deadline=_deadline(),
        )


@pytest.mark.asyncio
async def test_service_contract_configure_economy_settlement_links_returned_coordinate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service_contract = _service_contract(
        service_contract_id=uuid4(),
        consumer_finance_entity_id=uuid4(),
        producer_finance_entity_id=uuid4(),
        smart_contract_id=uuid4(),
    )
    coordinate = ServiceContractEconomySettlement.model_construct(
        id=stable_service_contract_economy_settlement_id(
            service_contract_id=service_contract.id
        ),
        service_contract_id=service_contract.id,
        permit_id=uuid4(),
        permit_nonce=7,
        payer_wallet_id=uuid4(),
        payer_wallet_public_id=uuid4(),
        receiver_wallet_id=uuid4(),
        receiver_wallet_public_id=uuid4(),
        coin_id=uuid4(),
        deadline=_deadline(),
    )
    captured: dict[str, object] = {}

    async def _fake_build_via_service_contract(**kwargs: object) -> object:
        captured.update(kwargs)
        return coordinate

    monkeypatch.setattr(
        contract_impl.ServiceContractEconomySettlement,
        "build_via_service_contract",
        _fake_build_via_service_contract,
    )

    result = await contract_impl.configure_economy_settlement(
        service_contract=service_contract,
        permit_id=coordinate.permit_id,
        permit_nonce=coordinate.permit_nonce,
        payer_wallet_id=coordinate.payer_wallet_id,
        payer_wallet_public_id=coordinate.payer_wallet_public_id,
        receiver_wallet_id=coordinate.receiver_wallet_id,
        receiver_wallet_public_id=coordinate.receiver_wallet_public_id,
        coin_id=coordinate.coin_id,
        deadline=coordinate.deadline,
    )

    assert result is coordinate
    assert service_contract.economy_settlement is coordinate
    assert captured == {
        "service_contract_id": service_contract.id,
        "permit_id": coordinate.permit_id,
        "permit_nonce": coordinate.permit_nonce,
        "payer_wallet_id": coordinate.payer_wallet_id,
        "payer_wallet_public_id": coordinate.payer_wallet_public_id,
        "receiver_wallet_id": coordinate.receiver_wallet_id,
        "receiver_wallet_public_id": coordinate.receiver_wallet_public_id,
        "coin_id": coordinate.coin_id,
        "deadline": coordinate.deadline,
    }
