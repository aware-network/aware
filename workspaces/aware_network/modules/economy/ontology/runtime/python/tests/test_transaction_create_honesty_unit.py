from __future__ import annotations

# Standard
from decimal import Decimal
from uuid import uuid4

# Third-party
import pytest

# Economy Runtime
from aware_economy.handlers.impl.transaction.transaction import (
    create,
    create_external_ingress,
)

# Economy Ontology
from aware_economy_ontology.stable_ids import stable_transaction_id
from aware_economy_ontology.transaction.transaction_enums import TransactionKind
from aware_economy_ontology.wallet.wallet import Wallet
from aware_economy_ontology.wallet.wallet_balance import WalletBalance

# Orm
from aware_orm.session.current_session_ctx import set_session
from aware_orm.session.session import Session


@pytest.mark.asyncio
async def test_transaction_create_keeps_previous_balances_unknown_without_lane_context() -> None:
    source_wallet_public_id = uuid4()
    tx = await create(
        source_wallet_public_id=source_wallet_public_id,
        capital_origin_id=source_wallet_public_id,
        target_wallet_public_id=uuid4(),
        coin_id=uuid4(),
        coin_amount=Decimal("5.0"),
        nonce=1,
        description="unit-test",
    )

    assert tx.source_previous_coin_balance is None
    assert tx.target_previous_coin_balance is None


@pytest.mark.asyncio
async def test_transaction_create_reads_known_previous_balances_from_active_lane() -> None:
    source_wallet_public_id = uuid4()
    target_wallet_public_id = uuid4()
    coin_id = uuid4()
    source_wallet = Wallet(
        id=uuid4(),
        wallet_public_id=source_wallet_public_id,
        public_key="source-public-key",
        private_key_encrypted="source-private-key-encrypted",
    )
    target_wallet = Wallet(
        id=uuid4(),
        wallet_public_id=target_wallet_public_id,
        public_key="target-public-key",
        private_key_encrypted="target-private-key-encrypted",
    )
    source_balance = WalletBalance(
        id=uuid4(),
        wallet_id=source_wallet.id,
        coin_id=coin_id,
        balance="12.5",
    )
    target_balance = WalletBalance(
        id=uuid4(),
        wallet_id=target_wallet.id,
        coin_id=coin_id,
        balance="3.25",
    )
    source_wallet.wallet_balances.append(source_balance)
    target_wallet.wallet_balances.append(target_balance)

    session = Session(branch_id=uuid4(), skip_db=True)
    session.imap_add(source_wallet)
    session.imap_add(target_wallet)
    session.imap_add(source_balance)
    session.imap_add(target_balance)

    with set_session(session):
        tx = await create(
            source_wallet_public_id=source_wallet_public_id,
            capital_origin_id=source_wallet_public_id,
            target_wallet_public_id=target_wallet_public_id,
            coin_id=coin_id,
            coin_amount=Decimal("5.0"),
            nonce=1,
            description="unit-test",
        )

    assert tx.source_previous_coin_balance == Decimal("12.5")
    assert tx.target_previous_coin_balance == Decimal("3.25")


@pytest.mark.asyncio
async def test_transaction_create_rejects_insufficient_known_source_balance() -> None:
    source_wallet_public_id = uuid4()
    coin_id = uuid4()
    source_wallet = Wallet(
        id=uuid4(),
        wallet_public_id=source_wallet_public_id,
        public_key="source-public-key",
        private_key_encrypted="source-private-key-encrypted",
    )
    source_balance = WalletBalance(
        id=uuid4(),
        wallet_id=source_wallet.id,
        coin_id=coin_id,
        balance="1",
    )

    session = Session(branch_id=uuid4(), skip_db=True)
    session.imap_add(source_wallet)
    session.imap_add(source_balance)

    with set_session(session):
        with pytest.raises(
            ValueError,
            match="insufficient known source wallet balance",
        ):
            await create(
                source_wallet_public_id=source_wallet_public_id,
                capital_origin_id=source_wallet_public_id,
                target_wallet_public_id=uuid4(),
                coin_id=coin_id,
                coin_amount=Decimal("2.0"),
                nonce=1,
                description="unit-test",
            )


@pytest.mark.asyncio
async def test_transaction_create_rejects_ambiguous_source_balance_context() -> None:
    source_wallet_public_id = uuid4()
    coin_id = uuid4()
    source_wallet = Wallet(
        id=uuid4(),
        wallet_public_id=source_wallet_public_id,
        public_key="source-public-key",
        private_key_encrypted="source-private-key-encrypted",
    )
    source_balance_a = WalletBalance(
        id=uuid4(),
        wallet_id=source_wallet.id,
        coin_id=coin_id,
        balance="10",
    )
    source_balance_b = WalletBalance(
        id=uuid4(),
        wallet_id=source_wallet.id,
        coin_id=coin_id,
        balance="11",
    )

    session = Session(branch_id=uuid4(), skip_db=True)
    session.imap_add(source_wallet)
    session.imap_add(source_balance_a)
    session.imap_add(source_balance_b)

    with set_session(session):
        with pytest.raises(
            ValueError,
            match="exactly one source wallet coin balance",
        ):
            await create(
                source_wallet_public_id=source_wallet_public_id,
                capital_origin_id=source_wallet_public_id,
                target_wallet_public_id=uuid4(),
                coin_id=coin_id,
                coin_amount=Decimal("2.0"),
                nonce=1,
                description="unit-test",
            )


@pytest.mark.asyncio
async def test_transaction_create_rejects_non_wallet_transfer_origin() -> None:
    with pytest.raises(ValueError, match="capital_origin_id"):
        await create(
            source_wallet_public_id=uuid4(),
            capital_origin_id=uuid4(),
            target_wallet_public_id=uuid4(),
            coin_id=uuid4(),
            coin_amount="2",
            nonce=1,
        )


@pytest.mark.asyncio
async def test_external_ingress_has_quote_origin_and_no_source_wallet() -> None:
    capital_conversion_quote_id = uuid4()
    target_wallet_public_id = uuid4()
    coin_id = uuid4()

    transaction = await create_external_ingress(
        capital_origin_id=capital_conversion_quote_id,
        target_wallet_public_id=target_wallet_public_id,
        coin_id=coin_id,
        coin_amount="25.00",
        nonce=7,
        description="verified external capital",
        idempotency_key="evt_1",
    )

    assert transaction.id == stable_transaction_id(
        capital_origin_id=capital_conversion_quote_id,
        target_wallet_public_id=target_wallet_public_id,
        coin_id=coin_id,
        nonce=7,
    )
    assert transaction.source_wallet_public_id is None
    assert transaction.capital_origin_id == capital_conversion_quote_id
    assert transaction.kind == TransactionKind.external_ingress
    assert transaction.coin_amount == Decimal("25")
    assert transaction.gas_price == Decimal("0")
    assert transaction.sender_signature is None
    assert transaction.source_previous_coin_balance is None
