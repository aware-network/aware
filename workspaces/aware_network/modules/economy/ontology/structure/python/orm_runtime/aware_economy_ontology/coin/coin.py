from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology
from aware_economy_ontology.coin.coin_enums import CoinType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_economy_ontology.coin.coin_exchange_rate import CoinExchangeRate


class Coin(ORMModel):
    # Relationships
    coin_exchange_rates: list[CoinExchangeRate] = Field(default_factory=list, exclude=True)

    # Attributes
    decimals: int = Field(default=8)
    name: str
    symbol: str
    type: CoinType

    @classmethod
    async def build(cls, symbol: str, name: str, type: CoinType, decimals: int = 8) -> Coin:
        """
        Creates a Coin definition.

        Receipt: Coin(symbol, name, type, decimals).
        """

        payload = {"symbol": symbol, "name": name, "type": type, "decimals": decimals}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Coin):
            return value
        return Coin.validate_invocation_value(value)


class CoinBuildInput(BaseModel):
    symbol: str
    name: str
    type: CoinType
    decimals: int = Field(default=8)


class CoinBuildOutput(BaseModel):
    value: Coin


FUNCTIONS = {
    "Coin": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Creates a Coin definition.\n\nReceipt: Coin(symbol, name, type, decimals).",
                "is_constructor": True,
            },
            "input": CoinBuildInput,
            "output": CoinBuildOutput,
        },
    },
}

__all__ = [
    "Coin",
    "CoinBuildInput",
    "CoinBuildOutput",
    "FUNCTIONS",
]
