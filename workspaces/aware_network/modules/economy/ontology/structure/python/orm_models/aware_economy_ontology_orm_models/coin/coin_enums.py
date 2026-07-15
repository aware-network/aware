from __future__ import annotations

# Standard
from enum import Enum


class CoinType(Enum):
    crypto = "crypto"
    fiat = "fiat"
    token = "token"
