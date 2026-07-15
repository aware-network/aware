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
from aware_economy_ontology_orm_models.transaction.transaction_intent_enums import TransactionIntentStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.coin.coin import Coin
    from aware_economy_ontology_orm_models.external_capital.external_capital_provider_config import (
        ExternalCapitalProviderConfig,
    )
    from aware_economy_ontology_orm_models.finance.finance_entity import FinanceEntity
    from aware_economy_ontology_orm_models.transaction.capital_conversion_quote import CapitalConversionQuote
    from aware_economy_ontology_orm_models.transaction.transaction_intent_external_expiration import (
        TransactionIntentExternalExpiration,
    )
    from aware_economy_ontology_orm_models.wallet.wallet import Wallet
    from aware_economy_ontology_orm_models.wallet.wallet_public import WalletPublic


class TransactionIntent(ORMModel):
    # Relationships
    capital_conversion_quote: CapitalConversionQuote | None = Field(default=None, exclude=True)
    coin: Coin | None = Field(default=None, exclude=True)
    external_expirations: list[TransactionIntentExternalExpiration] = Field(default_factory=list, exclude=True)
    provider_config: ExternalCapitalProviderConfig | None = Field(default=None, exclude=True)
    recipient_finance_entity: FinanceEntity | None = Field(default=None, exclude=True)
    recipient_wallet: Wallet | None = Field(default=None, exclude=True)
    recipient_wallet_public: WalletPublic | None = Field(default=None, exclude=True)

    # Attributes
    amount: Annotated[Decimal, DecimalWire()]
    created_at: datetime
    funding_intent_key: str
    idempotency_key: str
    metadata_json: JsonObject | None = Field(default=None)
    provider_key: str
    status: TransactionIntentStatus = Field(default=TransactionIntentStatus.created)
    updated_at: datetime | None = Field(default=None)

    # Foreign Keys
    capital_conversion_quote_id: UUID | None = Field(
        default=None, description="Foreign key for TransactionIntent.capital_conversion_quote"
    )
    coin_id: UUID = Field(description="Foreign key for TransactionIntent.coin")
    provider_config_id: UUID = Field(description="Foreign key for TransactionIntent.provider_config")
    recipient_finance_entity_id: UUID = Field(description="Foreign key for TransactionIntent.recipient_finance_entity")
    recipient_wallet_id: UUID = Field(description="Foreign key for TransactionIntent.recipient_wallet")
    recipient_wallet_public_id: UUID = Field(description="Foreign key for TransactionIntent.recipient_wallet_public")
