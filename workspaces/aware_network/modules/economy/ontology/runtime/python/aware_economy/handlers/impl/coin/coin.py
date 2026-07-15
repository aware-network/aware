from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Economy Ontology
from aware_economy_ontology.coin.coin_enums import CoinType
from aware_economy_ontology.coin.coin import Coin

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Runtime
from aware_economy.stable_ids import stable_coin_id

# --- AWARE: USER_IMPORTS END


async def build(symbol: str, name: str, type: CoinType, decimals: int = 8) -> Coin:
    """
    Creates a Coin definition.

    Receipt: Coin(symbol, name, type, decimals).
    """

    # --- AWARE: LOGIC START build
    symbol_norm = symbol.strip().upper()
    coin_id = stable_coin_id(symbol=symbol_norm)
    return Coin(
        id=coin_id,
        symbol=symbol_norm,
        name=name.strip(),
        type=type,
        decimals=decimals,
    )
    # --- AWARE: LOGIC END build
