from __future__ import annotations

# Standard
from datetime import datetime
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
    from aware_economy_ontology.transaction.transaction import Transaction


class WalletExternalIngressApplication(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)
    transaction: Transaction | None = Field(default=None, exclude=True)

    # Attributes
    amount: Annotated[Decimal, DecimalWire()]
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    new_balance: Annotated[Decimal, DecimalWire()]
    previous_balance: Annotated[Decimal, DecimalWire()]

    # Foreign Keys
    wallet_id: UUID = Field(description="Foreign key for Wallet.external_ingress_applications")
    coin_id: UUID = Field(description="Foreign key for WalletExternalIngressApplication.coin")
    transaction_id: UUID = Field(description="Foreign key for WalletExternalIngressApplication.transaction")


FUNCTIONS = {
    "WalletExternalIngressApplication": {},
}

__all__ = [
    "WalletExternalIngressApplication",
    "FUNCTIONS",
]
