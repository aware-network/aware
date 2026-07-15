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
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology Dto
from aware_economy_ontology_dto.transaction.transaction_enums import (
    TransactionKind,
    TransactionStatus,
)

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin import Coin
    from aware_economy_ontology_dto.wallet.wallet_public import WalletPublic


class Transaction(BaseModel):
    # Relationships
    coin: Coin | None = Field(default=None)
    source_wallet_public: WalletPublic | None = Field(default=None)
    target_wallet_public: WalletPublic | None = Field(default=None)

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
