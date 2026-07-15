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
from aware_economy_ontology_orm_models.transaction.provider_lifecycle_receipt_enums import (
    ProviderLifecycleEventKind,
    ProviderLifecycleStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin import Coin
    from aware_economy_ontology_orm_models.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_orm_models.transaction.transaction import Transaction
    from aware_economy_ontology_orm_models.transaction.transaction_external import TransactionExternal
    from aware_economy_ontology_orm_models.wallet.wallet import Wallet
    from aware_economy_ontology_orm_models.wallet.wallet_public import WalletPublic


class ProviderLifecycleReceipt(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)
    provider_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    transaction: Transaction | None = Field(default=None, exclude=True)
    transaction_external: TransactionExternal | None = Field(default=None, exclude=True)
    wallet: Wallet | None = Field(default=None, exclude=True)
    wallet_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    wallet_public: WalletPublic | None = Field(default=None, exclude=True)

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

    # Foreign Keys
    coin_id: UUID = Field(description="Foreign key for ProviderLifecycleReceipt.coin")
    provider_finance_entity_id: UUID = Field(
        description="Foreign key for ProviderLifecycleReceipt.provider_finance_entity"
    )
    transaction_id: UUID = Field(description="Foreign key for ProviderLifecycleReceipt.transaction")
    transaction_external_id: UUID = Field(description="Foreign key for ProviderLifecycleReceipt.transaction_external")
    wallet_id: UUID = Field(description="Foreign key for ProviderLifecycleReceipt.wallet")
    wallet_finance_entity_id: UUID = Field(description="Foreign key for ProviderLifecycleReceipt.wallet_finance_entity")
    wallet_public_id: UUID = Field(description="Foreign key for ProviderLifecycleReceipt.wallet_public")
