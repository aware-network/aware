from __future__ import annotations

# Standard
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin import Coin


class WalletBalance(BaseModel):
    # Relationships
    coin: Coin | None = Field(default=None)

    # Attributes
    balance: Annotated[Decimal, DecimalWire()] = Field(default=Decimal("0"))
    held_balance: Annotated[Decimal, DecimalWire()] = Field(default=Decimal("0"))
