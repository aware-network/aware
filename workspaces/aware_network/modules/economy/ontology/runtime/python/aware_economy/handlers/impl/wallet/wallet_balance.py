from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.wallet.wallet_balance import WalletBalance

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Runtime
from aware_economy.capital_amount import (
    ZERO_AMOUNT,
    non_negative_amount,
)

# Economy Ontology
from aware_economy_ontology.stable_ids import stable_wallet_balance_id

# --- AWARE: USER_IMPORTS END


async def set_balance(
    wallet_balance: WalletBalance,
    balance: Annotated[Decimal, DecimalWire()],
    held_balance: Annotated[Decimal, DecimalWire()] | None = None,
) -> WalletBalance:
    """
    Sets absolute total and optional held balance on this WalletBalance.

    Receipt: WalletBalance(balance>=0, held_balance>=0, held_balance<=balance).
    """

    # --- AWARE: LOGIC START set_balance
    balance = non_negative_amount(balance, field_name="wallet balance")
    held_balance_amount = non_negative_amount(
        (held_balance if held_balance is not None else getattr(wallet_balance, "held_balance", ZERO_AMOUNT)),
        field_name="wallet held_balance",
    )
    if held_balance_amount > balance:
        raise ValueError(
            "wallet_balance.set_balance held_balance cannot exceed balance: "
            f"balance={balance} held_balance={held_balance_amount}"
        )
    wallet_balance.balance = balance
    wallet_balance.held_balance = held_balance_amount
    return wallet_balance
    # --- AWARE: LOGIC END set_balance


async def create_via_wallet(
    wallet_id: UUID,
    coin_id: UUID,
    balance: Annotated[Decimal, DecimalWire()] = Decimal("0"),
    held_balance: Annotated[Decimal, DecimalWire()] = Decimal("0"),
) -> WalletBalance:
    """
    Creates a deterministic wallet/coin balance record.

    Receipt: WalletBalance(id=stable(wallet_id, coin_id), balance>=0, held_balance>=0,
    held_balance<=balance).
    """

    # --- AWARE: LOGIC START create_via_wallet
    balance = non_negative_amount(balance, field_name="wallet balance")
    held_balance_amount = non_negative_amount(
        held_balance,
        field_name="wallet held_balance",
    )
    if held_balance_amount > balance:
        raise ValueError(
            "wallet_balance.create held_balance cannot exceed balance: "
            f"balance={balance} held_balance={held_balance_amount}"
        )

    wallet_balance_id = stable_wallet_balance_id(wallet_id=wallet_id, coin_id=coin_id)
    return WalletBalance(
        id=wallet_balance_id,
        wallet_id=wallet_id,
        coin_id=coin_id,
        balance=balance,
        held_balance=held_balance_amount,
    )
    # --- AWARE: LOGIC END create_via_wallet
