from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.coin.coin_enums import CoinType

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin_exchange_rate import CoinExchangeRate


class Coin(BaseModel):
    # Relationships
    coin_exchange_rates: list[CoinExchangeRate] = Field(default_factory=list)

    # Attributes
    decimals: int = Field(default=8)
    name: str
    symbol: str
    type: CoinType
