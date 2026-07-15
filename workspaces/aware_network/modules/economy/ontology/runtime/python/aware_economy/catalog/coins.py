from __future__ import annotations

from dataclasses import dataclass

from aware_economy_ontology.coin.coin_enums import CoinType


@dataclass(frozen=True, slots=True)
class CoinDeclaration:
    symbol: str
    name: str
    type: CoinType
    decimals: int = 8


DEFAULT_COIN_DECLARATIONS: tuple[CoinDeclaration, ...] = (
    CoinDeclaration(
        symbol="AWC",
        name="Aware Coin",
        type=CoinType.crypto,
        decimals=8,
    ),
    CoinDeclaration(
        symbol="BTC",
        name="Bitcoin",
        type=CoinType.crypto,
        decimals=8,
    ),
    CoinDeclaration(
        symbol="ETH",
        name="Ethereum",
        type=CoinType.crypto,
        decimals=18,
    ),
    CoinDeclaration(
        symbol="USD",
        name="US Dollar",
        type=CoinType.fiat,
        decimals=2,
    ),
    CoinDeclaration(
        symbol="EUR",
        name="Euro",
        type=CoinType.fiat,
        decimals=2,
    ),
    CoinDeclaration(
        symbol="GBP",
        name="British Pound",
        type=CoinType.fiat,
        decimals=2,
    ),
    CoinDeclaration(
        symbol="JPY",
        name="Japanese Yen",
        type=CoinType.fiat,
        decimals=0,
    ),
    CoinDeclaration(
        symbol="AUD",
        name="Australian Dollar",
        type=CoinType.fiat,
        decimals=2,
    ),
    CoinDeclaration(
        symbol="CAD",
        name="Canadian Dollar",
        type=CoinType.fiat,
        decimals=2,
    ),
    CoinDeclaration(
        symbol="CHF",
        name="Swiss Franc",
        type=CoinType.fiat,
        decimals=2,
    ),
    CoinDeclaration(
        symbol="TWD",
        name="New Taiwan Dollar",
        type=CoinType.fiat,
        decimals=2,
    ),
    CoinDeclaration(
        symbol="CNY",
        name="Chinese Yuan",
        type=CoinType.fiat,
        decimals=2,
    ),
)


__all__ = [
    "CoinDeclaration",
    "DEFAULT_COIN_DECLARATIONS",
]
