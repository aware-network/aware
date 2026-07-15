from __future__ import annotations

# Standard
from datetime import datetime
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
    from aware_economy_ontology_dto.transaction.transaction import Transaction


class WalletExternalIngressApplication(BaseModel):
    # Relationships
    coin: Coin | None = Field(default=None)
    transaction: Transaction | None = Field(default=None)

    # Attributes
    amount: Annotated[Decimal, DecimalWire()]
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    new_balance: Annotated[Decimal, DecimalWire()]
    previous_balance: Annotated[Decimal, DecimalWire()]
