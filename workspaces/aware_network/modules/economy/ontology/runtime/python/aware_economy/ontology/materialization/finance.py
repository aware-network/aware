from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from aware_economy.capital_amount import (
    ZERO_AMOUNT,
    amount_equal,
    capital_amount,
    non_negative_amount,
)
from aware_economy.wallet_balance_context import (
    ensure_wallet_balance_link,
    resolve_unique_wallet_balance,
)
from aware_economy_ontology.wallet.wallet import Wallet
from aware_economy_ontology.wallet.wallet_balance import WalletBalance


async def materialize_wallet_coin_balance_absolute(
    *,
    wallet: Wallet,
    coin_id: UUID,
    balance: Decimal,
) -> WalletBalance:
    balance = non_negative_amount(balance, field_name="wallet balance")

    wallet_balance = resolve_unique_wallet_balance(wallet=wallet, coin_id=coin_id)
    if wallet_balance is None:
        wallet_balance = await WalletBalance.create_via_wallet(
            wallet_id=wallet.id,
            coin_id=coin_id,
            balance=balance,
            held_balance=ZERO_AMOUNT,
        )
    elif not amount_equal(wallet_balance.balance, balance):
        held_balance = _wallet_held_balance(wallet_balance)
        if held_balance > balance:
            raise ValueError(
                "wallet.set_coin_balance cannot set balance below held balance: "
                f"wallet_id={wallet.id} coin_id={coin_id} balance={balance} held_balance={held_balance}"
            )
        wallet_balance = await wallet_balance.set_balance(
            balance=balance,
            held_balance=held_balance,
        )

    ensure_wallet_balance_link(wallet=wallet, wallet_balance=wallet_balance)
    return wallet_balance


async def materialize_wallet_coin_balance_delta(
    *,
    wallet: Wallet,
    coin_id: UUID,
    delta: Decimal,
) -> WalletBalance:
    delta = capital_amount(delta, field_name="wallet delta")
    if delta == ZERO_AMOUNT:
        raise ValueError("wallet.apply_coin_delta requires delta != 0")

    wallet_balance = resolve_unique_wallet_balance(wallet=wallet, coin_id=coin_id)
    if wallet_balance is None:
        if delta < ZERO_AMOUNT:
            raise ValueError(
                "wallet.apply_coin_delta insufficient balance: missing wallet_balance for debit"
            )
        wallet_balance = await WalletBalance.create_via_wallet(
            wallet_id=wallet.id,
            coin_id=coin_id,
            balance=ZERO_AMOUNT,
            held_balance=ZERO_AMOUNT,
        )

    current_balance = non_negative_amount(
        wallet_balance.balance,
        field_name="wallet balance",
    )
    current_held = _wallet_held_balance(wallet_balance)
    new_balance = current_balance + delta
    if new_balance < ZERO_AMOUNT:
        raise ValueError(
            "wallet.apply_coin_delta insufficient balance: "
            f"wallet_id={wallet.id} coin_id={coin_id} balance={current_balance} delta={delta}"
        )
    if new_balance < current_held:
        raise ValueError(
            "wallet.apply_coin_delta cannot reduce total below held balance: "
            f"wallet_id={wallet.id} coin_id={coin_id} new_balance={new_balance} held_balance={current_held}"
        )

    wallet_balance = await wallet_balance.set_balance(
        balance=new_balance,
        held_balance=current_held,
    )
    ensure_wallet_balance_link(wallet=wallet, wallet_balance=wallet_balance)
    return wallet_balance


