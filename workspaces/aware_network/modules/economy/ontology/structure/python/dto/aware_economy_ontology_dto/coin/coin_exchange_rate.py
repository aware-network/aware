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


class CoinExchangeRate(BaseModel):
    # Relationships
    quote_coin: Coin | None = Field(default=None)

    # Attributes
    data_source: str
    rate: Annotated[Decimal, DecimalWire()]
