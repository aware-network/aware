from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from aware_economy.handlers.impl.wallet import wallet as wallet_handlers
from aware_economy.ontology.materialization.finance import (
    materialize_wallet_coin_balance_delta,
    materialize_wallet_coin_balance_reconciliation,
)
from aware_economy_ontology.wallet.wallet import Wallet
from aware_economy_ontology.wallet.wallet_balance import WalletBalance


@pytest.mark.asyncio
async def test_wallet_set_coin_balance_delegates_to_finance_materialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wallet = Wallet(
        id=uuid4(),
        wallet_public_id=uuid4(),
        public_key="pk",
        private_key_encrypted="sk",
    )
    coin_id = uuid4()
    expected = WalletBalance(
        id=uuid4(),
        wallet_id=wallet.id,
        coin_id=coin_id,
        balance=Decimal("7.5"),
    )
    calls: list[tuple[Wallet, object, object]] = []

    async def _fake_materialize(*, wallet: Wallet, coin_id, balance):  # type: ignore[no-untyped-def]
        calls.append((wallet, coin_id, balance))
        return expected

    monkeypatch.setattr(
        wallet_handlers,
        "materialize_wallet_coin_balance_absolute",
        _fake_materialize,
    )

    result = await wallet_handlers.set_coin_balance(
        wallet=wallet,
        coin_id=coin_id,
        balance=Decimal("7.5"),
    )

    assert result is expected
    assert calls == [(wallet, coin_id, Decimal("7.5"))]


@pytest.mark.asyncio
async def test_finance_materialization_apply_delta_updates_existing_balance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wallet = Wallet(
        id=uuid4(),
        wallet_public_id=uuid4(),
        public_key="pk",
        private_key_encrypted="sk",
    )
    coin_id = uuid4()
    wallet_balance = WalletBalance(
        id=uuid4(),
        wallet_id=wallet.id,
        coin_id=coin_id,
        balance=Decimal("10"),
    )
    wallet.wallet_balances.append(wallet_balance)

    async def _fake_set_balance(
        self: WalletBalance,
        balance: Decimal,
        held_balance: Decimal | None = None,
    ) -> WalletBalance:
        self.balance = balance
        if held_balance is not None:
            self.held_balance = held_balance
        return self

    monkeypatch.setattr(WalletBalance, "set_balance", _fake_set_balance)

    result = await materialize_wallet_coin_balance_delta(
        wallet=wallet,
        coin_id=coin_id,
        delta=Decimal("-3.0"),
    )

    assert result is wallet_balance
    assert wallet_balance.balance == Decimal("7")
    assert len(wallet.wallet_balances) == 1


@pytest.mark.asyncio
async def test_finance_materialization_reconciliation_is_idempotent_when_target_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wallet = Wallet(
        id=uuid4(),
        wallet_public_id=uuid4(),
        public_key="pk",
        private_key_encrypted="sk",
    )
    coin_id = uuid4()
    wallet_balance = WalletBalance(
        id=uuid4(),
        wallet_id=wallet.id,
        coin_id=coin_id,
        balance=Decimal("4"),
    )
    wallet.wallet_balances.append(wallet_balance)
    set_calls = {"count": 0}

    async def _fake_set_balance(self: WalletBalance, balance: Decimal) -> WalletBalance:
        set_calls["count"] += 1
        self.balance = balance
        return self

    monkeypatch.setattr(WalletBalance, "set_balance", _fake_set_balance)

    result = await materialize_wallet_coin_balance_reconciliation(
        wallet=wallet,
        coin_id=coin_id,
        expected_balance=Decimal("1.0"),
        new_balance=Decimal("4.0"),
    )

    assert result is wallet_balance
    assert wallet_balance.balance == Decimal("4")
    assert set_calls["count"] == 0
