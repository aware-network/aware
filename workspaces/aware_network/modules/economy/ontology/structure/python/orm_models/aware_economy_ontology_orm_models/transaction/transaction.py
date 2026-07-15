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

# Economy Ontology Orm Models
from aware_economy_ontology_orm_models.transaction.transaction_enums import (
    TransactionKind,
    TransactionStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin import Coin
    from aware_economy_ontology_orm_models.wallet.wallet_public import WalletPublic


class Transaction(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)
    source_wallet_public: WalletPublic | None = Field(default=None, exclude=True)
    target_wallet_public: WalletPublic | None = Field(default=None, exclude=True)

    # Attributes
    capital_origin_id: UUID
    coin_amount: Annotated[Decimal, DecimalWire()]
    confirmed_at: datetime | None = Field(default=None)
    description: str | None = Field(default=None)
    gas_price: Annotated[Decimal, DecimalWire()]
    idempotency_key: str | None = Field(default=None)
    kind: TransactionKind = Field(default=TransactionKind.transfer)
    nonce: int
    receiver_signature: str | None = Field(default=None)
    sender_signature: str | None = Field(default=None)
    source_previous_coin_balance: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    status: TransactionStatus = Field(default=TransactionStatus.created)
    target_previous_coin_balance: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    transaction_hash: str

    # Foreign Keys
    coin_id: UUID = Field(description="Foreign key for Transaction.coin")
    source_wallet_public_id: UUID | None = Field(
        default=None, description="Foreign key for Transaction.source_wallet_public"
    )
    target_wallet_public_id: UUID = Field(description="Foreign key for Transaction.target_wallet_public")
