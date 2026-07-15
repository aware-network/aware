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

# Economy Ontology Dto
from aware_economy_ontology_dto.transaction.provider_lifecycle_receipt_enums import (
    ProviderLifecycleEventKind,
    ProviderLifecycleStatus,
)

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology_dto.coin.coin import Coin
    from aware_economy_ontology_dto.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_dto.transaction.transaction import Transaction
    from aware_economy_ontology_dto.transaction.transaction_external import TransactionExternal
    from aware_economy_ontology_dto.wallet.wallet import Wallet
    from aware_economy_ontology_dto.wallet.wallet_public import WalletPublic


class ProviderLifecycleReceipt(BaseModel):
    # Relationships
    coin: Coin | None = Field(default=None)
    provider_finance_entity: FinanceEntity | None = Field(default=None)
    transaction: Transaction | None = Field(default=None)
    transaction_external: TransactionExternal | None = Field(default=None)
    wallet: Wallet | None = Field(default=None)
    wallet_finance_entity: FinanceEntity | None = Field(default=None)
    wallet_public: WalletPublic | None = Field(default=None)

    # Attributes
    amount: Annotated[Decimal, DecimalWire()]
    event_kind: ProviderLifecycleEventKind
    external_created_at: datetime
    idempotency_key: str
    metadata_json: JsonObject | None = Field(default=None)
    new_available_balance: Annotated[Decimal, DecimalWire()]
    new_balance: Annotated[Decimal, DecimalWire()]
    new_held_balance: Annotated[Decimal, DecimalWire()]
    previous_available_balance: Annotated[Decimal, DecimalWire()]
    previous_balance: Annotated[Decimal, DecimalWire()]
    previous_held_balance: Annotated[Decimal, DecimalWire()]
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    provider_event_id: str
    provider_lifecycle_effect_key: str
    provider_lifecycle_object_id: str
    provider_payment_reference: str
    provider_key: str
    provider_payload_hash: str
    status: ProviderLifecycleStatus