async def materialize_wallet_coin_balance_reconciliation(
    *,
    wallet: Wallet,
    coin_id: UUID,
    expected_balance: Decimal,
    new_balance: Decimal,
) -> WalletBalance:
    expected_balance = non_negative_amount(
        expected_balance,
        field_name="wallet expected_balance",
    )
    new_balance = non_negative_amount(new_balance, field_name="wallet new_balance")

    wallet_balance = resolve_unique_wallet_balance(wallet=wallet, coin_id=coin_id)
    if wallet_balance is None:
        current_balance = ZERO_AMOUNT
        if amount_equal(current_balance, new_balance):
            wallet_balance = await WalletBalance.create_via_wallet(
                wallet_id=wallet.id,
                coin_id=coin_id,
                balance=current_balance,
                held_balance=ZERO_AMOUNT,
            )
            ensure_wallet_balance_link(wallet=wallet, wallet_balance=wallet_balance)
            return wallet_balance
        if not amount_equal(current_balance, expected_balance):
            raise ValueError(
                "wallet.reconcile_coin_balance expected/current mismatch: "
                f"wallet_id={wallet.id} coin_id={coin_id} expected={expected_balance} current={current_balance}"
            )
        wallet_balance = await WalletBalance.create_via_wallet(
            wallet_id=wallet.id,
            coin_id=coin_id,
            balance=new_balance,
            held_balance=ZERO_AMOUNT,
        )
        ensure_wallet_balance_link(wallet=wallet, wallet_balance=wallet_balance)
        return wallet_balance

    current_balance = non_negative_amount(
        wallet_balance.balance,
        field_name="wallet balance",
    )
    current_held = _wallet_held_balance(wallet_balance)
    if new_balance < current_held:
        raise ValueError(
            "wallet.reconcile_coin_balance cannot set balance below held balance: "
            f"wallet_id={wallet.id} coin_id={coin_id} new_balance={new_balance} held_balance={current_held}"
        )
    if amount_equal(current_balance, new_balance):
        ensure_wallet_balance_link(wallet=wallet, wallet_balance=wallet_balance)
        return wallet_balance
    if not amount_equal(current_balance, expected_balance):
        raise ValueError(
            "wallet.reconcile_coin_balance expected/current mismatch: "
            f"wallet_id={wallet.id} coin_id={coin_id} expected={expected_balance} current={current_balance}"
        )

    wallet_balance = await wallet_balance.set_balance(
        balance=new_balance,
        held_balance=current_held,
    )
    ensure_wallet_balance_link(wallet=wallet, wallet_balance=wallet_balance)
    return wallet_balance


async def materialize_wallet_coin_hold(
    *,
    wallet: Wallet,
    coin_id: UUID,
    amount: Decimal,
) -> WalletBalance:
    amount = _positive_wallet_hold_amount(amount, field_name="wallet hold amount")

    wallet_balance = resolve_unique_wallet_balance(wallet=wallet, coin_id=coin_id)
    if wallet_balance is None:
        raise ValueError(
            "wallet.reserve_coin_hold insufficient available balance: "
            f"wallet_id={wallet.id} coin_id={coin_id} available=0 amount={amount}"
        )

    balance = non_negative_amount(
        wallet_balance.balance,
        field_name="wallet balance",
    )
    held_balance = _wallet_held_balance(wallet_balance)
    available_balance = _wallet_available_balance(
        balance=balance,
        held_balance=held_balance,
    )
    if amount > available_balance:
        raise ValueError(
            "wallet.reserve_coin_hold insufficient available balance: "
            f"wallet_id={wallet.id} coin_id={coin_id} available={available_balance} amount={amount}"
        )

    wallet_balance = await wallet_balance.set_balance(
        balance=balance,
        held_balance=held_balance + amount,
    )
    ensure_wallet_balance_link(wallet=wallet, wallet_balance=wallet_balance)
    return wallet_balance


async def materialize_wallet_coin_hold_release(
    *,
    wallet: Wallet,
    coin_id: UUID,
    amount: Decimal,
) -> WalletBalance:
    amount = _positive_wallet_hold_amount(amount, field_name="wallet hold amount")
    wallet_balance = _require_wallet_balance_for_hold(
        wallet=wallet,
        coin_id=coin_id,
        operation="wallet.release_coin_hold",
    )
    balance = non_negative_amount(
        wallet_balance.balance,
        field_name="wallet balance",
    )
    held_balance = _wallet_held_balance(wallet_balance)
    if amount > held_balance:
        raise ValueError(
            "wallet.release_coin_hold amount exceeds held balance: "
            f"wallet_id={wallet.id} coin_id={coin_id} held_balance={held_balance} amount={amount}"
        )

    wallet_balance = await wallet_balance.set_balance(
        balance=balance,
        held_balance=held_balance - amount,
    )
    ensure_wallet_balance_link(wallet=wallet, wallet_balance=wallet_balance)
    return wallet_balance


