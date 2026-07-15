from __future__ import annotations

# Standard
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin import Coin


class WalletBalance(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)

    # Attributes
    balance: Annotated[Decimal, DecimalWire()] = Field(default=Decimal("0"))
    held_balance: Annotated[Decimal, DecimalWire()] = Field(default=Decimal("0"))

    # Foreign Keys
    wallet_id: UUID = Field(description="Foreign key for Wallet.wallet_balances")
    coin_id: UUID = Field(description="Foreign key for WalletBalance.coin")
