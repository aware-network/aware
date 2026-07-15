from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Economy Ontology Orm Models
from aware_economy_ontology_orm_models.coin.coin_enums import CoinType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin_exchange_rate import CoinExchangeRate


class Coin(ORMModel):
    # Relationships
    coin_exchange_rates: list[CoinExchangeRate] = Field(default_factory=list, exclude=True)

    # Attributes
    decimals: int = Field(default=8)
    name: str
    symbol: str
    type: CoinType
