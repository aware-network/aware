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
    from aware_economy_ontology.coin.coin import Coin


class CoinExchangeRate(ORMModel):
    # Relationships
    quote_coin: Coin | None = Field(default=None, exclude=True)

    # Attributes
    data_source: str
    rate: Annotated[Decimal, DecimalWire()]

    # Foreign Keys
    coin_id: UUID = Field(description="Foreign key for Coin.coin_exchange_rates")
    quote_coin_id: UUID = Field(description="Foreign key for CoinExchangeRate.quote_coin")


FUNCTIONS = {
    "CoinExchangeRate": {},
}

__all__ = [
    "CoinExchangeRate",
    "FUNCTIONS",
]
