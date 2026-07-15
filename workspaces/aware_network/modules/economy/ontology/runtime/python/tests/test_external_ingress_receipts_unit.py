from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from aware_economy.handlers.impl.transaction.transaction_external import record
import aware_economy.handlers.impl.wallet.wallet as wallet_handler_module
from aware_economy.handlers.impl.wallet.wallet import apply_external_ingress
from aware_economy_ontology.wallet.wallet import Wallet
from aware_economy_ontology.wallet.wallet_balance import WalletBalance
from aware_orm.session.current_session_ctx import set_session
from aware_orm.session.session import Session


def _external_evidence() -> dict[str, object]:
    return {
        "transaction_id": uuid4(),
        "transaction_intent_id": uuid4(),
        "provider_config_id": uuid4(),
        "capital_conversion_quote_id": uuid4(),
        "provider_finance_entity_id": uuid4(),
        "provider_key": "stripe",
        "provider_event_id": "evt_wallet_1",
        "idempotency_key": "evt_wallet_1",
        "quote_hash": "a" * 64,
        "external_amount_minor": 2500,
        "external_currency": "USD",
        "provider_public_reference": "pi_wallet_1",
        "provider_payload_hash": "sha256:" + "b" * 64,
        "external_created_at": datetime(2026, 7, 10, 8, 30, tzinfo=UTC),
    }


def _install_wallet_delta(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _materialize_wallet_coin_balance_delta(
        *,
        wallet: Wallet,
        coin_id: UUID,
        delta: Decimal,
    ) -> WalletBalance:
        balance = next(
            (
                candidate
                for candidate in wallet.wallet_balances
                if candidate.coin_id == coin_id
            ),
            None,
        )
        if balance is None:
            balance = WalletBalance(
                id=uuid4(),
                wallet_id=wallet.id,
                coin_id=coin_id,
                balance=Decimal("0"),
            )
            wallet.wallet_balances.append(balance)
        balance.balance += delta
        return balance

    monkeypatch.setattr(
        wallet_handler_module,
        "materialize_wallet_coin_balance_delta",
        _materialize_wallet_coin_balance_delta,
    )


@pytest.mark.asyncio
async def test_transaction_external_records_complete_correlated_evidence() -> None:
    evidence = _external_evidence()

    receipt = await record(**evidence)  # type: ignore[arg-type]

    assert receipt.transaction_id == evidence["transaction_id"]
    assert receipt.transaction_intent_id == evidence["transaction_intent_id"]
    assert receipt.provider_config_id == evidence["provider_config_id"]
    assert (
        receipt.capital_conversion_quote_id == evidence["capital_conversion_quote_id"]
    )
    assert receipt.provider_key == "stripe"
    assert receipt.external_amount_minor == 2500
    assert receipt.external_currency == "USD"
    assert receipt.provider_public_reference == "pi_wallet_1"


@pytest.mark.asyncio
async def test_transaction_external_replay_requires_exact_evidence() -> None:
    evidence = _external_evidence()
    receipt = await record(**evidence)  # type: ignore[arg-type]
    session = Session(branch_id=uuid4(), skip_db=True)
    session.imap_add(receipt)

    with set_session(session):
        replay = await record(**evidence)  # type: ignore[arg-type]
        assert replay is receipt

        with pytest.raises(ValueError, match="cannot redefine"):
            await record(  # type: ignore[arg-type]
                **{
                    **evidence,
                    "external_amount_minor": 2501,
                }
            )


@pytest.mark.asyncio
async def test_transaction_external_provider_event_cannot_credit_another_transaction() -> (
    None
):
    evidence = _external_evidence()
    receipt = await record(**evidence)  # type: ignore[arg-type]
    session = Session(branch_id=uuid4(), skip_db=True)
    session.imap_add(receipt)

    with set_session(session):
        with pytest.raises(ValueError, match="cannot redefine"):
            await record(  # type: ignore[arg-type]
                **{
                    **evidence,
                    "transaction_id": uuid4(),
                    "transaction_intent_id": uuid4(),
                    "capital_conversion_quote_id": uuid4(),
                }
            )


@pytest.mark.asyncio
async def test_transaction_external_rejects_unverified_payload_hash_shape() -> None:
    with pytest.raises(ValueError, match="sha256: prefix"):
        await record(  # type: ignore[arg-type]
            **{
                **_external_evidence(),
                "provider_payload_hash": "not-a-provider-payload-hash",
            }
        )


@pytest.mark.asyncio
async def test_wallet_applies_external_ingress_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_wallet_delta(monkeypatch)
    wallet = Wallet(
        id=uuid4(),
        wallet_public_id=uuid4(),
        public_key="wallet-public-key",
        private_key_encrypted="custody://wallet",
    )
    transaction_id = uuid4()
    coin_id = uuid4()

    application = await apply_external_ingress(
        wallet,
        transaction_id=transaction_id,
        coin_id=coin_id,
        amount=Decimal("25.00"),
    )
    replay = await apply_external_ingress(
        wallet,
        transaction_id=transaction_id,
        coin_id=coin_id,
        amount=Decimal("25"),
    )

    assert replay is application
    assert application.transaction_id == transaction_id
    assert application.amount == Decimal("25")
    assert application.previous_balance == Decimal("0")
    assert application.new_balance == Decimal("25")
    assert len(wallet.external_ingress_applications) == 1
    assert len(wallet.wallet_balances) == 1
    assert wallet.wallet_balances[0].balance == Decimal("25")


@pytest.mark.asyncio
async def test_wallet_rejects_mismatched_external_ingress_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_wallet_delta(monkeypatch)
    wallet = Wallet(
        id=uuid4(),
        wallet_public_id=uuid4(),
        public_key="wallet-public-key",
        private_key_encrypted="custody://wallet",
    )
    transaction_id = uuid4()
    coin_id = uuid4()
    await apply_external_ingress(
        wallet,
        transaction_id=transaction_id,
        coin_id=coin_id,
        amount=Decimal("25"),
    )

    with pytest.raises(ValueError, match="existing application mismatch"):
        await apply_external_ingress(
            wallet,
            transaction_id=transaction_id,
            coin_id=coin_id,
            amount=Decimal("26"),
        )