async def materialize_wallet_coin_hold_settlement(
    *,
    wallet: Wallet,
    coin_id: UUID,
    reserved_amount: Decimal,
    final_cost: Decimal,
) -> WalletBalance:
    reserved_amount = _positive_wallet_hold_amount(
        reserved_amount,
        field_name="wallet reserved_amount",
    )
    final_cost = non_negative_amount(
        final_cost,
        field_name="wallet final_cost",
    )
    if final_cost > reserved_amount:
        raise ValueError(
            "wallet.settle_coin_hold final_cost exceeds reserved_amount: "
            f"final_cost={final_cost} reserved_amount={reserved_amount}"
        )
    wallet_balance = _require_wallet_balance_for_hold(
        wallet=wallet,
        coin_id=coin_id,
        operation="wallet.settle_coin_hold",
    )
    balance = non_negative_amount(
        wallet_balance.balance,
        field_name="wallet balance",
    )
    held_balance = _wallet_held_balance(wallet_balance)
    if reserved_amount > held_balance:
        raise ValueError(
            "wallet.settle_coin_hold reserved_amount exceeds held balance: "
            f"wallet_id={wallet.id} coin_id={coin_id} held_balance={held_balance} reserved_amount={reserved_amount}"
        )
    if final_cost > balance:
        raise ValueError(
            "wallet.settle_coin_hold insufficient total balance: "
            f"wallet_id={wallet.id} coin_id={coin_id} balance={balance} final_cost={final_cost}"
        )

    wallet_balance = await wallet_balance.set_balance(
        balance=balance - final_cost,
        held_balance=held_balance - reserved_amount,
    )
    ensure_wallet_balance_link(wallet=wallet, wallet_balance=wallet_balance)
    return wallet_balance


def wallet_balance_amounts(
    wallet_balance: WalletBalance,
) -> tuple[Decimal, Decimal, Decimal]:
    balance = non_negative_amount(
        wallet_balance.balance,
        field_name="wallet balance",
    )
    held_balance = _wallet_held_balance(wallet_balance)
    available_balance = _wallet_available_balance(
        balance=balance,
        held_balance=held_balance,
    )
    return balance, held_balance, available_balance


def _require_wallet_balance_for_hold(
    *,
    wallet: Wallet,
    coin_id: UUID,
    operation: str,
) -> WalletBalance:
    wallet_balance = resolve_unique_wallet_balance(wallet=wallet, coin_id=coin_id)
    if wallet_balance is None:
        raise ValueError(
            f"{operation} requires existing wallet balance: wallet_id={wallet.id} coin_id={coin_id}"
        )
    return wallet_balance


def _wallet_held_balance(wallet_balance: WalletBalance) -> Decimal:
    held_balance = non_negative_amount(
        getattr(wallet_balance, "held_balance", ZERO_AMOUNT),
        field_name="wallet held_balance",
    )
    balance = non_negative_amount(
        wallet_balance.balance,
        field_name="wallet balance",
    )
    if held_balance > balance:
        raise ValueError(
            "wallet held balance cannot exceed total balance: "
            f"wallet_balance_id={wallet_balance.id} balance={balance} held_balance={held_balance}"
        )
    return held_balance


def _wallet_available_balance(*, balance: Decimal, held_balance: Decimal) -> Decimal:
    available_balance = balance - held_balance
    if available_balance < ZERO_AMOUNT:
        raise ValueError(
            "wallet available balance cannot be negative: "
            f"balance={balance} held_balance={held_balance}"
        )
    return available_balance


def _positive_wallet_hold_amount(value: Decimal, *, field_name: str) -> Decimal:
    amount = capital_amount(value, field_name=field_name)
    if amount <= ZERO_AMOUNT:
        raise ValueError(f"{field_name} must be > 0")
    return amount


__all__ = [
    "materialize_wallet_coin_balance_absolute",
    "materialize_wallet_coin_balance_delta",
    "materialize_wallet_coin_balance_reconciliation",
    "materialize_wallet_coin_hold",
    "materialize_wallet_coin_hold_release",
    "materialize_wallet_coin_hold_settlement",
    "wallet_balance_amounts",
]
