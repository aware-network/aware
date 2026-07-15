from __future__ import annotations

# Standard
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology.coin.coin import Coin


class WalletBalance(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)

    # Attributes
    balance: Annotated[Decimal, DecimalWire()] = Field(default=Decimal("0"))
    held_balance: Annotated[Decimal, DecimalWire()] = Field(default=Decimal("0"))

    # Foreign Keys
    wallet_id: UUID = Field(description="Foreign key for Wallet.wallet_balances")
    coin_id: UUID = Field(description="Foreign key for WalletBalance.coin")

    async def set_balance(
        self, balance: Annotated[Decimal, DecimalWire()], held_balance: Annotated[Decimal, DecimalWire()] | None = None
    ) -> WalletBalance:
        """
        Sets absolute total and optional held balance on this WalletBalance.

        Receipt: WalletBalance(balance>=0, held_balance>=0, held_balance<=balance).
        """

        payload = {"balance": balance, "held_balance": held_balance}
        result = await invoke_instance(orm_model=self, function_name="set_balance", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, WalletBalance):
            return value
        return WalletBalance.validate_invocation_value(value)

    @classmethod
    async def create_via_wallet(
        cls,
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

        payload = {"wallet_id": wallet_id, "coin_id": coin_id, "balance": balance, "held_balance": held_balance}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_wallet", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, WalletBalance):
            return value
        return WalletBalance.validate_invocation_value(value)


class WalletBalanceSetBalanceInput(BaseModel):
    balance: Annotated[Decimal, DecimalWire()]
    held_balance: Annotated[Decimal, DecimalWire()] | None = Field(default=None)


class WalletBalanceSetBalanceOutput(BaseModel):
    value: WalletBalance


class WalletBalanceCreateViaWalletInput(BaseModel):
    wallet_id: UUID = Field(description="Foreign key for Wallet.wallet_balances")
    coin_id: UUID
    balance: Annotated[Decimal, DecimalWire()] = Field(default=Decimal("0"))
    held_balance: Annotated[Decimal, DecimalWire()] = Field(default=Decimal("0"))


class WalletBalanceCreateViaWalletOutput(BaseModel):
    value: WalletBalance


FUNCTIONS = {
    "WalletBalance": {
        "set_balance": {
            "canonical": {
                "name": "set_balance",
                "description": "Sets absolute total and optional held balance on this WalletBalance.\n\nReceipt: WalletBalance(balance>=0, held_balance>=0, held_balance<=balance).",
                "is_constructor": False,
            },
            "input": WalletBalanceSetBalanceInput,
            "output": WalletBalanceSetBalanceOutput,
        },
        "create_via_wallet": {
            "canonical": {
                "name": "create_via_wallet",
                "description": "Creates a deterministic wallet/coin balance record.\n\nReceipt: WalletBalance(id=stable(wallet_id, coin_id), balance>=0, held_balance>=0, held_balance<=balance).",
                "is_constructor": True,
            },
            "input": WalletBalanceCreateViaWalletInput,
            "output": WalletBalanceCreateViaWalletOutput,
        },
    },
}

__all__ = [
    "WalletBalance",
    "WalletBalanceSetBalanceInput",
    "WalletBalanceSetBalanceOutput",
    "WalletBalanceCreateViaWalletInput",
    "WalletBalanceCreateViaWalletOutput",
    "FUNCTIONS",
]
